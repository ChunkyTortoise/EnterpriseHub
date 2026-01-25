# IAM Role and Policies for Ultra-Fast ML Engine
# Provides access to S3 model storage and ElastiCache Redis

# IAM Role for ML Engine Service Account
resource "aws_iam_role" "jorge_platform_ml_role" {
  name = "jorge-platform-ml-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.jorge_platform.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.jorge_platform.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:jorge-platform:jorge-platform-ml-service-account"
            "${replace(aws_eks_cluster.jorge_platform.identity[0].oidc[0].issuer, "https://", "")}:aud": "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name = "jorge-platform-ml-role"
    Component = "ml-engine"
  }
}

# Policy for S3 Model Storage Access
resource "aws_iam_policy" "ml_model_storage_policy" {
  name = "jorge-platform-ml-model-storage-policy"
  description = "Policy for ML engine to access model storage in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::jorge-platform-ml-models",
          "arn:aws:s3:::jorge-platform-ml-models/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "arn:aws:s3:::jorge-platform-ml-models/cache/*",
          "arn:aws:s3:::jorge-platform-ml-models/metrics/*"
        ]
      }
    ]
  })
}

# Policy for ElastiCache Redis Access
resource "aws_iam_policy" "redis_access_policy" {
  name = "jorge-platform-redis-access-policy"
  description = "Policy for ML engine to access ElastiCache Redis cluster"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticache:Describe*",
          "elasticache:List*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for CloudWatch Metrics
resource "aws_iam_policy" "cloudwatch_metrics_policy" {
  name = "jorge-platform-ml-cloudwatch-policy"
  description = "Policy for ML engine to publish CloudWatch metrics"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace": [
              "Jorge/MLEngine",
              "Jorge/Performance",
              "Jorge/Business"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/jorge-platform/ml-engine"
      }
    ]
  })
}

# Attach policies to the ML engine role
resource "aws_iam_role_policy_attachment" "ml_model_storage_attach" {
  role       = aws_iam_role.jorge_platform_ml_role.name
  policy_arn = aws_iam_policy.ml_model_storage_policy.arn
}

resource "aws_iam_role_policy_attachment" "redis_access_attach" {
  role       = aws_iam_role.jorge_platform_ml_role.name
  policy_arn = aws_iam_policy.redis_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "cloudwatch_metrics_attach" {
  role       = aws_iam_role.jorge_platform_ml_role.name
  policy_arn = aws_iam_policy.cloudwatch_metrics_policy.arn
}

# S3 Bucket for ML Models (if not already exists)
resource "aws_s3_bucket" "ml_models" {
  bucket = "jorge-platform-ml-models-${random_string.bucket_suffix.result}"

  tags = {
    Name = "jorge-platform-ml-models"
    Component = "ml-engine"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "ml_models_versioning" {
  bucket = aws_s3_bucket.ml_models.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "ml_models_encryption" {
  bucket = aws_s3_bucket.ml_models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "ml_models_pab" {
  bucket = aws_s3_bucket.ml_models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ElastiCache Redis Cluster for ML Engine Cache
resource "aws_elasticache_replication_group" "jorge_ml_cache" {
  replication_group_id         = "jorge-ml-cache"
  description                  = "Redis cluster for ML engine caching"

  node_type                    = "cache.r6g.large"
  port                         = 6379
  parameter_group_name         = aws_elasticache_parameter_group.jorge_ml_redis_params.name

  num_cache_clusters           = 3
  automatic_failover_enabled   = true
  multi_az_enabled            = true

  subnet_group_name           = aws_elasticache_subnet_group.jorge_ml_cache.name
  security_group_ids          = [aws_security_group.redis_ml_cache.id]

  at_rest_encryption_enabled  = true
  transit_encryption_enabled  = true
  auth_token                  = var.redis_auth_token

  # Maintenance and backup
  maintenance_window          = "sun:03:00-sun:04:00"
  snapshot_retention_limit    = 7
  snapshot_window            = "02:00-03:00"

  # Performance optimization for ML workloads
  data_tiering_enabled       = false  # Keep all data in memory for speed

  tags = {
    Name = "jorge-ml-cache"
    Component = "ml-engine"
    Environment = var.environment
  }
}

# Redis Parameter Group for ML Optimization
resource "aws_elasticache_parameter_group" "jorge_ml_redis_params" {
  family = "redis7"
  name   = "jorge-ml-redis-params"

  # Optimize for ML workload patterns
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"  # Evict least recently used keys
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = {
    Name = "jorge-ml-redis-params"
    Component = "ml-engine"
  }
}

# Subnet Group for Redis Cluster
resource "aws_elasticache_subnet_group" "jorge_ml_cache" {
  name       = "jorge-ml-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "jorge-ml-cache-subnet-group"
    Component = "ml-engine"
  }
}

# Security Group for Redis Cluster
resource "aws_security_group" "redis_ml_cache" {
  name_prefix = "jorge-ml-redis-sg"
  vpc_id      = aws_vpc.jorge_platform.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.jorge_platform_nodes.id]
    description     = "Redis access from EKS nodes"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "jorge-ml-redis-sg"
    Component = "ml-engine"
  }
}

# CloudWatch Log Group for ML Engine
resource "aws_cloudwatch_log_group" "ml_engine_logs" {
  name              = "/aws/jorge-platform/ml-engine"
  retention_in_days = 30

  tags = {
    Name = "jorge-ml-engine-logs"
    Component = "ml-engine"
    Environment = var.environment
  }
}

# Outputs
output "ml_engine_role_arn" {
  value = aws_iam_role.jorge_platform_ml_role.arn
  description = "ARN of the ML engine IAM role"
}

output "redis_cluster_endpoint" {
  value = aws_elasticache_replication_group.jorge_ml_cache.primary_endpoint_address
  description = "Redis cluster primary endpoint"
}

output "s3_model_bucket" {
  value = aws_s3_bucket.ml_models.bucket
  description = "S3 bucket name for ML models"
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.ml_engine_logs.name
  description = "CloudWatch log group for ML engine"
}