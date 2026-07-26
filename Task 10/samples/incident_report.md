# Incident Report — INC-2481: Checkout Latency Spike

**Date:** 12 March 2026
**Severity:** SEV-2
**Duration:** 3h 14m (09:42 – 12:56 WAT)
**Author:** Chidera Nwosu, Platform Reliability

## Summary

Between 09:42 and 12:56 on 12 March, checkout API p95 latency rose from a baseline
of 340 ms to a peak of 8.7 seconds. Roughly 18,400 checkout attempts were affected
and an estimated 2,900 carts were abandoned during the window. No data was lost and
no payments were double-charged.

## Timeline

- 09:42 — Latency alert fires on the `checkout-api` service. On-call paged.
- 09:51 — On-call acknowledges. Initial hypothesis is a downstream payment provider issue.
- 10:15 — Payment provider status page is green. Hypothesis discarded.
- 10:40 — Database CPU observed at 96% sustained. Connection pool saturated at 200/200.
- 11:20 — A slow query is traced to the new `order_promotions` join added in release 4.19.2.
- 11:35 — Decision made to roll back release 4.19.2 rather than hotfix forward.
- 12:10 — Rollback deployed to 50% of instances. Latency begins recovering.
- 12:56 — Full rollback complete. p95 back to 355 ms. Incident closed.

## Root Cause

Release 4.19.2 introduced a promotions lookup that joined `orders` against
`order_promotions` without an index on `order_promotions.order_id`. In staging the table
held 4,000 rows and the query returned in 12 ms. In production the table holds 41 million
rows, and the planner fell back to a sequential scan taking 6–9 seconds per call. Because
the checkout path calls this query synchronously, every request held its database
connection for the duration, saturating the pool and starving unrelated queries.

## Contributing Factors

- Staging data volume is not representative of production, and there is no automated check for this.
- The query was not covered by the load test suite, which exercises only the cart and search paths.
- Our slow-query alert threshold is 10 seconds, so a 6–9 second query never triggered it.
- The on-call engineer spent 33 minutes on the payment-provider hypothesis because the
  runbook lists it first for checkout latency.

## Action Items

1. Add an index on `order_promotions.order_id`. Owner: Chidera. Due 14 March.
2. Lower the slow-query alert threshold from 10s to 2s. Owner: Femi. Due 20 March.
3. Seed staging with a sampled 10% copy of production volume nightly. Owner: Data Platform. Due 3 April.
4. Extend the load test suite to cover the checkout path end to end. Owner: Tolu. Due 10 April.
5. Reorder the checkout latency runbook to put database saturation ahead of provider status. Owner: Chidera. Due 18 March.

## Open Questions

- Should schema changes touching tables above 1 million rows require a mandatory query plan review?
- Do we need a circuit breaker on the checkout path so a slow dependency sheds load rather than saturating the pool?
