#!/usr/bin/env python3
"""Self-check geo payload validator pass and rejection paths."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate-geo-payload.py"


def payload(city: str = "Lyon") -> dict[str, object]:
    description = " ".join(["Evidence-backed local service guidance supports informed decisions."] * 100)
    return {
        "id": f"service-{city.casefold()}", "city": city,
        "h1": f"Local service guidance for {city}",
        "hook": f"Verified local context helps {city} readers choose next steps with confidence.",
        "excerpt": f"Evidence-backed service guidance for {city} explains local options, process, and practical next steps for readers planning a decision today.",
        "description": description,
        "faq": [{"question": f"Question {number}", "answer": "Evidence-backed answer."} for number in range(4)],
        "timeline": [{"title": f"Stage {number}"} for number in range(4)],
        "qualities": [{"title": f"Quality {number}"} for number in range(3)],
        "source_index": {"S1": {"title": "Official source"}},
        "sources": [{"id": "S1", "url": "https://authority.example.org/local"}],
        "evidence": [{"source_id": "S1", "claim": "Local process."}],
    }


def persisted_payload() -> dict[str, object]:
    flat = payload("Toulouse")
    return {
        "id": 123,
        "title": "Local service guidance for Toulouse",
        "post_excerpt": flat["excerpt"],
        "evidence_map": {"h1": ["D01"], "sources": ["D01"]},
        "fields": {
            "h1": flat["h1"], "hook": flat["hook"], "description": flat["description"],
            "faq": flat["faq"], "conversion-timeline": flat["timeline"],
            "conversion-qualities": flat["qualities"],
            "sources": [{"title": "Official source", "url": "https://authority.example.org/local"}],
        },
    }


def run(*files: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", str(VALIDATOR), *map(str, files)], text=True, capture_output=True, check=False)


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        good = root / "good.json"
        good.write_text(json.dumps(payload()))
        result = run(good)
        if result.returncode or not json.loads(result.stdout)["valid"]:
            raise AssertionError(result.stdout + result.stderr)
        bad = root / "bad.json"
        invalid = payload()
        invalid["hook"] = "best in Lyon"
        invalid["sources"] = [{"id": "missing", "url": "https://example.com"}]
        invalid["timeline"] = []
        bad.write_text(json.dumps(invalid))
        result = run(bad)
        if result.returncode == 0 or json.loads(result.stdout)["valid"]:
            raise AssertionError("validator accepted invalid payload")
        sibling = root / "sibling.json"
        sibling.write_text(json.dumps(payload("Paris")))
        result = run(good, sibling)
        if result.returncode == 0:
            raise AssertionError("validator accepted city-swap sibling pair")
        unrelated = root / "unrelated.json"
        other = payload("Paris")
        other["h1"] = "Completely different topical guidance for Paris readers"
        unrelated.write_text(json.dumps(other))
        result = run(good, unrelated)
        if result.returncode != 0:
            raise AssertionError("validator flagged non-sibling pair: " + result.stdout)
        real = root / "real-shape.json"
        real.write_text(json.dumps(persisted_payload()))
        result = run(real)
        if result.returncode or not json.loads(result.stdout)["valid"]:
            raise AssertionError("validator rejected real persisted shape:\n" + result.stdout + result.stderr)
    print("Geo payload validator tests OK (valid payload, schema/content/source rejection, city-swap rejection, non-sibling pass, real persisted shape)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
