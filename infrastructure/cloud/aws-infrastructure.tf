# Jorge's Real Estate AI Platform - AWS Cloud Infrastructure
# Terraform configuration for production-grade deployment with 99.99% uptime SLA
# Version: 2.0.0

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
    bucket = "jorge-platform-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "Jorge Real Estate AI"
      Environment = var.environment
      Owner       = "Jorge Platform Team"
      CostCenter  = "Revenue Platform"
      Terraform   = "true"
    }
  }
}

# ================================================================
# VARIABLES
# ================================================================
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Primary domain for the application"
  type        = string
  default     = "jorge-platform.com"
}

variable "api_domain_name" {
  description = "API subdomain"
  type        = string
  default     = "api.jorge-platform.com"
}

variable "eks_cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

variable "node_instance_type" {
  description = "EC2 instance type for EKS worker nodes"
  type        = string
  default     = "t3.large"
}

variable "min_nodes" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 3
}

variable "max_nodes" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 20
}

variable "desired_nodes" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 6
}

# ================================================================
# DATA SOURCES
# ================================================================
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# ================================================================
# VPC AND NETWORKING
# ================================================================
resource "aws_vpc" "jorge_platform" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                                        = "jorge-platform-vpc"
    "kubernetes.io/cluster/jorge-platform-eks" = "shared"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "jorge_platform" {
  vpc_id = aws_vpc.jorge_platform.id

  tags = {
    Name = "jorge-platform-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 3

  vpc_id                  = aws_vpc.jorge_platform.id
  cidr_block              = "10.0.${1 + count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                        = "jorge-platform-public-subnet-${count.index + 1}"
    "kubernetes.io/cluster/jorge-platform-eks" = "shared"
    "kubernetes.io/role/elb"                   = "1"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 3

  vpc_id            = aws_vpc.jorge_platform.id
  cidr_block        = "10.0.${10 + count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                                        = "jorge-platform-private-subnet-${count.index + 1}"
    "kubernetes.io/cluster/jorge-platform-eks" = "owned"
    "kubernetes.io/role/internal-elb"          = "1"
  }
}

# Database Subnets
resource "aws_subnet" "database" {
  count = 3

  vpc_id            = aws_vpc.jorge_platform.id
  cidr_block        = "10.0.${20 + count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "jorge-platform-database-subnet-${count.index + 1}"
  }
}

# NAT Gateways
resource "aws_eip" "nat" {
  count  = 3
  domain = "vpc"

  depends_on = [aws_internet_gateway.jorge_platform]

  tags = {
    Name = "jorge-platform-nat-eip-${count.index + 1}"
  }
}

resource "aws_nat_gateway" "jorge_platform" {
  count = 3

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  depends_on = [aws_internet_gateway.jorge_platform]

  tags = {
    Name = "jorge-platform-nat-gw-${count.index + 1}"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.jorge_platform.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.jorge_platform.id
  }

  tags = {
    Name = "jorge-platform-public-rt"
  }
}

resource "aws_route_table" "private" {
  count  = 3
  vpc_id = aws_vpc.jorge_platform.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.jorge_platform[count.index].id
  }

  tags = {
    Name = "jorge-platform-private-rt-${count.index + 1}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = 3

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 3

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# ================================================================
# SECURITY GROUPS
# ================================================================
resource "aws_security_group" "eks_cluster" {
  name_prefix = "jorge-platform-eks-cluster"
  vpc_id      = aws_vpc.jorge_platform.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jorge-platform-eks-cluster-sg"
  }
}

resource "aws_security_group" "eks_worker_nodes" {
  name_prefix = "jorge-platform-eks-workers"
  vpc_id      = aws_vpc.jorge_platform.id

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  ingress {
    from_port       = 1025
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name                                        = "jorge-platform-eks-workers-sg"
    "kubernetes.io/cluster/jorge-platform-eks" = "owned"
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "jorge-platform-alb"
  vpc_id      = aws_vpc.jorge_platform.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jorge-platform-alb-sg"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "jorge-platform-rds"
  vpc_id      = aws_vpc.jorge_platform.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_worker_nodes.id]
  }

  tags = {
    Name = "jorge-platform-rds-sg"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "jorge-platform-redis"
  vpc_id      = aws_vpc.jorge_platform.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_worker_nodes.id]
  }

  tags = {
    Name = "jorge-platform-redis-sg"
  }
}

# ================================================================
# EKS CLUSTER
# ================================================================
resource "aws_iam_role" "eks_cluster" {
  name = "jorge-platform-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_eks_cluster" "jorge_platform" {
  name     = "jorge-platform-eks"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.eks_cluster_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    security_group_ids      = [aws_security_group.eks_cluster.id]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_AmazonEKSClusterPolicy,
  ]

  tags = {
    Name = "jorge-platform-eks"
  }
}

# ================================================================
# EKS NODE GROUPS
# ================================================================
resource "aws_iam_role" "eks_worker_nodes" {
  name = "jorge-platform-eks-worker-nodes-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_nodes_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_worker_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_worker_nodes_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_worker_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_worker_nodes_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_worker_nodes.name
}

resource "aws_eks_node_group" "jorge_platform" {
  cluster_name    = aws_eks_cluster.jorge_platform.name
  node_group_name = "jorge-platform-nodes"
  node_role_arn   = aws_iam_role.eks_worker_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = [var.node_instance_type]
  ami_type       = "AL2_x86_64"
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = var.desired_nodes
    max_size     = var.max_nodes
    min_size     = var.min_nodes
  }

  update_config {
    max_unavailable_percentage = 25
  }

  remote_access {
    ec2_ssh_key = aws_key_pair.jorge_platform.key_name
    source_security_group_ids = [aws_security_group.eks_worker_nodes.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_nodes_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.eks_worker_nodes_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.eks_worker_nodes_AmazonEC2ContainerRegistryReadOnly,
  ]

  tags = {
    Name = "jorge-platform-eks-nodes"
  }
}

# ================================================================
# KEY PAIR FOR SSH ACCESS
# ================================================================
resource "aws_key_pair" "jorge_platform" {
  key_name   = "jorge-platform-key"
  public_key = file("~/.ssh/id_rsa.pub") # Update with your public key path

  tags = {
    Name = "jorge-platform-key"
  }
}

# ================================================================
# RDS DATABASE (PostgreSQL)
# ================================================================
resource "aws_db_subnet_group" "jorge_platform" {
  name       = "jorge-platform-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = {
    Name = "jorge-platform-db-subnet-group"
  }
}

resource "aws_rds_cluster" "jorge_platform" {
  cluster_identifier              = "jorge-platform-postgres"
  engine                         = "aurora-postgresql"
  engine_version                 = "14.9"
  database_name                  = "jorge_platform_prod"
  master_username                = "jorge"
  master_password                = random_password.db_password.result
  backup_retention_period        = 30
  preferred_backup_window        = "03:00-04:00"
  preferred_maintenance_window   = "sun:04:00-sun:05:00"
  db_subnet_group_name           = aws_db_subnet_group.jorge_platform.name
  vpc_security_group_ids         = [aws_security_group.rds.id]
  storage_encrypted              = true
  apply_immediately              = false
  final_snapshot_identifier      = "jorge-platform-final-snapshot-${formatdate("YYYY-MM-DD-hhmmss", timestamp())}"
  skip_final_snapshot            = false
  deletion_protection           = true

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "jorge-platform-postgres"
  }
}

resource "aws_rds_cluster_instance" "jorge_platform" {
  count              = 2
  identifier         = "jorge-platform-postgres-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.jorge_platform.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.jorge_platform.engine
  engine_version     = aws_rds_cluster.jorge_platform.engine_version

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn

  tags = {
    Name = "jorge-platform-postgres-instance-${count.index + 1}"
  }
}

# ================================================================
# REDIS CLUSTER (ElastiCache)
# ================================================================
resource "aws_elasticache_subnet_group" "jorge_platform" {
  name       = "jorge-platform-cache-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "jorge-platform-cache-subnet-group"
  }
}

resource "aws_elasticache_replication_group" "jorge_platform" {
  description          = "Jorge Platform Redis Cluster"
  replication_group_id = "jorge-platform-redis"
  port                 = 6379

  node_type            = "cache.t3.medium"
  num_cache_clusters   = 3
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"

  subnet_group_name  = aws_elasticache_subnet_group.jorge_platform.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_password.result

  maintenance_window         = "sun:03:00-sun:04:00"
  snapshot_retention_limit   = 5
  snapshot_window           = "02:00-03:00"
  automatic_failover_enabled = true
  multi_az_enabled          = true

  tags = {
    Name = "jorge-platform-redis"
  }
}

# ================================================================
# RANDOM PASSWORDS
# ================================================================
resource "random_password" "db_password" {
  length  = 16
  special = true
}

resource "random_password" "redis_password" {
  length  = 32
  special = false
}

# ================================================================
# SECRETS MANAGER
# ================================================================
resource "aws_secretsmanager_secret" "db_credentials" {
  name_prefix             = "jorge-platform-db-credentials"
  description             = "Database credentials for Jorge Platform"
  recovery_window_in_days = 7

  tags = {
    Name = "jorge-platform-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_rds_cluster.jorge_platform.master_username
    password = aws_rds_cluster.jorge_platform.master_password
    endpoint = aws_rds_cluster.jorge_platform.endpoint
    port     = aws_rds_cluster.jorge_platform.port
    dbname   = aws_rds_cluster.jorge_platform.database_name
  })
}

resource "aws_secretsmanager_secret" "redis_credentials" {
  name_prefix             = "jorge-platform-redis-credentials"
  description             = "Redis credentials for Jorge Platform"
  recovery_window_in_days = 7

  tags = {
    Name = "jorge-platform-redis-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id
  secret_string = jsonencode({
    endpoint = aws_elasticache_replication_group.jorge_platform.configuration_endpoint_address
    port     = aws_elasticache_replication_group.jorge_platform.port
    auth_token = aws_elasticache_replication_group.jorge_platform.auth_token
  })
}

# ================================================================
# IAM ROLE FOR RDS ENHANCED MONITORING
# ================================================================
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name_prefix = "rds-monitoring-role"

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
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ================================================================
# APPLICATION LOAD BALANCER
# ================================================================
resource "aws_lb" "jorge_platform" {
  name               = "jorge-platform-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2              = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-access-logs"
    enabled = true
  }

  tags = {
    Name = "jorge-platform-alb"
  }
}

# ================================================================
# S3 BUCKETS
# ================================================================
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "jorge-platform-alb-logs-${random_string.bucket_suffix.result}"
  force_destroy = false

  tags = {
    Name = "jorge-platform-alb-logs"
  }
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "application_storage" {
  bucket        = "jorge-platform-storage-${random_string.bucket_suffix.result}"
  force_destroy = false

  tags = {
    Name = "jorge-platform-application-storage"
  }
}

resource "aws_s3_bucket_versioning" "application_storage" {
  bucket = aws_s3_bucket.application_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "application_storage" {
  bucket = aws_s3_bucket.application_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ================================================================
# ROUTE 53 DNS
# ================================================================
data "aws_route53_zone" "jorge_platform" {
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.jorge_platform.zone_id
  name    = var.api_domain_name
  type    = "A"

  alias {
    name                   = aws_lb.jorge_platform.dns_name
    zone_id                = aws_lb.jorge_platform.zone_id
    evaluate_target_health = true
  }
}

# ================================================================
# SSL CERTIFICATE
# ================================================================
resource "aws_acm_certificate" "jorge_platform" {
  domain_name               = var.api_domain_name
  subject_alternative_names = [var.domain_name, "*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "jorge-platform-certificate"
  }
}

resource "aws_route53_record" "certificate_validation" {
  for_each = {
    for dvo in aws_acm_certificate.jorge_platform.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.jorge_platform.zone_id
}

resource "aws_acm_certificate_validation" "jorge_platform" {
  certificate_arn         = aws_acm_certificate.jorge_platform.arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation : record.fqdn]
}

# ================================================================
# CLOUDWATCH LOG GROUPS
# ================================================================
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/jorge-platform-eks/cluster"
  retention_in_days = 30

  tags = {
    Name = "jorge-platform-eks-logs"
  }
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/jorge-platform/application"
  retention_in_days = 30

  tags = {
    Name = "jorge-platform-application-logs"
  }
}

# ================================================================
# OUTPUTS
# ================================================================
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.jorge_platform.id
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.jorge_platform.name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.jorge_platform.endpoint
}

output "rds_cluster_endpoint" {
  description = "RDS cluster endpoint"
  value       = aws_rds_cluster.jorge_platform.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.jorge_platform.configuration_endpoint_address
  sensitive   = true
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.jorge_platform.dns_name
}

output "api_url" {
  description = "API URL"
  value       = "https://${var.api_domain_name}"
}

output "s3_application_bucket" {
  description = "S3 bucket for application storage"
  value       = aws_s3_bucket.application_storage.bucket
}

output "db_secret_arn" {
  description = "Database credentials secret ARN"
  value       = aws_secretsmanager_secret.db_credentials.arn
  sensitive   = true
}

output "redis_secret_arn" {
  description = "Redis credentials secret ARN"
  value       = aws_secretsmanager_secret.redis_credentials.arn
  sensitive   = true
}