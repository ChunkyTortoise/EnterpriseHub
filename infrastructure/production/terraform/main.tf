# ==============================================================================
# JORGE'S BI DASHBOARD - PRODUCTION TERRAFORM INFRASTRUCTURE
# Enterprise-grade AWS infrastructure for business intelligence platform
# ==============================================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    bucket         = "jorge-platform-terraform-state"
    key            = "bi-dashboard/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# ==============================================================================
# PROVIDER CONFIGURATION
# ==============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "jorge-bi-dashboard"
      Environment = "production"
      Owner       = "jorge-real-estate"
      CostCenter  = "business-intelligence"
      Terraform   = "true"
    }
  }
}

# Get EKS cluster information
data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "cluster" {
  name = var.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.cluster.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# ==============================================================================
# DATA SOURCES
# ==============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {}

# ==============================================================================
# RDS - POSTGRESQL DATABASE
# ==============================================================================

# DB Subnet Group
resource "aws_db_subnet_group" "jorge_bi" {
  name       = "jorge-bi-db-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name = "Jorge BI Database Subnet Group"
  }
}

# DB Parameter Group
resource "aws_db_parameter_group" "jorge_bi" {
  family = "postgres15"
  name   = "jorge-bi-postgres15"

  # Performance optimization for BI workloads
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4}"
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory*3/4}"
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "2048000"  # 2GB
  }

  parameter {
    name  = "checkpoint_completion_target"
    value = "0.7"
  }

  parameter {
    name  = "wal_buffers"
    value = "16384"  # 16MB
  }

  parameter {
    name  = "default_statistics_target"
    value = "100"
  }

  parameter {
    name  = "random_page_cost"
    value = "1.1"
  }

  parameter {
    name  = "effective_io_concurrency"
    value = "200"
  }

  tags = {
    Name = "Jorge BI PostgreSQL Parameters"
  }
}

# Security Group for RDS
resource "aws_security_group" "jorge_bi_rds" {
  name        = "jorge-bi-rds-sg"
  description = "Security group for Jorge BI PostgreSQL database"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.jorge_bi_app.id]
    description     = "PostgreSQL access from application"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "Jorge BI RDS Security Group"
  }
}

# RDS Instance
resource "aws_db_instance" "jorge_bi" {
  identifier = "jorge-bi-production"

  # Engine Configuration
  engine                = "postgres"
  engine_version        = "15.4"
  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.jorge_bi.arn

  # Database Configuration
  db_name  = "jorge_bi_production"
  username = var.db_username
  password = var.db_password

  # Network Configuration
  db_subnet_group_name   = aws_db_subnet_group.jorge_bi.name
  vpc_security_group_ids = [aws_security_group.jorge_bi_rds.id]
  publicly_accessible    = false
  port                   = 5432

  # Parameter and Option Groups
  parameter_group_name = aws_db_parameter_group.jorge_bi.name

  # Backup Configuration
  backup_retention_period   = 30
  backup_window            = "03:00-04:00"
  maintenance_window       = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = false

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "jorge-bi-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Name = "Jorge BI Production Database"
  }
}

# Read Replica for Analytics
resource "aws_db_instance" "jorge_bi_read_replica" {
  identifier = "jorge-bi-read-replica"

  # Replica Configuration
  replicate_source_db = aws_db_instance.jorge_bi.id
  instance_class      = var.db_replica_instance_class

  # Network Configuration
  vpc_security_group_ids = [aws_security_group.jorge_bi_rds.id]
  publicly_accessible    = false

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
  performance_insights_enabled = true

  tags = {
    Name = "Jorge BI Read Replica"
  }
}

# ==============================================================================
# ELASTICACHE - REDIS CLUSTER
# ==============================================================================

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "jorge_bi" {
  name       = "jorge-bi-cache-subnet"
  subnet_ids = var.cache_subnet_ids

  tags = {
    Name = "Jorge BI Cache Subnet Group"
  }
}

# Security Group for ElastiCache
resource "aws_security_group" "jorge_bi_redis" {
  name        = "jorge-bi-redis-sg"
  description = "Security group for Jorge BI Redis cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.jorge_bi_app.id]
    description     = "Redis access from application"
  }

  tags = {
    Name = "Jorge BI Redis Security Group"
  }
}

# ElastiCache Replication Group
resource "aws_elasticache_replication_group" "jorge_bi" {
  replication_group_id       = "jorge-bi-redis"
  description                = "Jorge BI Redis cluster for production workloads"

  # Engine Configuration
  engine               = "redis"
  engine_version       = "7.0"
  node_type           = var.redis_node_type
  port                = 6379
  parameter_group_name = "default.redis7"

  # Cluster Configuration
  num_cache_clusters         = var.redis_num_nodes
  automatic_failover_enabled = true
  multi_az_enabled          = true

  # Network Configuration
  subnet_group_name  = aws_elasticache_subnet_group.jorge_bi.name
  security_group_ids = [aws_security_group.jorge_bi_redis.id]

  # Security
  auth_token                 = var.redis_auth_token
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  kms_key_id                = aws_kms_key.jorge_bi.arn

  # Backup Configuration
  snapshot_retention_limit = 7
  snapshot_window         = "03:30-05:30"
  maintenance_window      = "sun:05:30-sun:06:30"

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  tags = {
    Name = "Jorge BI Redis Cluster"
  }
}

# ==============================================================================
# APPLICATION LOAD BALANCER
# ==============================================================================

# Security Group for ALB
resource "aws_security_group" "jorge_bi_alb" {
  name        = "jorge-bi-alb-sg"
  description = "Security group for Jorge BI Application Load Balancer"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "Jorge BI ALB Security Group"
  }
}

# Application Load Balancer
resource "aws_lb" "jorge_bi" {
  name               = "jorge-bi-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.jorge_bi_alb.id]
  subnets           = var.public_subnet_ids

  enable_deletion_protection = true
  enable_http2              = true

  access_logs {
    bucket  = aws_s3_bucket.jorge_bi_logs.bucket
    prefix  = "alb"
    enabled = true
  }

  tags = {
    Name = "Jorge BI Application Load Balancer"
  }
}

# ==============================================================================
# S3 BUCKETS
# ==============================================================================

# S3 Bucket for Logs
resource "aws_s3_bucket" "jorge_bi_logs" {
  bucket = "jorge-bi-logs-${random_string.bucket_suffix.result}"

  tags = {
    Name = "Jorge BI Logs Bucket"
  }
}

resource "aws_s3_bucket_versioning" "jorge_bi_logs" {
  bucket = aws_s3_bucket.jorge_bi_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "jorge_bi_logs" {
  bucket = aws_s3_bucket.jorge_bi_logs.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.jorge_bi.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "jorge_bi_logs" {
  bucket = aws_s3_bucket.jorge_bi_logs.id

  rule {
    id     = "log_lifecycle"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket for Backups
resource "aws_s3_bucket" "jorge_bi_backups" {
  bucket = "jorge-bi-backups-${random_string.bucket_suffix.result}"

  tags = {
    Name = "Jorge BI Backups Bucket"
  }
}

resource "aws_s3_bucket_versioning" "jorge_bi_backups" {
  bucket = aws_s3_bucket.jorge_bi_backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "jorge_bi_backups" {
  bucket = aws_s3_bucket.jorge_bi_backups.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.jorge_bi.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

# ==============================================================================
# KMS ENCRYPTION
# ==============================================================================

# KMS Key for Jorge BI
resource "aws_kms_key" "jorge_bi" {
  description             = "KMS key for Jorge BI Dashboard encryption"
  deletion_window_in_days = 7

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "Jorge BI KMS Key"
  }
}

resource "aws_kms_alias" "jorge_bi" {
  name          = "alias/jorge-bi-dashboard"
  target_key_id = aws_kms_key.jorge_bi.key_id
}

# ==============================================================================
# SECURITY GROUPS
# ==============================================================================

# Security Group for Application
resource "aws_security_group" "jorge_bi_app" {
  name        = "jorge-bi-app-sg"
  description = "Security group for Jorge BI application pods"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.jorge_bi_alb.id]
    description     = "HTTP access from ALB"
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Internal cluster access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "Jorge BI Application Security Group"
  }
}

# ==============================================================================
# IAM ROLES AND POLICIES
# ==============================================================================

# RDS Monitoring Role
resource "aws_iam_role" "rds_monitoring" {
  name = "jorge-bi-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Jorge BI RDS Monitoring Role"
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Application Service Account Role
resource "aws_iam_role" "jorge_bi_app" {
  name = "jorge-bi-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Condition = {
          StringEquals = {
            "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:${var.kubernetes_namespace}:jorge-bi-service-account"
          }
        }
      }
    ]
  })

  tags = {
    Name = "Jorge BI Application Role"
  }
}

# S3 Access Policy for the Application
resource "aws_iam_policy" "jorge_bi_s3_access" {
  name        = "jorge-bi-s3-access"
  description = "S3 access policy for Jorge BI application"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.jorge_bi_backups.arn}/*",
          "${aws_s3_bucket.jorge_bi_logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.jorge_bi_backups.arn,
          aws_s3_bucket.jorge_bi_logs.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "jorge_bi_s3_access" {
  role       = aws_iam_role.jorge_bi_app.name
  policy_arn = aws_iam_policy.jorge_bi_s3_access.arn
}

# ==============================================================================
# CLOUDWATCH LOG GROUPS
# ==============================================================================

resource "aws_cloudwatch_log_group" "jorge_bi_app" {
  name              = "/aws/eks/jorge-bi/application"
  retention_in_days = 30

  tags = {
    Name = "Jorge BI Application Logs"
  }
}

resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/jorge-bi/redis-slow"
  retention_in_days = 14

  tags = {
    Name = "Jorge BI Redis Slow Logs"
  }
}

# ==============================================================================
# RANDOM GENERATORS
# ==============================================================================

resource "random_string" "bucket_suffix" {
  length  = 8
  upper   = false
  special = false
}

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.jorge_bi.endpoint
  sensitive   = true
}

output "database_read_replica_endpoint" {
  description = "RDS read replica endpoint"
  value       = aws_db_instance.jorge_bi_read_replica.endpoint
  sensitive   = true
}

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.jorge_bi.primary_endpoint_address
  sensitive   = true
}

output "load_balancer_dns" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.jorge_bi.dns_name
}

output "s3_logs_bucket" {
  description = "S3 bucket for logs"
  value       = aws_s3_bucket.jorge_bi_logs.bucket
}

output "s3_backups_bucket" {
  description = "S3 bucket for backups"
  value       = aws_s3_bucket.jorge_bi_backups.bucket
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.jorge_bi.arn
}

output "app_security_group_id" {
  description = "Security group ID for the application"
  value       = aws_security_group.jorge_bi_app.id
}

output "iam_role_arn" {
  description = "IAM role ARN for the application"
  value       = aws_iam_role.jorge_bi_app.arn
}