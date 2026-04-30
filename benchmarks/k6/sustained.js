/**
 * k6 Sustained Throughput Test — 150 req/s for 10 minutes
 *
 * Validates the "150 req/s" throughput claim against
 * POST /api/v1/orchestration/qualify. Uses k6's constant-arrival-rate
 * executor so req/s is the control variable, not VU count.
 * Captures throughput stability, latency percentiles over time,
 * and error budget consumption across the full window.
 *
 * This script produces the numbers that back case study claims.
 * Do not quote numbers from bench_cache.py (simulation) in its place.
 *
 * Usage:
 *   k6 run benchmarks/k6/sustained.js \
 *     --out json=benchmarks/results/2026-W17/sustained.json \
 *     -e BASE_URL=http://localhost:8000 \
 *     -e TARGET_RPS=150
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate, Counter } from "k6/metrics";

const sustainedDuration = new Trend("sustained_duration", true);
const errorRate = new Rate("sustained_error_rate");
const totalRequests = new Counter("sustained_total_requests");

const TARGET_RPS = parseInt(__ENV.TARGET_RPS || "150", 10);
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  scenarios: {
    sustained_load: {
      executor: "constant-arrival-rate",
      rate: TARGET_RPS,
      timeUnit: "1s",
      duration: "10m",
      preAllocatedVUs: Math.ceil(TARGET_RPS * 1.5), // headroom for slow responses
      maxVUs: TARGET_RPS * 4,
    },
  },
  thresholds: {
    sustained_duration: [
      "p(50)<500",   // P50 < 500ms
      "p(95)<2000",  // P95 < 2s
      "p(99)<5000",  // P99 < 5s
    ],
    sustained_error_rate: ["rate<0.01"],
    http_req_failed: ["rate<0.01"],
  },
};

const MESSAGES = [
  "Interested in Rancho Cucamonga homes under $700k",
  "Looking for 3/2 with good schools",
  "We're pre-approved, moving in 90 days",
  "Just starting our home search",
  "Investor looking for multi-unit properties",
  "Need to sell first, timeline flexible",
  "First-time buyer, what programs apply to me?",
  "Price range $500k-$650k, need pool or large yard",
];

export default function () {
  const payload = JSON.stringify({
    contact_id: `sustained-${__VU}-${__ITER}`,
    location_id: "sustained-test-location",
    message: MESSAGES[Math.floor(Math.random() * MESSAGES.length)],
    contact_tags: [],
    contact_info: {
      first_name: "Sustained",
      last_name: `VU${__VU}`,
      email: `sustained.vu${__VU}@loadtest.local`,
    },
    conversation_history: null,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    timeout: "10s",
  };

  const res = http.post(
    `${BASE_URL}/api/v1/orchestration/qualify`,
    payload,
    params
  );

  const ok = check(res, {
    "status 200": (r) => r.status === 200,
    "body parseable": (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    },
  });

  sustainedDuration.add(res.timings.duration);
  errorRate.add(!ok);
  totalRequests.add(1);
}
