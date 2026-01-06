# Performance Optimization Checklist

## Query Optimization
- [ ] No N+1 queries (use DataLoader for GraphQL)
- [ ] Indexes on frequently filtered columns
- [ ] Pagination on large result sets (cursor-based)
- [ ] Select only needed fields (not SELECT *)

## Caching
- [ ] Redis for session tokens
- [ ] ETags for REST endpoints
- [ ] Browser caching headers (Cache-Control)

## Monitoring
- Use Sentry for error tracking
- Log slow queries (>1 second)
- Monitor memory usage (Node.js: --max-old-space-size)
