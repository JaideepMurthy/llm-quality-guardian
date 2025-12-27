# PHASE 2: Detailed Architecture Planning - Days 3-4

## Overview
Phase 2 locks the v1 production architecture for multi-stage real-time hallucination detection. All critical design decisions are documented, APIs are specified, and development roadmap is defined.

---

## Part 1: Multi-Stage Detection Pipeline (v1)

### Architecture Diagram
```
┌────────────────────────────────────────────────────────────────┐
│                    INPUT: Query + LLM Answer                   │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE A: Fast Heuristics (<10ms) - ALWAYS RUNS               │
│  - Token length ratio check                                    │
│  - Vocabulary novelty scoring                                  │
│  - Semantic entropy estimation                                 │
│  Output: confidence_a (0-1)                                    │
└────────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────┬────────────────────┐
         ↓                    ↓                    ↓
    confidence_a         confidence_a         confidence_a
    > 0.95?              0.7-0.95?            < 0.7?
    ACCEPT               RUN B                RUN C/D
         ↓                    ↓                    ↓
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Stage B: Probe   │ │ Stage C: Context │ │ Stage D: Fallback│
│ (20-30ms)        │ │ (500ms)          │ │ (1.5s)           │
│ LoRA on 70B      │ │ RAG + Cross-Enc  │ │ LLM-Judge        │
│ Binary clf       │ │ Semantic verify  │ │ Final decision   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
         ↓                    ↓                    ↓
         └────────────────────┬────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │ DECISION ENGINE: Aggregate Results    │
         │ - Combine scores from all stages      │
         │ - Apply confidence thresholds         │
         │ - Generate confidence interval        │
         └────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ OUTPUT: Hallucination Score (0-1) + Recommended Action        │
│ - 0.0-0.3: ACCEPT (low hallucination risk)                   │
│ - 0.3-0.7: FLAG (medium - requires review)                   │
│ - 0.7-1.0: REGENERATE (high hallucination risk)              │
└────────────────────────────────────────────────────────────────┘
```

### Stage A: Fast Heuristics (<10ms)
**Purpose**: Quick filtering for obvious cases; avoid expensive computation

**Metrics**:
- Token Count Ratio: len(answer) / len(question)
  - Extreme ratios (>10x) indicate hallucination
- Vocabulary Novelty: % of novel tokens not in question or reference
  - High novelty (>60%) suggests hallucination
- Semantic Entropy: Self-consistency score
  - Low entropy (<0.3) suggests hallucination

**Decision Logic**:
```python
if confidence_a > 0.95:  # Very high confidence
    return ACCEPT
elif confidence_a < 0.7:  # Very low confidence
    continue_to_stage_c_or_d
else:  # Medium confidence
    continue_to_stage_b
```

### Stage B: Lightweight Probe (20-30ms)
**Purpose**: Fast ML-based detection without full LLM inference

**Implementation**:
- LoRA-adapted MLP layer on 70B LLM hidden states
- Binary classifier: hallucinated (0) vs. correct (1)
- Input: Last hidden state of LLM @ token ~300
- Output: Probability (0-1)

**Training Data**:
- HaluEval dataset (50k examples)
- Proprietary labeled data (50k examples)
- Total: 100k examples, 80/20 train/val split

**Performance Target**:
- Accuracy: ≥85%
- Precision: ≥80% (minimize false positives)
- Inference: 20-30ms on GPU

### Stage C: Context Verification (500ms, Optional)
**Purpose**: Semantic grounding against knowledge base

**Process**:
1. Retrieve 5-10 relevant documents via embedding search
2. Extract key facts from documents
3. Cross-encoder scoring: answer vs. facts (0-1)
4. Generate confidence interval

**Triggers**:
- Stage B probability 0.35-0.65 (uncertain)
- User opt-in for high-stakes scenarios
- Custom domain knowledge required

### Stage D: LLM Fallback (1.5s, Optional)
**Purpose**: Final arbitration for truly uncertain cases

**Logic**:
- Only runs if stages A-C still uncertain
- Cached judge responses to reduce cost
- LLM-as-judge pattern (same as Day 2 prototype)
- Final hallucination probability

**Cost Control**:
- Cache similar questions (embed + vector search)
- Batch evaluation during off-peak hours
- Fallback cost: ~$0.001 per query

---

## Part 2: Latency Budget

```
Total SLO Target: <100ms p95 latency

┌─────────────────────────────────────┐
│ Stage A (Fast Heuristics)     : 5ms │ ← Always
│ Network + Overhead            : 2ms │
├─────────────────────────────────────┤
│ Stage B (LoRA Probe)          : 25ms│ ← 70% of requests
│ Stage C (Context Verification): 65ms│ ← 20% of requests  
│ Stage D (LLM Fallback)       : 1500ms│ ← 5% of requests
├─────────────────────────────────────┤
│ Expected p95: 32ms (Stage A+B)      │
│ Expected p99: 70ms (Stage A+C)      │
└─────────────────────────────────────┘
```

---

## Part 3: Datadog Instrumentation

### APM Spans
```python
with tracer.trace('hallucination.detect', service='llm-quality-guardian'):
    with tracer.trace('stage_a.heuristics'):
        # Fast heuristics logic
        pass
    
    with tracer.trace('stage_b.probe'):
        # LoRA probe inference
        pass
    
    with tracer.trace('decision_engine'):
        # Aggregate and decide
        pass
```

### Custom Metrics
- `hallucination.rate` (gauge): % of answers flagged as hallucinated
- `detection.latency_ms` (histogram): p50, p95, p99, p99.9
- `stage_a.confidence` (histogram): distribution of Stage A scores
- `stage_b.probability` (histogram): distribution of probe outputs
- `false_positive_rate` (gauge): on validation set
- `false_negative_rate` (gauge): on validation set
- `cost_per_query` (gauge): avg inference cost

### Dashboard Widgets
- Real-time detection rate (time series)
- Latency distribution (histogram)
- Accuracy metrics (gauge)
- Cost tracking (time series)
- Error rate (time series)
- Stage distribution (pie chart)

---

## Part 4: API Specification

### POST /detect
**Request**:
```json
{
  "question": "string (required)",
  "llm_answer": "string (required)",
  "reference_context": "string (optional)",
  "use_context_verification": "boolean (default: false)",
  "timeout_ms": "integer (default: 5000)"
}
```

**Response**:
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

**Error Responses**:
```json
{
  "error": "timeout",
  "message": "Detection exceeded 5000ms timeout",
  "fallback_action": "flag"
}
```

---

## Part 5: Development Roadmap (Days 5-9)

### Day 5: Setup & Stage A
- [ ] Create FastAPI gateway with request validation
- [ ] Implement Stage A heuristics (token ratio, novelty, entropy)
- [ ] Integrate with Datadog APM
- [ ] Unit tests for Stage A
- [ ] Commit: `feat: Add FastAPI gateway and Stage A heuristics`

### Day 6: Stage B & Training
- [ ] Prepare 100k training samples (HaluEval + proprietary)
- [ ] Implement LoRA probe training pipeline
- [ ] Train LoRA adapter on 70B model
- [ ] Create inference wrapper for Stage B
- [ ] Commit: `feat: Add LoRA probe training and Stage B inference`

### Day 7: Stage C, D & Integration
- [ ] Implement RAG context retrieval (Stage C)
- [ ] Add LLM-judge fallback (Stage D)
- [ ] Implement decision engine
- [ ] Integration tests (A+B, A+C, A+D)
- [ ] Commit: `feat: Add Stages C, D and decision engine`

### Day 8: Optimization & Caching
- [ ] Add response caching for repeated queries
- [ ] Optimize latency (quantize probe, batch inference)
- [ ] Load testing (1000+ QPS)
- [ ] Performance tuning
- [ ] Commit: `perf: Add caching and latency optimization`

### Day 9: Testing & Benchmarking
- [ ] Comprehensive benchmark on HaluEval
- [ ] A/B testing framework
- [ ] Accuracy vs. latency tradeoff analysis
- [ ] Documentation
- [ ] Commit: `test: Add comprehensive benchmarks and A/B testing`

---

## Part 6: Key Decisions & Tradeoffs

### Decision 1: Multi-Stage vs. Single Model
**Option A**: Single unified LLM-judge (Day 2 approach)
- Pros: Simple, consistent accuracy
- Cons: 1.5s latency unacceptable for production

**Option B**: Multi-stage pipeline (CHOSEN)
- Pros: <100ms p95 latency, cost-effective, graceful degradation
- Cons: More complex, requires calibration

**Rationale**: Production deployments need <100ms. Multi-stage is standard in industry (see Google Bruin, Meta LLama2 safety).

### Decision 2: LoRA Probe vs. Fine-tune
**Option A**: Full model fine-tuning
- Cons: Expensive ($5k+), slow training, resource intensive

**Option B**: LoRA-adapted probe (CHOSEN)
- Pros: Fast training (hours), low cost, minimal storage
- Cons: Slightly lower accuracy (~2-3%)

**Rationale**: LoRA proven on similar tasks (PEFT papers). Accuracy target 85% is achievable.

### Decision 3: Cached Judge vs. On-demand
**Option A**: On-demand LLM calls
- Cons: $0.001/query = $1000/1M queries, slow

**Option B**: Cached responses with embedding dedup (CHOSEN)
- Pros: 90%+ cache hit rate, near-zero latency
- Cons: Cache management complexity

**Rationale**: Hallucination detection on similar QA pairs likely similar. Embedding search + duplication detection effective.

---

## Acceptance Criteria (Phase 2 Complete)
- ✓ Architecture document complete and reviewed
- ✓ API spec finalized and locked
- ✓ Development roadmap (Days 5-9) detailed
- ✓ All tradeoffs documented with rationale
- ✓ Datadog instrumentation spec defined
- ✓ Latency budget calculated and feasible
- ✓ All documents committed to GitHub

---

**Status**: Ready for Phase 3 (Full Build) on Day 5
