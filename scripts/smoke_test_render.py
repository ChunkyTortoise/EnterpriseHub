#!/usr/bin/env python3
"""
Smoke test for Jorge Bot live on Render.

Usage:  python3 scripts/smoke_test_render.py
"""
import hashlib, hmac, json, sys, time, urllib.error, urllib.request

BASE        = "https://jorge-realty-ai-xxdf.onrender.com"
HMAC_SECRET = "ffb42fb9b69801686e04edbcb2f54f4f123eb3389bb1dedf9317930a0518bd10"
LOCATION_ID = "3xt4qayAh35BlDLaUv7P"

def signed_post(payload):
    body = json.dumps(payload).encode()
    sig  = hmac.new(HMAC_SECRET.encode(), body, hashlib.sha256).hexdigest()
    req  = urllib.request.Request(
        f"{BASE}/api/ghl/webhook", data=body, method="POST",
        headers={"Content-Type": "application/json", "x-ghl-signature": sig},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.reason}

def run():
    ts, results = int(time.time()), []

    # 1 — health
    try:
        with urllib.request.urlopen(f"{BASE}/api/ghl/health", timeout=10) as r:
            ok = r.status == 200
    except Exception as e:
        ok = False
    results.append(ok)
    print(f"[1] GET  /api/ghl/health  → {'✅ PASS' if ok else '❌ FAIL'}")

    # 2 — seller
    status, resp = signed_post({
        "type": "InboundMessage", "locationId": LOCATION_ID,
        "contactId": f"smoke-seller-{ts}", "tags": ["Needs Qualifying"],
        "message": {"body": "Is Zillow accurate for my home?", "type": "SMS", "direction": "inbound"},
    })
    ok = status == 200 and resp.get("success") is True
    results.append(ok)
    print(f"[2] POST /webhook seller  → {'✅ PASS' if ok else '❌ FAIL'} ({status})")

    # 3 — buyer
    status, resp = signed_post({
        "type": "InboundMessage", "locationId": LOCATION_ID,
        "contactId": f"smoke-buyer-{ts}", "tags": ["Buyer-Lead"],
        "message": {"body": "I want to buy under 600k", "type": "SMS", "direction": "inbound"},
    })
    ok = status == 200 and resp.get("success") is True
    results.append(ok)
    print(f"[3] POST /webhook buyer   → {'✅ PASS' if ok else '❌ FAIL'} ({status})")

    passed = sum(results)
    print(f"\n{'✅ ALL PASS' if passed == len(results) else '❌ FAILURES'} ({passed}/{len(results)})")
    return passed == len(results)

if __name__ == "__main__":
    print(f"Smoke testing {BASE}\n")
    sys.exit(0 if run() else 1)
