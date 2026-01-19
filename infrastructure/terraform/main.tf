# Jorge's Revenue Acceleration Platform - Infrastructure as Code
# Terraform configuration for cloud infrastructure provisioning
# Version: 1.0.0
# Provider: AWS (adaptable to GCP, Azure)

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    bucket         = "jorge-revenue-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "jorge-revenue-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Jorge-Revenue-Platform"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Jorge-Salas"
    }
  }
}

# ============================================
# VPC and Networking
# ============================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "jorge-revenue-vpc-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "staging"
  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Flow Logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  tags = {
    Name = "jorge-revenue-vpc-${var.environment}"
  }
}

# ============================================
# EKS Cluster
# ============================================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "jorge-revenue-${var.environment}"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster endpoint access
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Enable cluster logging
  cluster_enabled_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  # Managed node groups
  eks_managed_node_groups = {
    general = {
      name           = "general-${var.environment}"
      instance_types = ["t3.large"]

      min_size     = 3
      max_size     = 20
      desired_size = 3

      disk_size = 50

      labels = {
        role        = "general"
        environment = var.environment
      }

      tags = {
        NodeGroup = "general"
      }
    }

    compute = {
      name           = "compute-${var.environment}"
      instance_types = ["c5.2xlarge"]

      min_size     = 2
      max_size     = 10
      desired_size = 2

      disk_size = 100

      labels = {
        role        = "compute"
        environment = var.environment
      }

      taints = [{
        key    = "compute-intensive"
        value  = "true"
        effect = "NoSchedule"
      }]

      tags = {
        NodeGroup = "compute"
      }
    }
  }

  # Cluster security group rules
  cluster_security_group_additional_rules = {
    ingress_nodes_ephemeral_ports_tcp = {
      description                = "Nodes on ephemeral ports"
      protocol                   = "tcp"
      from_port                  = 1025
      to_port                    = 65535
      type                       = "ingress"
      source_node_security_group = true
    }
  }

  # Node security group rules
  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }
  }

  tags = {
    Cluster = "jorge-revenue-${var.environment}"
  }
}

# ============================================
# RDS PostgreSQL Database
# ============================================
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "jorge-revenue-${var.environment}"

  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true

  db_name  = "jorge_revenue"
  username = "jorge_admin"
  port     = 5432

  # Multi-AZ for production high availability
  multi_az = var.environment == "production"

  # Database subnet group
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Backup configuration
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Enhanced monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  create_cloudwatch_log_group     = true
  monitoring_interval             = 60
  monitoring_role_name            = "jorge-revenue-rds-monitoring-${var.environment}"
  create_monitoring_role          = true

  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Deletion protection for production
  deletion_protection = var.environment == "production"

  tags = {
    Name = "jorge-revenue-db-${var.environment}"
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "jorge-revenue-rds-${var.environment}-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "PostgreSQL from EKS"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jorge-revenue-rds-sg-${var.environment}"
  }
}

# ============================================
# ElastiCache Redis
# ============================================
resource "aws_elasticache_subnet_group" "redis" {
  name       = "jorge-revenue-redis-${var.environment}"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "jorge-revenue-redis-subnet-${var.environment}"
  }
}

resource "aws_elasticache_parameter_group" "redis" {
  name   = "jorge-revenue-redis-params-${var.environment}"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "jorge-revenue-${var.environment}"
  replication_group_description = "Redis cluster for Jorge Revenue Platform"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.redis_node_type
  num_cache_clusters   = var.environment == "production" ? 3 : 2
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]
  parameter_group_name = aws_elasticache_parameter_group.redis.name

  # Automatic failover for high availability
  automatic_failover_enabled = true
  multi_az_enabled          = var.environment == "production"

  # Backup configuration
  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_enabled        = true

  tags = {
    Name = "jorge-revenue-redis-${var.environment}"
  }
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name_prefix = "jorge-revenue-redis-${var.environment}-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Redis from EKS"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jorge-revenue-redis-sg-${var.environment}"
  }
}

# ============================================
# S3 Buckets
# ============================================
# Analytics data bucket
resource "aws_s3_bucket" "analytics" {
  bucket = "jorge-revenue-analytics-${var.environment}-${var.aws_account_id}"

  tags = {
    Name = "jorge-revenue-analytics-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# Backup bucket
resource "aws_s3_bucket" "backups" {
  bucket = "jorge-revenue-backups-${var.environment}-${var.aws_account_id}"

  tags = {
    Name = "jorge-revenue-backups-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================
# CloudWatch Log Groups
# ============================================
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/jorge-revenue/${var.environment}/application"
  retention_in_days = var.environment == "production" ? 90 : 30

  tags = {
    Name = "jorge-revenue-app-logs-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "business_metrics" {
  name              = "/aws/jorge-revenue/${var.environment}/business-metrics"
  retention_in_days = var.environment == "production" ? 365 : 90

  tags = {
    Name = "jorge-revenue-business-logs-${var.environment}"
  }
}

# ============================================
# Secrets Manager
# ============================================
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "jorge-revenue/${var.environment}/app-secrets"
  description = "Application secrets for Jorge Revenue Platform"

  tags = {
    Name = "jorge-revenue-secrets-${var.environment}"
  }
}

# ============================================
# CloudWatch Alarms
# ============================================
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "jorge-revenue-${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorRate"
  namespace           = "Jorge/RevenueAPI"
  period              = "300"
  statistic           = "Average"
  threshold           = "0.01"
  alarm_description   = "Alert when error rate exceeds 1%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Name = "high-error-rate-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_response_time" {
  alarm_name          = "jorge-revenue-${var.environment}-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ResponseTime"
  namespace           = "Jorge/RevenueAPI"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000"
  alarm_description   = "Alert when response time exceeds 1 second"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Name = "high-response-time-${var.environment}"
  }
}

# ============================================
# SNS Topics for Alerts
# ============================================
resource "aws_sns_topic" "alerts" {
  name = "jorge-revenue-alerts-${var.environment}"

  tags = {
    Name = "jorge-revenue-alerts-${var.environment}"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================
# WAF for API Protection
# ============================================
resource "aws_wafv2_web_acl" "api_protection" {
  name  = "jorge-revenue-api-protection-${var.environment}"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "jorge-revenue-api-waf-${var.environment}"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "jorge-revenue-waf-${var.environment}"
  }
}

# ============================================
# Outputs
# ============================================
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "analytics_bucket" {
  description = "S3 analytics bucket name"
  value       = aws_s3_bucket.analytics.id
}

output "backups_bucket" {
  description = "S3 backups bucket name"
  value       = aws_s3_bucket.backups.id
}
