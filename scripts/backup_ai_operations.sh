#!/bin/bash
# AI-Enhanced Operations Backup Script

set -e

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting AI Operations backup at $(date)"

# Backup PostgreSQL database
echo "Backing up PostgreSQL..."
kubectl exec deployment/postgres -- pg_dump ai_operations | gzip > $BACKUP_DIR/postgres_backup.sql.gz

# Backup Redis data
echo "Backing up Redis..."
kubectl exec deployment/redis -- redis-cli save
kubectl cp redis-deployment:/data/dump.rdb $BACKUP_DIR/redis_backup.rdb

# Backup Kubernetes configurations
echo "Backing up Kubernetes configurations..."
kubectl get all -n ai-operations -o yaml > $BACKUP_DIR/k8s_resources.yaml
kubectl get configmaps -n ai-operations -o yaml > $BACKUP_DIR/configmaps.yaml
kubectl get secrets -n ai-operations -o yaml > $BACKUP_DIR/secrets.yaml
kubectl get pvc -n ai-operations -o yaml > $BACKUP_DIR/persistent_volumes.yaml

# Backup ML models
echo "Backing up ML models..."
for component in intelligent-monitoring-engine auto-scaling-controller self-healing-system performance-predictor; do
    kubectl exec deployment/$component -- tar -czf - /app/models/ > $BACKUP_DIR/${component}_models.tar.gz
done

# Backup application configurations
echo "Backing up application configurations..."
cp -r config/ $BACKUP_DIR/
cp -r monitoring/ $BACKUP_DIR/
cp docker-compose.production.yml $BACKUP_DIR/
cp nginx.conf $BACKUP_DIR/

# Create backup manifest
cat > $BACKUP_DIR/backup_manifest.json << EOF
{
  "backup_date": "$(date -Iseconds)",
  "platform": "AI-Enhanced Operations",
  "version": "1.0.0",
  "components": [
    "intelligent_monitoring_engine",
    "auto_scaling_controller",
    "self_healing_system",
    "performance_predictor",
    "operations_dashboard",
    "enhanced_ml_integration"
  ],
  "backup_size_mb": $(du -sm $BACKUP_DIR | cut -f1),
  "files_included": [
    "postgres_backup.sql.gz",
    "redis_backup.rdb",
    "k8s_resources.yaml",
    "configmaps.yaml",
    "secrets.yaml",
    "persistent_volumes.yaml",
    "ml_models",
    "application_configs"
  ]
}
EOF

echo "Backup completed successfully at $BACKUP_DIR"
echo "Backup size: $(du -sh $BACKUP_DIR | cut -f1)"

# Cleanup old backups (keep last 30 days)
find /backups -type d -mtime +30 -exec rm -rf {} +

echo "Backup process finished at $(date)"
