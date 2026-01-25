# ==============================================================================
# JORGE'S BI DASHBOARD - TERRAFORM VARIABLES
# Production infrastructure configuration variables
# ==============================================================================

# ==============================================================================
# GENERAL CONFIGURATION
# ==============================================================================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "jorge-bi-dashboard"
}

# ==============================================================================
# NETWORK CONFIGURATION
# ==============================================================================

variable "vpc_id" {
  description = "ID of the VPC where resources will be created"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancer"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for application"
  type        = list(string)
}

variable "database_subnet_ids" {
  description = "List of database subnet IDs for RDS"
  type        = list(string)
}

variable "cache_subnet_ids" {
  description = "List of cache subnet IDs for ElastiCache"
  type        = list(string)
}

# ==============================================================================
# EKS CONFIGURATION
# ==============================================================================

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "jorge-production-eks"
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "jorge-bi-production"
}

# ==============================================================================
# DATABASE CONFIGURATION (RDS PostgreSQL)
# ==============================================================================

variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL database"
  type        = string
  default     = "db.r6g.xlarge"

  validation {
    condition = contains([
      "db.r6g.large", "db.r6g.xlarge", "db.r6g.2xlarge", "db.r6g.4xlarge",
      "db.m6g.large", "db.m6g.xlarge", "db.m6g.2xlarge", "db.m6g.4xlarge"
    ], var.db_instance_class)
    error_message = "Database instance class must be a supported type for production workloads."
  }
}

variable "db_replica_instance_class" {
  description = "RDS instance class for read replica"
  type        = string
  default     = "db.r6g.large"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS instance (GB)"
  type        = number
  default     = 100

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 10000
    error_message = "Database allocated storage must be between 20 and 10000 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 1000

  validation {
    condition     = var.db_max_allocated_storage >= var.db_allocated_storage
    error_message = "Maximum allocated storage must be greater than or equal to allocated storage."
  }
}

variable "db_username" {
  description = "Username for the RDS instance"
  type        = string
  default     = "jorge_bi_admin"
}

variable "db_password" {
  description = "Password for the RDS instance"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

# ==============================================================================
# CACHE CONFIGURATION (ElastiCache Redis)
# ==============================================================================

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"

  validation {
    condition = contains([
      "cache.r6g.large", "cache.r6g.xlarge", "cache.r6g.2xlarge", "cache.r6g.4xlarge",
      "cache.m6g.large", "cache.m6g.xlarge", "cache.m6g.2xlarge", "cache.m6g.4xlarge"
    ], var.redis_node_type)
    error_message = "Redis node type must be a supported type for production workloads."
  }
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes in the cluster"
  type        = number
  default     = 3

  validation {
    condition     = var.redis_num_nodes >= 2 && var.redis_num_nodes <= 6
    error_message = "Redis cluster must have between 2 and 6 nodes."
  }
}

variable "redis_auth_token" {
  description = "Auth token for Redis cluster"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.redis_auth_token) >= 32
    error_message = "Redis auth token must be at least 32 characters long."
  }
}

# ==============================================================================
# LOAD BALANCER CONFIGURATION
# ==============================================================================

variable "certificate_arn" {
  description = "ARN of the SSL certificate for the load balancer"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "bi.jorge-platform.com"
}

variable "alternative_domain_names" {
  description = "Alternative domain names for the application"
  type        = list(string)
  default     = ["dashboard.jorge-platform.com"]
}

# ==============================================================================
# MONITORING CONFIGURATION
# ==============================================================================

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for RDS"
  type        = bool
  default     = true
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = true
}

variable "cloudwatch_log_retention" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.cloudwatch_log_retention)
    error_message = "CloudWatch log retention must be a valid retention period."
  }
}

# ==============================================================================
# BACKUP CONFIGURATION
# ==============================================================================

variable "backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_period >= 7 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 7 and 35 days."
  }
}

variable "backup_window" {
  description = "RDS backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "RDS maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# ==============================================================================
# SECURITY CONFIGURATION
# ==============================================================================

variable "enable_deletion_protection" {
  description = "Enable deletion protection for RDS instances"
  type        = bool
  default     = true
}

variable "storage_encrypted" {
  description = "Enable storage encryption for RDS"
  type        = bool
  default     = true
}

variable "enable_transit_encryption" {
  description = "Enable transit encryption for ElastiCache"
  type        = bool
  default     = true
}

variable "enable_at_rest_encryption" {
  description = "Enable at-rest encryption for ElastiCache"
  type        = bool
  default     = true
}

# ==============================================================================
# SCALING CONFIGURATION
# ==============================================================================

variable "app_min_replicas" {
  description = "Minimum number of application replicas"
  type        = number
  default     = 2

  validation {
    condition     = var.app_min_replicas >= 1 && var.app_min_replicas <= 10
    error_message = "Minimum replicas must be between 1 and 10."
  }
}

variable "app_max_replicas" {
  description = "Maximum number of application replicas"
  type        = number
  default     = 10

  validation {
    condition     = var.app_max_replicas >= var.app_min_replicas && var.app_max_replicas <= 50
    error_message = "Maximum replicas must be greater than minimum replicas and less than 50."
  }
}

variable "app_target_cpu_utilization" {
  description = "Target CPU utilization for horizontal pod autoscaler"
  type        = number
  default     = 70

  validation {
    condition     = var.app_target_cpu_utilization >= 50 && var.app_target_cpu_utilization <= 90
    error_message = "Target CPU utilization must be between 50 and 90 percent."
  }
}

# ==============================================================================
# JORGE-SPECIFIC CONFIGURATION
# ==============================================================================

variable "jorge_commission_rate" {
  description = "Jorge's commission rate (as decimal)"
  type        = number
  default     = 0.06

  validation {
    condition     = var.jorge_commission_rate > 0 && var.jorge_commission_rate <= 1
    error_message = "Commission rate must be between 0 and 1."
  }
}

variable "jorge_monthly_target" {
  description = "Jorge's monthly commission target in dollars"
  type        = number
  default     = 25000

  validation {
    condition     = var.jorge_monthly_target > 0
    error_message = "Monthly target must be greater than 0."
  }
}

variable "enable_jorge_features" {
  description = "Enable Jorge-specific business intelligence features"
  type        = bool
  default     = true
}

# ==============================================================================
# COST OPTIMIZATION
# ==============================================================================

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling for non-business hours"
  type        = bool
  default     = true
}

variable "business_hours_start" {
  description = "Business hours start time (UTC)"
  type        = string
  default     = "13:00"  # 8 AM Central Time
}

variable "business_hours_end" {
  description = "Business hours end time (UTC)"
  type        = string
  default     = "02:00"  # 9 PM Central Time
}

variable "weekend_min_replicas" {
  description = "Minimum replicas during weekends"
  type        = number
  default     = 1
}

# ==============================================================================
# DISASTER RECOVERY
# ==============================================================================

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

variable "enable_cross_region_backups" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = false
}

variable "dr_region" {
  description = "Disaster recovery region"
  type        = string
  default     = "us-west-2"
}

# ==============================================================================
# COMPLIANCE CONFIGURATION
# ==============================================================================

variable "enable_audit_logging" {
  description = "Enable audit logging for compliance"
  type        = bool
  default     = true
}

variable "data_retention_days" {
  description = "Data retention period for compliance"
  type        = number
  default     = 2555  # 7 years

  validation {
    condition     = var.data_retention_days >= 365
    error_message = "Data retention must be at least 365 days for compliance."
  }
}

variable "enable_encryption_in_transit" {
  description = "Enforce encryption in transit for all communications"
  type        = bool
  default     = true
}

# ==============================================================================
# TAGGING CONFIGURATION
# ==============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Cost center for billing purposes"
  type        = string
  default     = "business-intelligence"
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "jorge-real-estate"
}

# ==============================================================================
# FEATURE FLAGS
# ==============================================================================

variable "enable_ai_concierge" {
  description = "Enable AI Concierge features"
  type        = bool
  default     = true
}

variable "enable_predictive_analytics" {
  description = "Enable predictive analytics features"
  type        = bool
  default     = true
}

variable "enable_advanced_visualizations" {
  description = "Enable advanced visualizations with Deck.gl"
  type        = bool
  default     = true
}

variable "enable_real_time_streaming" {
  description = "Enable real-time WebSocket streaming"
  type        = bool
  default     = true
}

# ==============================================================================
# DEVELOPMENT CONFIGURATION
# ==============================================================================

variable "enable_debug_mode" {
  description = "Enable debug mode (should be false in production)"
  type        = bool
  default     = false
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"

  validation {
    condition = contains(["DEBUG", "INFO", "WARN", "ERROR"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARN, ERROR."
  }
}

# ==============================================================================
# VARIABLE VALIDATION
# ==============================================================================

# Ensure production environment has appropriate settings
locals {
  is_production = var.environment == "production"

  # Validation checks for production environment
  production_validations = {
    deletion_protection = local.is_production ? var.enable_deletion_protection : true
    storage_encryption  = local.is_production ? var.storage_encrypted : true
    multi_az           = local.is_production ? var.enable_multi_az : true
    debug_mode         = local.is_production ? !var.enable_debug_mode : true
  }
}

# Production environment validations
variable "enforce_production_standards" {
  description = "Enforce production standards for critical settings"
  type        = bool
  default     = true
}

# Validate production standards
resource "null_resource" "production_validation" {
  count = var.enforce_production_standards && local.is_production ? 1 : 0

  # This will fail if production standards are not met
  provisioner "local-exec" {
    command = <<-EOT
      if [ "${var.enable_deletion_protection}" != "true" ]; then
        echo "ERROR: Deletion protection must be enabled in production"
        exit 1
      fi
      if [ "${var.storage_encrypted}" != "true" ]; then
        echo "ERROR: Storage encryption must be enabled in production"
        exit 1
      fi
      if [ "${var.enable_multi_az}" != "true" ]; then
        echo "ERROR: Multi-AZ must be enabled in production"
        exit 1
      fi
      if [ "${var.enable_debug_mode}" == "true" ]; then
        echo "ERROR: Debug mode must be disabled in production"
        exit 1
      fi
      echo "Production standards validation passed"
    EOT
  }
}