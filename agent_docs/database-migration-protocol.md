# Safe Database Migrations

## Before Schema Change
1. Write migration: `npx prisma migrate dev --name add_feature`
2. Test locally: `npx prisma db push`
3. Write rollback: Ensure migration can reverse
4. Backup production (AWS RDS: create snapshot)

## During Migration
- No downtime: Use **backwards-compatible** changes
- ✅ Good: Add nullable column, add index
- ❌ Bad: Delete column, rename column (requires coordination)

## After Migration
- [ ] Verify schema matches Prisma schema
- [ ] Run integration tests
- [ ] Check performance impact
- [ ] Keep previous migration in git history
