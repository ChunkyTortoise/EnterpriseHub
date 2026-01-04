# Phase 2 Deployment Checklist

## Pre-Deployment

- [ ] All 63 tests passing locally
- [ ] Integration report reviewed (Agent Alpha)
- [ ] Railway project exists: `ghl-real-estate-ai`
- [ ] Git branch clean and committed
- [ ] Backup of Phase 1 deployment taken

## Environment Variables

### Required (Already Set from Phase 1)
- [ ] `ANTHROPIC_API_KEY` - Claude API key
- [ ] `GHL_API_KEY` - GoHighLevel API key (or per-tenant)
- [ ] `ENVIRONMENT` - Set to "production"

### Optional New Variables
- [ ] `ENABLE_ANALYTICS` - Enable analytics endpoints (default: true)
- [ ] `ENABLE_BULK_OPS` - Enable bulk operations (default: true)
- [ ] `ENABLE_LIFECYCLE` - Enable lifecycle features (default: true)
- [ ] `MAX_BULK_OPERATION_SIZE` - Max items per bulk op (default: 1000)

## Railway Deployment Steps

1. [ ] Connect to Railway project
   ```bash
   railway link ghl-real-estate-ai
   ```

2. [ ] Review current deployment
   ```bash
   railway status
   ```

3. [ ] Deploy Phase 2
   ```bash
   railway up
   ```

4. [ ] Monitor deployment logs
   ```bash
   railway logs
   ```

5. [ ] Verify deployment successful
   ```bash
   railway run python -c "print('Phase 2 deployed')"
   ```

## Post-Deployment Validation

- [ ] Health check responds: `GET /health`
- [ ] API docs accessible: `GET /docs` (if dev mode)
- [ ] Test analytics endpoint: `GET /api/analytics/dashboard?location_id=test&days=7`
- [ ] Test webhook still works: `POST /api/ghl/webhook`
- [ ] Check Railway logs for errors

## Rollback Procedure (If Needed)

1. [ ] Note current deployment ID
2. [ ] Rollback via Railway dashboard
3. [ ] Or redeploy previous git commit
4. [ ] Verify Phase 1 functionality restored

## Success Criteria

- [ ] All endpoints responding
- [ ] No errors in logs
- [ ] Phase 1 functionality intact
- [ ] Response times < 200ms

---

**Prepared by:** Agent Beta - Deployment Engineer
**Date:** 2026-01-04
