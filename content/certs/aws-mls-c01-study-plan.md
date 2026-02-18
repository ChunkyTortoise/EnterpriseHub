# AWS Certified Machine Learning — Specialty (MLS-C01) Study Plan

**Target**: Pass in 16 weeks | **Exam cost**: $300 | **65 questions, 180 min, ~75% passing**
**Background**: Senior Python/AI, RAG, FastAPI, PostgreSQL, Redis, Docker, CI/CD. PMLE running parallel.

---

## Exam Domains & Weightings

| Domain | Weight | ~Questions |
|--------|--------|-----------|
| 1. Data Engineering | 20% | 13 |
| 2. Exploratory Data Analysis | 24% | 16 |
| 3. Modeling | 36% | 23 |
| 4. ML Implementation & Operations | 20% | 13 |

---

## 16-Week Study Plan (6-8h/week)

### Phase 1: Foundation & Data Layer (Weeks 1-4)

**Week 1** (7h) — AWS ML Ecosystem + S3/Lake Formation
- Diagnostic test on TutorialsDojo — note wrong answers by domain
- S3 for ML: storage classes, lifecycle, S3 Select, Object Lambda
- Lake Formation: governed tables, permissions, blueprints
- Glue Data Catalog: crawlers, classifiers, schemas

**Week 2** (5h, reduced — PMLE parallel) — Kinesis Ecosystem
- Kinesis Data Streams: shards, partition keys, KCL/KPL, enhanced fan-out
- Kinesis Firehose: destinations (S3/Redshift/OpenSearch), Lambda transform, buffering
- Kinesis Data Analytics (Flink): SQL on streams, windowing
- Kinesis Video Streams: Rekognition Video integration
- ⚠️ Key trap: Streams needs consumer code, Firehose is fully managed delivery

**Week 3** (7h) — Glue ETL + Athena + EMR
- Glue ETL: DynamicFrames vs DataFrames, job bookmarks, Glue Studio, Databrew
- Athena: partitioning, columnar formats (Parquet, ORC), CTAS, federated queries
- EMR: cluster types, instance groups vs fleets, Spark/Hive/Presto, EMR Serverless
- Glue vs EMR: Glue=serverless ETL to S3/Redshift; EMR=full Spark control, cheaper at scale

**Week 4** (8h) — SageMaker Core Architecture
- SageMaker Studio: Domains, user profiles, JupyterServer, KernelGateway apps
- Training jobs: containers, BYOC, script mode, distributed training
- Feature Store: online vs offline store, feature groups, ingestion APIs
- Data Wrangler: 300+ transforms, data flow export to Pipelines/Feature Store

### Phase 2: Algorithms & Modeling (Weeks 5-9)

**Week 5** (7h) — Built-in Algorithms Part 1 (highest ROI week)

| Algorithm | Problem | Input | Notes |
|-----------|---------|-------|-------|
| XGBoost | Class/Regression | CSV, LibSVM, Parquet | Most common on exam |
| Linear Learner | Class/Regression | CSV, RecordIO | Binary + multiclass |
| K-Means | Clustering | CSV, RecordIO | Elbow method for K |
| KNN | Class/Regression | CSV, RecordIO | Good baseline |
| Factorization Machines | Recommendation | RecordIO-protobuf ONLY | Sparse data |
| DeepAR | Time Series | JSON Lines | Key differentiator |

**Week 6** (7h) — Built-in Algorithms Part 2

| Algorithm | Problem | Notes |
|-----------|---------|-------|
| BlazingText | Text class, Word2Vec | modes: supervised/skipgram/cbow/batch_skipgram |
| Seq2Seq | Translation, summarization | MXNet, GPU required |
| Object Detection | CV bounding boxes | ResNet backbone |
| Image Classification | CV classes | ResNet, fine-tuning |
| Semantic Segmentation | CV pixel masks | MXNet, GPU only |
| LDA / NTM | Topic modeling | LDA=RecordIO, NTM=RecordIO |
| PCA | Dimensionality reduction | Regular vs Randomized |
| Random Cut Forest | Anomaly detection | Exam favorite |
| IP Insights | IP anomaly | entity pair anomalies |

**Week 7** (5h, reduced) — HPO + Model Evaluation
- SageMaker HPO: Bayesian (default), Random, Hyperband, Warm start (IDENTICAL vs TRANSFER)
- Evaluation metrics by problem: AUC vs F1 vs RMSE — know when
- SageMaker Experiments: tracking, compare training runs
- Clarify bias metrics: pre-training (CI, DPL) / post-training (DI, AD, DPPL)

**Week 8** (7h) — Deep Learning on SageMaker
- Distributed training: SMDDP (data parallel) vs SMMP (model parallel) — SMMP when model doesn't fit one GPU
- JumpStart: foundation models, fine-tuning, deployment
- Autopilot: AutoML, explainability reports, candidate exploration
- Custom containers: `sagemaker-training-toolkit`, `/opt/ml/` directory structure
- Spot training: `use_spot_instances=True`, `max_wait`, checkpoint to S3 for recovery

**Week 9** (8h) — Inference Architecture
- Real-time endpoints: auto-scaling, production variants (A/B via weights), instance types (ml.g4dn for GPU)
- Serverless inference: concurrency, cold starts, when NOT to use (latency-sensitive)
- Async inference: S3 input/output, SNS notification
- Batch transform: `BatchStrategy` (MultiRecord vs SingleRecord), `SplitType`
- Multi-model endpoints (MME): shared container, dynamic loading
- Inference Pipeline: serial container chains (preprocessing → model → postprocessing)

### Phase 3: AWS AI Services & MLOps (Weeks 10-13)

**Week 10** (6h, reduced) — AWS AI Services

| Service | Use Case | Key API |
|---------|----------|---------|
| Rekognition Image | Object/face/text detection | `DetectLabels`, `CompareFaces` |
| Rekognition Video | Activity in video | Async + SNS, Kinesis Video input |
| Comprehend | NLP: entities, sentiment | Custom classification/NER |
| Comprehend Medical | Clinical NLP, PHI detection | ICD-10/RxNorm |
| Translate | Neural MT | Custom terminology |
| Transcribe | Speech-to-text | Custom vocabulary, PII redaction |
| Textract | Document extraction | `AnalyzeDocument`, forms/tables |
| Forecast | Time series | AutoML, DeepAR+ backed |
| Personalize | Recommendations | Recipes, campaigns, event tracker |
| Kendra | Intelligent search | Connectors, FAQs |
| Lex | Conversational AI | Intents, slots, Lambda fulfillment |

⚠️ Know when NOT to use SageMaker: use Comprehend for standard sentiment, Forecast over DeepAR for AutoML time series, Personalize for standard recommendations.

**Week 11** (7h) — MLOps: SageMaker Pipelines + Model Registry
- Pipelines: Pipeline, Step types (ProcessingStep, TrainingStep, RegisterModel, ConditionStep)
- Model Registry: model groups, versions, approval status, CI/CD hooks
- SageMaker Projects: MLOps templates, CodePipeline integration, EventBridge triggers
- Model Monitor: data quality, model quality, bias drift, feature attribution drift; baseline constraints
- Clarify in production: continuous fairness monitoring, SHAP feature attribution

**Week 12** (7h) — Security + Cost Optimization
- SageMaker security: VPC-only mode (`EnableNetworkIsolation`), interface VPC endpoints, IMDSv2
- IAM for ML: execution role, cross-account deployment, resource vs identity policies
- Encryption: KMS CMK for notebooks/training/endpoints, inter-node encryption for distributed
- Cost: Spot instances, Savings Plans, right-sizing via CloudWatch, Graviton for inference
- Well-Architected ML Lens: 6 pillars applied to ML workloads

**Week 13** (5h, reduced) — Redshift ML + Step Functions
- Redshift ML: `CREATE MODEL` SQL, SageMaker Autopilot integration, `PREDICT` function
- OpenSearch k-NN: vector embeddings, ML nodes
- Step Functions for ML: Map state for parallel, comparison to SageMaker Pipelines
- EventBridge + Lambda: event-driven retraining patterns

### Phase 4: Exam Readiness (Weeks 14-16)

**Week 14** (8h) — Full Domain Review
- Use diagnostic results from Week 1 to focus on weak domains
- 50+ algorithm selection practice questions (Domain 3)

**Week 15** (8h) — Practice Exam Blitz
- TutorialsDojo Exam 1 (full, timed 65q) → review wrong answers
- TutorialsDojo Exam 2 (full, timed)
- Stephane Maarek Udemy practice set
- Target: 80%+ on TutorialsDojo before booking

**Week 16** (6h) — Final Polish + Exam
- AWS Skill Builder official 20-question practice (free)
- Cheat sheet review: algorithm table, service use cases, inference modes
- Weak algorithm flashcard drill
- Schedule exam for end of Week 16

---

## Key Gaps to Address

| Gap | Priority | Why |
|-----|----------|-----|
| SageMaker service anatomy (training jobs, estimator, `fit()`) | HIGH | Core of exam |
| Kinesis capacity math (shards, MB/s limits) | HIGH | Domain 1 staple |
| SageMaker built-in algorithm hyperparameters | HIGH | Very testable |
| AWS AI services vs SageMaker tradeoffs | HIGH | Scenario questions |
| Glue vs EMR decision tree | MEDIUM | Data engineering |
| RecordIO-protobuf format (convert from numpy/pandas) | MEDIUM | Algorithm input |
| SageMaker Model Monitor (baseline, drift metrics) | MEDIUM | Domain 4 |
| Lake Formation column/row-level security | MEDIUM | Data governance |

---

## Quick Wins — Transfers From Your Background

**Full transfer** (30-60 min review only):
- ML fundamentals: bias/variance, regularization, cross-validation — just map to SageMaker
- Docker/containers: BYOC maps directly; memorize `/opt/ml/` paths
- PostgreSQL → Redshift: add `DISTKEY`, `SORTKEY`, `VACUUM`, `ANALYZE`
- FastAPI → Lambda + API Gateway: map async patterns to SageMaker async inference
- Redis → ElastiCache, Feature Store online store concept
- RAG knowledge → Kendra, OpenSearch k-NN intuition
- CI/CD → SageMaker Pipelines conceptual mapping

---

## Top Resources

| Resource | Cost | Priority |
|----------|------|----------|
| **Stephane Maarek Udemy** (https://www.udemy.com/course/aws-machine-learning/) | ~$15 sale | #1 — best comprehensive coverage |
| **TutorialsDojo practice exams** (https://portal.tutorialsdojo.com/courses/aws-certified-machine-learning-specialty-practice-exams/) | $15-20 | #1 — 6 exams, 390 questions |
| Adrian Cantrill (https://learn.cantrill.io/p/aws-certified-machine-learning-specialty) | $40 | Better for networking/security depth |
| AWS Skill Builder ML Learning Plan (free) | Free | Official; use for 20-question practice set |
| TutorialsDojo cheat sheets (https://tutorialsdojo.com/aws-cheat-sheets/) | Free | Print SageMaker algorithm cheat sheet |

**Total spend**: ~$30 (Maarek + TutorialsDojo on sale) covers 90% of what you need.

---

## Sequencing vs PMLE

**Recommended**: MLS-C01 first (April-May 2026), then PMLE (July-Aug 2026)
- MLS is slightly easier overall — good confidence builder
- SageMaker Pipelines mental model transfers to Vertex AI Pipelines
- Shared concepts (study once, apply to both): ML fundamentals, feature engineering, MLOps principles, model monitoring, responsible AI

**Study-once shared topics**: bias/variance → both, evaluation metrics → both, MLOps pipelines → Vertex vs SageMaker framing, responsible AI → Clarify vs Vertex AI Explainability.

---

## SageMaker Algorithm Quick Reference

```
CLASSIFICATION/REGRESSION
  XGBoost         → CSV/LibSVM/Parquet, CPU
  Linear Learner  → CSV/RecordIO, CPU
  KNN             → CSV/RecordIO, CPU

NLP
  BlazingText     → supervised text class | skipgram/cbow Word2Vec
  Seq2Seq         → JSON Lines, GPU required
  LDA / NTM       → topic modeling, RecordIO

COMPUTER VISION  (all need GPU, augmented manifest or RecordIO)
  Image Classification | Object Detection | Semantic Segmentation

TIME SERIES
  DeepAR          → JSON Lines, CPU/GPU

UNSUPERVISED
  K-Means         → RecordIO/CSV, CPU
  PCA             → RecordIO/CSV, Regular vs Randomized
  RCF             → anomaly detection, RecordIO, CPU
  IP Insights     → IP anomaly, CSV

RECOMMENDATION
  Factorization Machines → RecordIO-protobuf ONLY
```

**Expected outcome**: 780-850 score given background | **Book after**: 80%+ on TutorialsDojo
