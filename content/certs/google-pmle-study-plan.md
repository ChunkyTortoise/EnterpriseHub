# Google Professional Machine Learning Engineer (PMLE) Study Plan

**Target**: Pass in 12-16 weeks | **Exam cost**: $200 | **Background**: Senior Python/AI, RAG, FastAPI, LLMs, PostgreSQL, Redis

---

## Exam Domains & Weightings

| Domain | Weight | Core Topics |
|--------|--------|-------------|
| 1. Architecting low-code ML solutions | ~18% | AutoML, Vertex AI no-code tools, pre-trained APIs, model selection |
| 2. Collaborating / managing data and models | ~22% | Feature Store, Model Registry, Vertex Experiments, data validation, MLMD |
| 3. Scaling prototypes into ML models | ~18% | Distributed training, Vertex Training, custom containers, Vertex Vizier |
| 4. Serving and scaling models | ~16% | Vertex Prediction, model versioning, traffic splitting, explainability |
| 5. Automating and orchestrating ML pipelines | ~16% | Vertex Pipelines (KFP v2), TFX, Cloud Composer, artifact lineage |
| 6. Monitoring, optimizing, maintaining | ~10% | Model monitoring, skew/drift, retraining triggers, cost optimization |

**Exam**: 2 hours, ~60 questions, multiple choice + multi-select | **Pass score**: ~70%

---

## 12-Week Study Plan (8-12h/week)

### Phase 1: Foundation & Vertex AI Basics (Weeks 1-3)

**Week 1 — GCP Foundations + Vertex AI Overview** (8h)
- GCP fundamentals: IAM, VPC, Cloud Storage, BigQuery basics (2h)
- Vertex AI architecture: Workbench, Datasets, Experiments, Model Registry (3h)
- AutoML Tables, AutoML Vision, Natural Language API — hands-on (3h)
- **Lab**: Train one AutoML Tables model on a public dataset

**Week 2 — Data Engineering for ML + Feature Store** (10h)
- BigQuery ML: `CREATE MODEL`, `ML.PREDICT`, `ML.EVALUATE` (3h)
- Vertex AI Feature Store v2: online serving, offline ingestion (3h)
- TensorFlow Data Validation (TFDV): schema inference, anomaly detection (2h)
- Dataflow for ML preprocessing: Apache Beam basics, `tf.data` pipelines (2h)
- **Lab**: Build a Feature Store with 3+ features, serve online predictions

**Week 3 — Custom Training on Vertex AI** (10h)
- Custom training jobs: pre-built containers, custom containers via Artifact Registry (3h)
- Hyperparameter tuning with Vertex Vizier: `cloudml-hypertune`, Bayesian optimization (3h)
- Distributed training: `MirroredStrategy`, `MultiWorkerMirroredStrategy`, Reduction Server (2h)
- TPU fundamentals: when to use, `TPUStrategy`, cost tradeoffs (2h)
- **Lab**: Launch a custom training job with Vizier hyperparameter tuning

### Phase 2: MLOps Core (Weeks 4-7)

**Week 4 — Vertex Pipelines + KFP v2** (12h)
- KFP v2 SDK: `@component`, `@pipeline`, artifact types (3h)
- Multi-step pipelines: data validation → training → evaluation → conditional deployment (4h)
- Pipeline scheduling, caching, parameterization (3h)
- Cloud Composer vs Vertex Pipelines (2h)
- **Lab**: 5-step KFP pipeline that trains, evaluates, and conditionally deploys

**Week 5 — TFX (TensorFlow Extended)** (10h)
- TFX components: `ExampleGen`, `StatisticsGen`, `SchemaGen`, `ExampleValidator` (3h)
- `Transform`, `Trainer`, `Evaluator` with TFMA (3h)
- `Pusher`, `InfraValidator`, ML Metadata (MLMD) lineage tracking (2h)
- TFX on Vertex Pipelines (2h)
- **Lab**: Full TFX pipeline end-to-end (Penguin or Chicago Taxi dataset)
- ⚠️ TFX is heavily tested — do not skip

**Week 6 — Model Serving + Explainability** (10h)
- Vertex Prediction: online endpoints, dedicated vs shared, pre/post-processing (3h)
- Batch prediction jobs: BigQuery input/output, scaling (2h)
- Explainable AI: SHAP, Integrated Gradients, XRAI for images, `ExplanationMetadata` (3h)
- Traffic splitting: canary deployments, A/B testing via Vertex endpoints (2h)
- **Lab**: Deploy model with SHAP explanations enabled

**Week 7 — Model Monitoring + Drift Detection** (8h)
- Vertex AI Model Monitoring: prediction drift, feature skew, training-serving skew (3h)
- Alert configuration: Pub/Sub integration, retraining triggers, thresholds (2h)
- Continuous evaluation: `ModelEvaluationSlice`, fairness metrics, degradation detection (3h)
- **Lab**: Configure model monitoring, set up Pub/Sub alert

### Phase 3: Advanced Topics + Gap Filling (Weeks 8-10)

**Week 8 — Responsible AI + MLOps at Scale** (10h)
- Fairness: What-If Tool, Fairness Indicators, sliced evaluation in TFMA (3h)
- Model cards, data cards, Vertex Experiments tracking (3h)
- Cost optimization: preemptible/Spot VMs, committed use discounts (2h)
- CI/CD for ML: Cloud Build triggers, GitHub Actions + `gcloud ai` CLI (2h)

**Week 9 — Specialized ML Scenarios** (10h)
- NLP on Vertex: fine-tuning `text-bison`, Embeddings API, semantic search (3h)
- Recommendation systems: collaborative filtering with BigQuery ML, two-tower models (3h)
- Time-series forecasting: `ARIMA_PLUS` in BigQuery ML, Vertex Forecast (2h)
- Tabular data: XGBoost on Vertex, feature importance (2h)

**Week 10 — Security, Compliance, Networking** (8h)
- VPC Service Controls for Vertex AI, private endpoints (2h)
- CMEK for models/datasets, Workload Identity (2h)
- Data governance: DLP API for training data, data lineage in Dataplex (2h)
- Shared VPC for Vertex training, PSC endpoints (2h)

### Phase 4: Exam Readiness (Weeks 11-12)

**Week 11 — Practice Exam Blitz** (12h)
- Practice exam #1 — full timed 120 min, review all wrong answers (4h)
- Deep-dive review of weakest domain (3h)
- Practice exam #2 — different question bank, timed (4h)
- Targeted codelab catchup on weak areas (1h)

**Week 12 — Final Review** (8h)
- Flashcard review: Vertex AI service names, KFP types, TFX components (2h)
- Re-read official exam guide, verify coverage of every bullet point (2h)
- Light practice questions — confidence maintenance (2h)
- Schedule exam, verify ID, test environment (2h)

**→ Schedule exam for end of Week 12 or early Week 13**

---

## Key Gaps to Address (Priority Order)

| Gap | Priority | Why |
|-----|----------|-----|
| **Vertex AI service landscape** (which service for which scenario) | HIGH | Exam tests service selection heavily |
| **TFX pipeline components** (inputs/outputs, MLMD) | HIGH | Heavily weighted, no Python analog |
| **Dataflow / Apache Beam** (PCollection, PTransform, windowing) | MEDIUM-HIGH | ML preprocessing scenarios |
| **BigQuery ML syntax** (`CREATE MODEL`, model types, `ML.*` functions) | MEDIUM | Exam-heavy, different from PostgreSQL |
| **Vertex AI Feature Store v2** (FeatureOnlineStore, FeatureView) | MEDIUM | Redis knowledge helps conceptually |
| **KFP v2 SDK specifics** (`dsl.Condition`, `dsl.ParallelFor`, caching) | MEDIUM | Syntax is exam-tested |
| **Explainable AI config** (SHAP vs IG, `ExplanationMetadata`) | LOWER | Frequently tested, quick to learn |

---

## Quick Wins — Skip Deep Study On These

You already have strong coverage here. 30-60 min review max:

- REST API design for ML serving (→ just learn Vertex prediction request format)
- LLM/RAG/embedding concepts (→ just learn Vertex Embeddings API endpoint names)
- Async/concurrent processing (→ apply to Dataflow concepts only)
- Database optimization (→ map to BigQuery partitioning/clustering)
- Caching strategies (→ learn Vertex prediction endpoint caching specifics)
- Containerization (→ learn `custom_container_training_spec` syntax only)
- CI/CD concepts (→ learn Cloud Build + Vertex AI CLI triggers)
- Monitoring/observability (→ learn Vertex Model Monitoring specifics)
- Python ML libraries (→ know which pre-built containers support what)
- Vector similarity search (→ learn Vertex AI Vector Search API names)

**Estimated time saved**: 25-35 hours

---

## Top Resources

### Must-Use (Free)
- [Official PMLE Exam Guide](https://cloud.google.com/learn/certification/guides/machine-learning-engineer)
- [Vertex AI Codelabs](https://codelabs.developers.google.com/?category=aiandmachinelearning)
- [Vertex AI Samples GitHub](https://github.com/GoogleCloudPlatform/vertex-ai-samples)
- [TFX Penguin Pipeline Tutorial](https://www.tensorflow.org/tfx/tutorials/tfx/penguin_simple)
- [BigQuery ML Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigquery-ml-syntax)
- [Google Cloud Skills Boost](https://cloudskillsboost.google) (free tier labs)

### Best Paid
- **TutorialsDojo PMLE Practice Exams** — $14.99, highest quality questions
- **Udemy — Dan Sullivan PMLE** — ~$19.99, strong community pass rate
- **"Machine Learning Design Patterns"** (O'Reilly, Lakshmanan et al.) — written by Googlers who know the exam
- **Coursera: Preparing for PMLE** (Google-official) — ~$49/month

### Practice Exam Sources (ranked)
1. TutorialsDojo — $14.99, best explanations
2. Examtopics — free/limited, read community discussions for corrections
3. Whizlabs — $19.95, good volume (flag outdated Vertex v1 questions)
4. Udemy Dan Sullivan — ~$19.99

**Target**: Score 80%+ consistently before booking the exam.

---

## Exam-Day Pattern Recognition

- **"Most cost-effective"** → AutoML or BigQuery ML (managed, no infra)
- **"Least operational overhead"** → Managed services, not custom
- **"Fastest time to production"** → AutoML, pre-trained APIs
- **"Maximum control"** → Custom containers, custom training
- **Drift/skew detection** → Vertex Model Monitoring (never manual queries)
- **Retraining trigger** → Cloud Scheduler + Pub/Sub + pipeline job

---

**Realistic target score with this background**: 75-85%
**Book the exam**: End of Week 11 to create a deadline forcing function
