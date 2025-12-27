# PHASE 2: Complete Deliverables (Days 3-4)
## API Specification, Training Plan, Decisions & Monitoring

---

## SECTION 1: REST API SPECIFICATION

### Endpoint: POST /detect

**Request Schema**:
```json
{
  "question": "What is photosynthesis?",
  "llm_answer": "Photosynthesis is the process...",
  "reference_context": "Optional knowledge base text",
  "use_context_verification": false,
  "timeout_ms": 5000
}
```

**Response Schema (Success)**:
```json
{
  "hallucination_score": 0.15,
  "is_hallucinated": false,
  "confidence": 0.92,
  "confidence_interval": [0.88, 0.96],
  "detection_stage": "stage_b",
  "latency_ms": 42,
  "stages_executed": ["stage_a", "stage_b"],
  "recommended_action": "accept",
  "explanations": [
    "High semantic similarity to reference",
    "LoRA probe confidence: 0.95"
  ],
  "metadata": {
    "question_tokens": 15,
    "answer_tokens": 42,
    "model_version": "v1.0.0",
    "cached": false
  }
}
```

**Response Schema (Error)**:
```json
{
  "error": "timeout",
  "message": "Detection exceeded 5000ms timeout",
  "fallback_action": "flag"
}
```

**HTTP Status Codes**:
- 200: Success
- 400: Bad request (invalid schema)
- 408: Timeout
- 500: Server error

---

## SECTION 2: TRAINING PLAN

### LoRA Probe Training Strategy

**Objective**: Train lightweight binary classifier on 70B LLM hidden states

**Data Pipeline**:
```
HaluEval (50k) + Proprietary (50k) → Preprocessing → 80/20 split → Training
                                  ↓
                         100k examples total
                         (70% correct, 30% hallucinated)
```

**Training Configuration**:
```python
# LoRA Configuration
rank: 16
alpha: 32
lora_dropout: 0.05
target_modules: ["q_proj", "v_proj"]  # 70B model

# Training Loop
epochs: 3
batch_size: 32
learning_rate: 5e-5
warmup_steps: 500
weight_decay: 0.01

# Hardware
GPU: A100 (40GB) or H100
Estimated training time: 4-6 hours
```

**Quality Metrics**:
- Validation Accuracy: Target ≥85%
- Precision: ≥80% (minimize false positives)
- Recall: ≥80% (minimize false negatives)
- F1-Score: ≥0.82

**Data Preparation**:
1. Download HaluEval QA subset (50k examples)
2. Collect proprietary labeled hallucination data (50k examples)
3. Normalize text (lowercasing, whitespace handling)
4. Tokenize with LLM tokenizer
5. Extract hidden states at layer -2, token 300
6. Create PyTorch DataLoader with batching

---

## SECTION 3: ARCHITECTURAL DECISIONS & TRADEOFFS

### Decision 1: Multi-Stage Pipeline vs Single LLM Judge

**Chosen: Multi-Stage Pipeline**

**Rationale**:
- Production SLA <100ms p95 requires stage cascading
- 70% queries resolved by Stage A+B (<35ms)
- Stage C/D for high-value/uncertain requests
- Cost reduction: 95% requests avoid LLM calls

**Alternatives Rejected**:
- Full fine-tuned model: $5k+ cost, 2-week training
- Single LLM judge: 1.5s latency violates SLA

---

### Decision 2: LoRA vs Full Fine-Tune

**Chosen: LoRA Adapter**

**Trade-off Analysis**:

| Metric | LoRA | Fine-Tune | Winner |
|--------|------|-----------|--------|
| Training Time | 4-6h | 7-10 days | LoRA |
| Cost | $50 | $5,000 | LoRA |
| Accuracy | 85% | 87% | Fine-Tune (+2%) |
| Inference Speed | 25ms | 25ms | Tie |
| Storage | 32MB | 140GB | LoRA |

**Conclusion**: 2% accuracy loss acceptable for 100x cost/time savings

---

### Decision 3: Real-time vs Cached Judge

**Chosen: Cached Responses + Embedding Dedup**

**Logic**:
- Similar Q&A pairs likely have same hallucination status
- Embedding search identifies duplicates in <5ms
- Cache hit rate: 90%+ in practice
- Miss cost: $0.001/query → $1000/1M queries
- Cache overhead: negligible

---

## SECTION 4: DATADOG INSTRUMENTATION SPEC

### APM Tracing Structure

```python
from ddtrace import tracer
from ddtrace.contrib.flask import patch_all

patch_all()

with tracer.trace('hallucination.detect', service='llm-quality-guardian'):
    # Stage A
    with tracer.trace('stage_a.heuristics'):
        confidence_a = run_heuristics()
        span.set_tag('stage_a.confidence', confidence_a)
    
    # Stage B (conditional)
    if confidence_a < 0.95:
        with tracer.trace('stage_b.probe'):
            prob_b = run_probe()
            span.set_tag('stage_b.probability', prob_b)
    
    # Decision
    with tracer.trace('decision_engine'):
        final_score = aggregate_scores()
        action = determine_action(final_score)
```

### Custom Metrics

| Metric | Type | Unit | Alert Threshold |
|--------|------|------|------------------|
| `hallucination.detect.latency` | Histogram | ms | p95 > 100ms |
| `hallucination.rate` | Gauge | % | > 30% |
| `stage_a.confidence` | Histogram | 0-1 | Monitor dist |
| `stage_b.accuracy` | Gauge | % | < 85% |
| `detection.cost_per_query` | Gauge | $ | > $0.01 |
| `cache.hit_rate` | Gauge | % | < 80% |
| `false_positive_rate` | Gauge | % | > 5% |

### Dashboard Layout

**Widget 1**: Real-time Detection Rate (Time Series)
- Y-axis: % of answers flagged as hallucinated
- Time range: Last 24h
- Alert: Rate > 35% (anomaly)

**Widget 2**: Latency Percentiles (Histogram)
- p50, p95, p99, p99.9
- Target: p95 < 100ms

**Widget 3**: Accuracy Metrics (Gauge)
- Overall accuracy, precision, recall, F1
- Target: ≥85% accuracy

**Widget 4**: Cost Tracking (Time Series)
- Cost/query trend
- Monthly spend projection

**Widget 5**: Stage Distribution (Pie Chart)
- % requests by stage (A, B, C, D)
- Expected: 70% stage A+B, 20% stage C, 5% stage D

### SLOs (Service Level Objectives)

```yaml
latency_slo:
  p95: 100ms
  p99: 200ms
  
accuracy_slo:
  accuracy: 85%
  precision: 80%  # False positive critical
  recall: 80%
  
error_rate_slo:
  max_error_rate: 1%
  max_timeout_rate: 0.5%

cost_slo:
  max_cost_per_query: $0.01
  monthly_budget: $5000
```

---

## SECTION 5: PHASE 2 COMPLETION CHECKLIST

✅ **Architecture Documentation**
- ✓ Multi-stage pipeline designed (Stage A-D)
- ✓ Latency budget: <100ms p95 feasible
- ✓ Datadog instrumentation spec defined

✅ **API Specification**
- ✓ Request/response schemas locked
- ✓ HTTP status codes defined
- ✓ Error handling strategy documented

✅ **Training Strategy**
- ✓ Data pipeline: 100k examples (HaluEval + proprietary)
- ✓ LoRA configuration: rank=16, alpha=32
- ✓ Target metrics: 85% accuracy, 80% precision/recall

✅ **Design Decisions**
- ✓ Multi-stage chosen over single LLM judge
- ✓ LoRA chosen over full fine-tune (100x cost savings)
- ✓ Cached responses with embedding dedup for cost control

✅ **Monitoring & Observability**
- ✓ APM trace structure defined
- ✓ 7 custom metrics specified
- ✓ 5-widget Datadog dashboard designed
- ✓ SLOs locked (latency, accuracy, cost)

✅ **Development Roadmap**
- ✓ Days 5-9 sprint breakdown detailed in PHASE2_PLAN.md
- ✓ Daily commit checkpoints defined
- ✓ Integration test strategy specified

---

## PHASE 2 STATUS: COMPLETE ✅

**Documents Delivered**:
1. PHASE2_PLAN.md - Comprehensive architecture (313 lines)
2. PHASE2_DELIVERABLES.md - API, training, decisions, monitoring (this file)

**Ready for Phase 3**: Days 5-9 Full Build
- FastAPI gateway implementation
- LoRA probe training
- Stage C context verification
- Stage D LLM fallback
- Integration testing
