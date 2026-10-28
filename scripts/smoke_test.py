"""Smoke test for a running AI Simulator Service instance.

Uses only the standard library, so it runs inside the runtime image:
    docker exec -i <container> python - < scripts/smoke_test.py
    kubectl exec -i deploy/ai-sim -- python - < scripts/smoke_test.py
    python scripts/smoke_test.py http://localhost:8100
"""
import json
import sys
import time
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8100"

PREDICT_PAYLOAD = {
    "student_data": [{
        "student_id": "smoke-1",
        "attendance_rate": 0.2,
        "assignment_completion": 0.1,
        "avg_grade": 20,
        "forum_posts": 0,
        "time_on_platform": 1,
        "late_submissions": 15,
    }]
}


def request(path, payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE_URL + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read())


def wait_for_health(attempts=30, delay=2):
    for _ in range(attempts):
        try:
            status, body = request("/health", timeout=3)
            if status == 200 and body.get("status") == "ok":
                return
        except OSError:
            pass
        time.sleep(delay)
    sys.exit(f"FAIL: {BASE_URL}/health did not become healthy")


def main():
    wait_for_health()
    print("OK   GET  /health")

    # The first call trains the risk model if data/model.pkl is missing
    status, body = request("/api/v1/predict", PREDICT_PAYLOAD, timeout=120)
    if status != 200 or len(body.get("predictions", [])) != 1:
        sys.exit(f"FAIL: /api/v1/predict returned {status}: {body}")
    p = body["predictions"][0]
    print(f"OK   POST /api/v1/predict -> risk_level={p['risk_level']} risk_score={p['risk_score']}")
    print("Smoke test passed")


if __name__ == "__main__":
    main()
