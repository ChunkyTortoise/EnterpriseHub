/**
 * k6 Burst Test — Spike to 500 Concurrent Users
 *
 * Tests the "500 concurrent users" claim by spiking from 10 → 500 VUs in
 * 15s, holding for 30s, then recovering. Records error rate and latency
 * degradation at peak load. Reveals actual concurrency ceiling.
 *
 * Usage:
 *   k6 run benchmarks/k6/burst.js \
 *     --out json=benchmarks/results/2026-W17/burst.json \
 *     -e BASE_URL=http://localhost:8000
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

const burstDuration = new Trend("burst_qualify_duration", true);
const errorRate = new Rate("burst_error_rate");
const peakErrorRate = new Rate("burst_peak_error_rate");

export const options = {
  stages: [
    { duration: "10s", target: 10 },  // baseline
    { duration: "15s", target: 500 }, // spike
    { duration: "30s", target: 500 }, // hold at peak
    { duration: "15s", target: 10 },  // recover
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    burst_error_rate: ["rate<0.05"],  // tolerate up to 5% errors during burst
    http_req_failed: ["rate<0.10"],   // hard stop at 10% failure
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

const MESSAGES = [
  "Interested in homes around $650k",
  "Looking for investment properties",
  "Need something fast — closing in 60 days",
  "What are interest rates like right now?",
  "3 bed 2 bath, good school district",
];

function isAtPeak() {
  // Approximate: stages 2+3 cover 10s–55s of elapsed time
  const elapsed = new Date() - __ENV._startTime;
  return elapsed > 10000 && elapsed < 55000;
}

export default function () {
  const payload = JSON.stringify({
    contact_id: `burst-${__VU}-${__ITER}`,
    location_id: "burst-test-location",
    message: MESSAGES[Math.floor(Math.random() * MESSAGES.length)],
    contact_tags: [],
    contact_info: { first_name: "Burst", last_name: `VU${__VU}` },
    conversation_history: null,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    timeout: "15s",
  };

  const res = http.post(
    `${BASE_URL}/api/v1/orchestration/qualify`,
    payload,
    params
  );

  const ok = check(res, {
    "status 200 or 429": (r) => r.status === 200 || r.status === 429,
    "not 5xx": (r) => r.status < 500,
  });

  burstDuration.add(res.timings.duration);
  errorRate.add(!ok);
  if (isAtPeak()) peakErrorRate.add(!ok);

  sleep(0.1);
}
