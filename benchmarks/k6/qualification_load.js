/**
 * k6 Load Test — Lead Qualification Ramp
 *
 * Tests POST /api/v1/orchestration/qualify with 50 VUs ramping over 30s.
 * Captures P50/P95/P99 latency and error rate against the headline
 * "150 req/s" claim. Run this to get a real answer.
 *
 * Usage:
 *   k6 run benchmarks/k6/qualification_load.js \
 *     --out json=benchmarks/results/2026-W17/qualification_load.json \
 *     -e BASE_URL=http://localhost:8000
 *
 * Or via benchmarks/run_k6.sh for all three scripts.
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate, Counter } from "k6/metrics";

const qualifyDuration = new Trend("qualify_duration", true);
const errorRate = new Rate("qualify_error_rate");
const qualifiedLeads = new Counter("qualified_leads");

export const options = {
  stages: [
    { duration: "30s", target: 50 }, // ramp up to 50 VUs
    { duration: "60s", target: 50 }, // steady state
    { duration: "15s", target: 0 },  // ramp down
  ],
  thresholds: {
    qualify_duration: ["p(95)<2000"],  // 95th percentile < 2s
    qualify_error_rate: ["rate<0.01"], // <1% errors
    http_req_failed: ["rate<0.01"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

// Realistic lead message pool
const MESSAGES = [
  "Hi, I'm interested in homes in Rancho Cucamonga under $700k",
  "Looking for a 3 bed 2 bath, max $650k budget",
  "What's available in the $500k-$600k range?",
  "I need to sell my house first before buying",
  "Just browsing, not ready to commit yet",
  "We're pre-approved for $800k, looking for something with a pool",
  "First-time buyer here, what programs are available?",
  "My lease ends in 3 months, need to move fast",
];

function randomMessage() {
  return MESSAGES[Math.floor(Math.random() * MESSAGES.length)];
}

function randomContactId() {
  return `load-test-${__VU}-${__ITER}`;
}

export default function () {
  const payload = JSON.stringify({
    contact_id: randomContactId(),
    location_id: "load-test-location",
    message: randomMessage(),
    contact_tags: [],
    contact_info: {
      first_name: "Test",
      last_name: `User${__VU}`,
      email: `test.vu${__VU}@loadtest.local`,
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
    "has success field": (r) => {
      try {
        return JSON.parse(r.body).success !== undefined;
      } catch {
        return false;
      }
    },
  });

  qualifyDuration.add(res.timings.duration);
  errorRate.add(!ok);

  if (ok && res.status === 200) {
    try {
      const body = JSON.parse(res.body);
      if (body.is_qualified) qualifiedLeads.add(1);
    } catch {
      // ignore parse errors — already captured in error rate
    }
  }

  sleep(Math.random() * 0.5); // 0–500ms think time
}
