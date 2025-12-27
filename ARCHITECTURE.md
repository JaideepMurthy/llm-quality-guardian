# LLM Quality Guardian - System Architecture

## Day 2 Prototype (Complete)
Lightweight, single-stage hallucination detection using LLM-as-judge factual scoring.

### Components
- **Detector**: Google Generative AI model scoring factual correctness (0-100)
- **Logger**: Custom Datadog trace instrumentation with tag-based metrics
- **Evaluator**: HaluEval benchmark evaluation with threshold optimization

### Performance
- Accuracy: 80%+ on HaluEval samples
- Latency: <2s per detection (v0 LLM-based)
- Metrics: 50+ custom Datadog tags per span

---

## Phase 2-5 Production Architecture (v1)

### Design Goals
1. **Sub-100ms Latency**: Lightweight probes replace LLM judges
2. **Scalable Streaming**: Real-time detection for 1000+ QPS
3. **Enterprise Observability**: Full Datadog APM integration
4. **Graceful Fallback**: Multi-stage pipelines with degradation

### Proposed v1 Components

#### 1. Input Gateway (FastAPI)
- REST/gRPC endpoints for query + response pairs
- Request validation & auth
- Rate limiting (Datadog dashboards)

#### 2. Detection Pipeline (Parallel Stages)

**Stage A: Fast Heuristics (<10ms)**
- Token length ratio (answer vs reference)
- Vocabulary novelty scoring
- Confidence entropy (semantic)

**Stage B: Lightweight Probe (20-30ms)**
- LoRA-adapted MLP on LLM hidden states (70B model)
- Binary classifier: hallucinated / correct
- Trained on HaluEval + proprietary data

**Stage C: Context Verification (optional, ~500ms)**
- Retrieve knowledge base context via embedding
- Compare answer against retrieved facts
- Cross-encoder similarity scoring

**Stage D: Fallback LLM-Judge (optional, ~1.5s)**
- Used only if stages A-C uncertain
- Cached judge responses for cost

#### 3. Decision Engine
```
if stage_a_score > 0.95 → ACCEPT
else if stage_b_prob_hallucinated > 0.8 → FLAG
else if uncertainty_high → STAGE_C
else → ACCEPT
```

#### 4. Datadog Integration
- **Traces**: APM spans for each detection
  - span_type: `hallucination.detect`
  - tags: `score`, `stage`, `latency_ms`, `model`, `question_domain`
- **Metrics**: Custom gauges
  - `hallucination_rate_pct`
  - `detection_latency_p50/p95/p99`
  - `stage_fallthrough_rate`
  - `false_positive_rate` (on validation set)
- **SLOs**: <100ms p95 latency, <2% false positive rate

#### 5. Output
JSON response with fields:
```json
{
  "hallucination_score": 0.15,
  "is_hallucinated": false,
  "confidence": 0.92,
  "detection_stage": "stage_b",
  "latency_ms": 42,
  "recommended_action": "accept" | "flag" | "regenerate",
  "explanations": ["70% vocab match with reference"]
}
```

### Data Pipeline
- Continuous logging of detections → Datadog
- Monthly retraining on false positives
- A/B test new stages vs production

### Deployment
- Google Cloud Run (auto-scaling)
- Vertex AI serving for LLM endpoints
- Datadog monitoring with PagerDuty alerts

### Timeline
- Days 3-4: Finalize architecture, define v1 scope
- Days 5-9: Build probe training, streaming infrastructure
- Days 10-11: Integration testing, demo video
- Days 12-14: Devpost submission, polish

---

## Security & Privacy
- No PII storage in logs
- Rate limiting per API key
- Encrypted data at rest (GCP)

## Success Metrics
- Hackathon: 1st place placement
- Technical: <100ms p95, 85%+ accuracy on public benchmarks
- Business: Reduce enterprise LLM deployment risks by 80%
