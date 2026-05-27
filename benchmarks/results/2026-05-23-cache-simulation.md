# Cache Simulation Result

Date: 2026-05-23

## Command

```bash
python3 -m benchmarks.bench_cache
```

## Result Summary

| Metric | Value | Claim Type |
|---|---:|---|
| Operations | 10,000 | Synthetic benchmark |
| Sampled hits | 8,807 | Synthetic benchmark |
| Sampled misses | 1,193 | Synthetic benchmark |
| Modeled hit rate | 88.1% | Design-target simulation |
| L1 P99 | 0.60ms | Synthetic latency model |
| L2 P99 | 3.93ms | Synthetic latency model |
| L3 P99 | 16.06ms | Synthetic latency model |
| Overall P95 | 14.36ms | Synthetic latency model |
| Overall P99 | 16.50ms | Synthetic latency model |

## Interpretation

This is a Monte Carlo simulation of the cache design target, not a live production measurement. The 88.1% modeled hit rate is sampled from the configured L1/L2/L3 distribution in `benchmarks/bench_cache.py`.

Use this artifact to support architecture and latency-model discussion. Do not use it to claim measured production cache hit rate, measured token savings, uptime, or live billing savings.

