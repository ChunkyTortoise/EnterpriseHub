# Performance Optimization Quick Start Guide

**Last Updated**: January 17, 2026

## 🚀 Quick Deployment (5 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- PostgreSQL database accessible
- Redis instance available
- Environment variables configured

### Step 1: Database Migration

```bash
# Run performance optimization migration
psql $DATABASE_URL < database/migrations/009_performance_optimization_indexes.sql

# Verify indexes created
psql $DATABASE_URL -c "\di" | grep idx_
```

### Step 2: Environment Configuration

```bash
# Copy and configure environment
cp .env.jorge.template .env.jorge.production

# Edit .env.jorge.production with:
# - ENVIRONMENT=production
# - REDIS_URL=redis://your-redis:6379/0
# - DATABASE_URL=postgresql://user:pass@host:5432/db
# - ENABLE_PERFORMANCE_MONITORING=true
```

### Step 3: Deploy Performance-Optimized Stack

```bash
# Start all services
docker-compose -f docker-compose.performance.yml up -d

# Wait for services to be ready (30 seconds)
sleep 30

# Verify deployment
docker-compose -f docker-compose.performance.yml ps
```

### Step 4: Verify Performance

```bash
# Run health checks
curl http://localhost/health
curl http://localhost/api/golden-leads/health
curl http://localhost/api/pricing/health

# Run performance benchmarks
python scripts/performance_benchmark.py --url http://localhost

# Check Grafana dashboards
open http://localhost:3000
# Login: admin / admin (change immediately!)
```

## 📊 Monitoring Access

### Grafana Performance Dashboard
- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin (change in production!)
- **Dashboard**: "Jorge's Revenue Platform - Performance Dashboard"

### Prometheus Metrics
- **URL**: http://localhost:9090
- **Query Examples**:
  - API Response Time: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
  - Cache Hit Rate: `(redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)) * 100`
  - Throughput: `rate(http_requests_total[1m])`

## 🔧 Common Operations

### Scale API Instances
```bash
# Scale to 5 instances
docker-compose -f docker-compose.performance.yml up -d --scale api-instance=5

# Verify load distribution
docker logs jorge-nginx-lb | grep upstream
```

### Check Performance Metrics
```bash
# Get performance summary from Python
python -c "
import asyncio
from ghl_real_estate_ai.services.performance_optimizer import get_performance_optimizer

async def check():
    optimizer = get_performance_optimizer()
    summary = await optimizer.get_performance_summary()
    print(f'P95 Response Time: {summary[\"response_times\"][\"p95_ms\"]}ms')
    print(f'Cache Hit Rate: {summary[\"cache\"][\"hit_rate_percent\"]}%')
    print(f'Throughput: {summary[\"throughput\"][\"avg_req_per_sec\"]} req/sec')

asyncio.run(check())
"
```

### View Logs
```bash
# Load balancer
docker logs -f jorge-nginx-lb

# API instances
docker logs -f jorge-api-1
docker logs -f jorge-api-2

# Database
docker logs -f jorge-postgres-primary

# Redis
docker logs -f jorge-redis-cache
```

## ⚡ Performance Targets Reference

| Metric | Target | Command to Check |
|--------|--------|------------------|
| API Response (P95) | <100ms | `curl -w "@curl-format.txt" http://localhost/api/health` |
| Cache Hit Rate | >90% | `docker exec jorge-redis-cache redis-cli INFO stats \| grep hits` |
| Throughput | >1000/sec | `python scripts/performance_benchmark.py` |
| Memory Usage | <2GB | `docker stats jorge-api-1` |
| CPU Usage | <70% | `docker stats jorge-api-1` |

## 🚨 Troubleshooting

### High Response Times
```bash
# Check slow queries
docker exec jorge-postgres-primary psql -U postgres -c "SELECT * FROM get_recent_slow_queries(100.0, 10);"

# Check NGINX cache
docker logs jorge-nginx-lb | grep "X-Cache-Status"

# Profile endpoint
# Add @track_performance decorator to slow endpoints
```

### Low Cache Hit Rate
```bash
# Check Redis stats
docker exec jorge-redis-cache redis-cli INFO stats

# Check cache keys
docker exec jorge-redis-cache redis-cli --scan --pattern "*"

# Increase TTL if appropriate
# Edit cache_service.py and increase default_cache_ttl_seconds
```

### Database Connection Issues
```bash
# Check connections
docker exec jorge-postgres-primary psql -U postgres -c "
SELECT count(*) as active_connections,
       (SELECT setting::int FROM pg_settings WHERE name='max_connections') as max_connections
FROM pg_stat_activity;
"

# Increase max_connections if needed
# Edit docker-compose.performance.yml:
#   POSTGRES_MAX_CONNECTIONS=300
```

## 📈 Scaling Checklist

### Before Scaling to 10x Traffic
- [ ] Run load tests with `performance_benchmark.py`
- [ ] Monitor metrics for 24 hours
- [ ] Verify cache hit rate >90%
- [ ] Check database connection pool not saturated
- [ ] Ensure CPU usage <60% average
- [ ] Test automatic failover (kill one API instance)
- [ ] Verify backup and disaster recovery

### Horizontal Scaling
```bash
# Scale API instances
docker-compose -f docker-compose.performance.yml up -d --scale api-instance=5

# Add database read replicas
# (Requires PostgreSQL streaming replication setup)

# Add Redis Sentinel for HA
# (Already configured in docker-compose.performance.yml)
```

## 📚 Documentation Links

- **Full Handoff**: [PERFORMANCE_OPTIMIZATION_HANDOFF_2026-01-17.md](PERFORMANCE_OPTIMIZATION_HANDOFF_2026-01-17.md)
- **Benchmark Suite**: [scripts/performance_benchmark.py](scripts/performance_benchmark.py)
- **Performance Optimizer**: [ghl_real_estate_ai/services/performance_optimizer.py](ghl_real_estate_ai/services/performance_optimizer.py)
- **NGINX Config**: [nginx/nginx.conf](nginx/nginx.conf)
- **Database Migration**: [database/migrations/009_performance_optimization_indexes.sql](database/migrations/009_performance_optimization_indexes.sql)

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ All health checks return 200 OK
- ✅ Performance benchmarks show grade "A" or higher
- ✅ Grafana dashboard shows all metrics in green
- ✅ Cache hit rate >90%
- ✅ API response time (P95) <100ms
- ✅ No errors in application logs

## 🆘 Support

For issues or questions:
1. Check the [Full Handoff Document](PERFORMANCE_OPTIMIZATION_HANDOFF_2026-01-17.md)
2. Review Grafana alerts and logs
3. Run diagnostics: `python scripts/performance_benchmark.py`
4. Contact: [Your Support Contact]

---

**Ready to deploy!** 🚀

Start with: `docker-compose -f docker-compose.performance.yml up -d`
