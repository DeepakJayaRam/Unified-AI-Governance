"""Repeatable native-check and ASGI application latency benchmark; no proxy claim."""
import json
import platform
import statistics
import time
from pathlib import Path


def distribution(values):
    ordered = sorted(values)
    return {"samples": len(values), "p50_ms": statistics.median(values), "p95_ms": ordered[int(len(values)*.95)-1], "p99_ms": ordered[int(len(values)*.99)-1]}


def main():
    from uag.runtime import evaluate
    from uag.schemas import PolicyConfig
    config = PolicyConfig(blocked_terms=["restricted phrase"])
    cases = {"short_safe": "Summarise the approved operating procedure.", "pii": "Email person@example.invalid; candidate identifier 123-45-6789.", "maximum_input": "A" * 31960 + " contact person@example.invalid"}
    report = {"environment": {"python": platform.python_version(), "platform": platform.platform(), "processor": platform.processor()}, "scope": "Native deterministic checks only, in-process; excludes HTTP, auth, DB, proxy, Presidio and model services", "cases": {}}
    for label, text in cases.items():
        for _ in range(30):
            evaluate(text, config)
        durations, checks = [], {}
        for _ in range(500):
            start = time.perf_counter()
            result = evaluate(text, config)
            durations.append((time.perf_counter()-start)*1000)
            for check in result["checks"]:
                checks.setdefault(check["name"], []).append(check["latency_ms"])
        report["cases"][label] = {"pipeline": distribution(durations), "checks": {key: distribution(values) for key, values in checks.items()}}
    target = Path("docs/validation/native-benchmark.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
