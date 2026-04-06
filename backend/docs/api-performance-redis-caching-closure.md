# API Performance and Redis Caching Closure (University Viva Pack)

## Milestone Summary
- Milestone: API Performance Optimization and Caching Using Redis (Flask)
- Status: Completed
- Final commit: acd13d6
- Commit message: Milestone-PPA-V2 Redis-Caching

## Simple Architecture (Easy to Explain)
1. Client calls API endpoint.
2. Backend checks Redis cache first.
3. If cache hit, return cached response.
4. If cache miss, query database and return response.
5. Backend stores response in Redis with TTL.
6. On write/update actions, related cache keys are invalidated.
7. If Redis is down, backend continues from DB path (fail-open behavior).

## Requirement Coverage Matrix
| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Use Redis caching for API optimization | Shared cache extension with Redis-backed JSON store and fail-open behavior | backend/app/cache.py |
| Cache frequently used endpoint: job listings | GET /admin/jobs read-through cache | backend/app/admin/routes.py |
| Cache frequently used endpoint: company search | GET /admin/search/companies read-through cache | backend/app/admin/routes.py |
| Cache frequently used endpoint: student search | GET /admin/search/students read-through cache | backend/app/admin/routes.py |
| Implement proper cache expiry policy | Configurable TTL in app config (default + per endpoint) | backend/app/__init__.py |
| Implement refresh/invalidation policy | Cache invalidation on successful write flows in admin/company/student/auth routes | backend/app/admin/routes.py, backend/app/company/routes.py, backend/app/student/routes.py, backend/app/auth/routes.py |
| Graceful fallback if Redis unavailable | Cache layer marks itself unavailable and requests continue via DB/service logic | backend/app/cache.py |

## Cached Endpoints and TTL Policy
| Endpoint | Cache Namespace | Default TTL | Invalidated By |
| --- | --- | --- | --- |
| GET /admin/jobs | admin:jobs | 120s | Job approve/reject/delete, company drive create/close |
| GET /admin/search/companies | admin:search:companies | 90s | Company approve/reject/activate/deactivate/delete, company profile update, company registration |
| GET /admin/search/students | admin:search:students | 90s | Student activate/deactivate, student profile update, student registration |

## Safety Notes (Viva-Friendly)
1. The cache is additive, not mandatory. API still works without Redis.
2. Read endpoints only are cached; write endpoints are never served from cache.
3. Only successful 200 responses are cached.
4. Invalidation is namespace-based to avoid stale data after updates.
5. Test fixture keeps cache disabled for non-cache tests to avoid external dependency flakiness.

## Test Evidence
### Cache-Specific Tests
- test_admin_cache_miss_then_set_and_hit
- test_admin_cache_expiry_refreshes_company_search
- test_admin_cache_invalidation_refreshes_jobs_after_write
- test_admin_cache_gracefully_falls_back_when_redis_unavailable

File: backend/tests/test_admin_redis_cache.py

### Full Backend Gate
- Result: 62 passed, 0 failed
- Command: pytest -q

## 2-Minute Viva Script
Use this exact flow while explaining:

1. "We added Redis as a read-through cache layer for three heavy admin read APIs: jobs, company search, and student search."
2. "For each request, backend first checks Redis. On miss, it queries DB and stores the response with TTL."
3. "TTL is configurable and currently practical defaults are 120 seconds for jobs and 90 seconds for both searches."
4. "Whenever related data changes, we invalidate only related cache namespaces so stale data is not served."
5. "If Redis is unavailable, the app falls back to DB path automatically, so functionality is not blocked."
6. "We validated this with dedicated tests for miss-hit, expiry, invalidation-refresh, and Redis-down fallback, then passed full backend regression."

## Optional Demo Steps (If Faculty Asks)
1. Show first request to one cached endpoint (cold request).
2. Repeat same request immediately (warm request).
3. Explain that second response is served from cache.
4. Perform a related write action (for example job approve) and repeat read request.
5. Show that read response refreshes after invalidation.
6. Stop Redis and repeat read request to show graceful fallback.
