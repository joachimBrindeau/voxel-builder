#!/usr/bin/env python3
"""Exercise Organization lane validation and deterministic merge. Stdlib only."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate-organization-profile.py"


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VALIDATOR), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def expect_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise AssertionError(f"{label} failed:\n{result.stdout}{result.stderr}")


def expect_rejected(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode == 0:
        raise AssertionError(f"validator accepted {label}")


def expect_rejected_with(result: subprocess.CompletedProcess[str], label: str, message: str) -> None:
    expect_rejected(result, label)
    if message not in result.stdout:
        raise AssertionError(f"{label} missed expected error {message!r}:\n{result.stdout}{result.stderr}")


def expect_cli_error_with(result: subprocess.CompletedProcess[str], label: str, message: str) -> None:
    expect_rejected(result, label)
    if message not in result.stderr:
        raise AssertionError(f"{label} missed expected CLI error {message!r}:\n{result.stdout}{result.stderr}")


def fixtures() -> dict[str, dict[str, object]]:
    history = (
        "<h3>Origins</h3><p><strong>Brand</strong> began in <strong>1900</strong> in "
        "<strong>Uji</strong>, building its work around stone-milled <em>tencha</em> (shade-grown tea leaf). "
        "The family later expanded direct sales while preserving documented regional sourcing and careful milling.</p>"
    )
    matcha = (
        "<h3>Matcha range</h3><p><strong>Brand Ceremonial Matcha</strong> is sold in a 30 g tin for whisked tea. "
        "Its documented product range also includes a culinary powder intended for desserts and mixed drinks. "
        "The official catalog distinguishes the products by use rather than unsupported quality claims.</p>"
    )
    harvest = (
        "<h3>Production</h3><p>The brand sources <em>tencha</em> (shade-grown tea leaf) from "
        "<strong>Uji, Kyoto</strong>. Leaves are shaded before harvest, dried without rolling, and stone-milled. "
        "Published production notes identify the region but do not claim a single-estate source.</p>"
    )
    faq_answer = (
        "<p><strong>Brand Ceremonial Matcha</strong> is the whisked-tea option in the documented range, "
        "while the culinary powder is positioned for desserts and mixed drinks.</p>"
    )
    return {
        "foundation": {
            "title": "Brand",
            "url_slug": "brand",
            "metadescription": "Brand, founded in 1900 in Uji, offers documented ceremonial and culinary matcha shaped by regional tencha sourcing and traditional stone milling practices.",
            "tagline": "Uji matcha rooted in documented family craft",
            "history-content": history,
            "history-events": [
                {"event-date": "1900-01-01", "event-name": "Brand founded in Uji", "event-description": "The founding family established the documented tea business in Uji and began regional production."},
                {"event-date": "1950-01-01", "event-name": "Direct sales expanded", "event-description": "The company expanded direct customer sales while continuing its documented regional sourcing practices."},
            ],
        },
        "production": {"title": "Brand", "matcha-content": matcha, "harvest-location": harvest},
        "contact": {
            "title": "Brand",
            "contact": [{"canal-type": ["website"], "canal-value": "https://example.com/"}],
            "location": {"address": "Uji, Kyoto, Japan", "map_picker": False, "latitude": None, "longitude": None},
        },
        "faq": {
            "title": "Brand",
            "faq": [
                {"question": "Which Brand matcha is intended for whisked tea?", "answer": faq_answer},
                {"question": "How does Brand distinguish its culinary matcha?", "answer": faq_answer},
                {"question": "What size is the Brand Ceremonial Matcha tin?", "answer": faq_answer},
                {"question": "Should I choose Brand Ceremonial Matcha for desserts?", "answer": faq_answer},
            ],
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        data = fixtures()
        paths: dict[str, Path] = {}
        for lane, value in data.items():
            path = root / f"{lane}.json"
            write(path, value)
            paths[lane] = path
            expect_ok(invoke("--lane", lane, "--brand-name", "Brand", str(path)), f"valid {lane}")

        help_result = invoke("--help")
        expect_ok(help_result, "--help")
        for text in ("usage:", "Validate", "--lane", "--merge", "profile JSON"):
            if text not in help_result.stdout:
                raise AssertionError(f"--help missed useful text {text!r}:\n{help_result.stdout}")
        expect_cli_error_with(invoke(), "missing profile argument", "file is required unless --merge is used")
        expect_cli_error_with(invoke("--unknown-option"), "unknown option", "unrecognized arguments: --unknown-option")

        scalar_cases = [
            ("foundation", ("title",), "title must be a non-empty string"),
            ("foundation", ("url_slug",), "url_slug must be a non-empty string"),
            ("foundation", ("metadescription",), "metadescription must be a non-empty string"),
            ("foundation", ("tagline",), "tagline must be a non-empty string"),
            ("foundation", ("history-content",), "history-content must be a non-empty string"),
            ("foundation", ("history-events", 0, "event-date"), "history-events[0].event-date must be YYYY-MM-DD"),
            ("foundation", ("history-events", 0, "event-name"), "history-events[0].event-name must be 5-100 chars"),
            ("foundation", ("history-events", 0, "event-description"), "history-events[0].event-description must be at least 50 chars"),
            ("production", ("matcha-content",), "matcha-content must be a non-empty string"),
            ("production", ("harvest-location",), "harvest-location must be a non-empty string"),
            ("contact", ("contact", 0, "canal-type", 0), "contact[0].canal-type must contain exactly one taxonomy slug"),
            ("contact", ("contact", 0, "canal-value"), "contact[0].canal-value must be a non-empty string"),
            ("contact", ("location", "address"), "location.address must be a string or null"),
            ("faq", ("faq", 0, "question"), "faq[0].question must be 10-160 chars and end with ?"),
            ("faq", ("faq", 0, "answer"), "faq[0].answer must be at least 50 chars"),
        ]
        for lane, path_parts, expected_error in scalar_cases:
            invalid = copy.deepcopy(data[lane])
            target = invalid
            for part in path_parts[:-1]:
                target = target[part]
            target[path_parts[-1]] = 1
            write(paths[lane], invalid)
            field = ".".join(str(part) for part in path_parts)
            expect_rejected_with(
                invoke("--lane", lane, str(paths[lane])),
                f"non-string {lane}.{field}",
                expected_error,
            )
            write(paths[lane], data[lane])

        output = root / "merged.json"
        merge_args = [str(paths[lane]) for lane in ("foundation", "production", "contact", "faq")]
        expect_ok(invoke("--merge", *merge_args, "--brand-name", "Brand", "--output", str(output)), "valid merge")
        expect_ok(invoke("--brand-name", "Brand", str(output)), "merged validation")
        merged = json.loads(output.read_text(encoding="utf-8"))
        expected_order = [
            "title", "url_slug", "metadescription", "tagline", "history-content", "history-events",
            "matcha-content", "harvest-location", "contact", "location", "faq",
        ]
        if list(merged) != expected_order:
            raise AssertionError(f"merge order drifted: {list(merged)}")
        if merged["faq"] != data["faq"]["faq"] or merged["contact"] != data["contact"]["contact"]:
            raise AssertionError("merge rewrote lane-owned values")

        extra = dict(data["foundation"], unexpected="no")
        write(paths["foundation"], extra)
        expect_rejected(invoke("--lane", "foundation", str(paths["foundation"])), "unexpected lane field")
        write(paths["foundation"], data["foundation"])

        mismatched = dict(data["contact"], title="Other Brand")
        write(paths["contact"], mismatched)
        expect_rejected(invoke("--merge", *merge_args, "--brand-name", "Brand"), "mismatched lane title")
        write(paths["contact"], data["contact"])

        bad_shape = dict(data["contact"], location="Uji, Kyoto, Japan")
        write(paths["contact"], bad_shape)
        expect_rejected(invoke("--lane", "contact", str(paths["contact"])), "legacy flat location shape")
        write(paths["contact"], data["contact"])

        faq_answer = data["faq"]["faq"][0]["answer"]
        bad_faq_shape = dict(data["faq"], faq=[{"faq-question": "Legacy question?", "faq-answer": faq_answer}] * 4)
        write(paths["faq"], bad_faq_shape)
        expect_rejected(invoke("--lane", "faq", str(paths["faq"])), "legacy FAQ child keys")
        write(paths["faq"], data["faq"])

        bad_html = dict(data["production"], **{"matcha-content": data["production"]["matcha-content"] + '<p><a href="https://source.test">Source</a></p>'})
        write(paths["production"], bad_html)
        expect_rejected(invoke("--lane", "production", str(paths["production"])), "external link without nofollow")

        bad_tagline = dict(data["foundation"], tagline="Documented family craft from Uji")
        write(paths["foundation"], bad_tagline)
        expect_rejected(invoke("--lane", "foundation", str(paths["foundation"])), "tagline without matcha")

        unsafe_slug = dict(data["foundation"], url_slug="crew")
        write(paths["foundation"], unsafe_slug)
        expect_rejected(invoke("--lane", "foundation", "--brand-name", "Matcha Crew", str(paths["foundation"])), "generic-identity slug stripping")

        bad_markup = dict(data["production"], **{"matcha-content": data["production"]["matcha-content"] + '<div class="promo">Copy</div>'})
        write(paths["production"], bad_markup)
        expect_rejected(invoke("--lane", "production", str(paths["production"])), "unsupported HTML")

        bad_japanese = dict(data["production"], **{"matcha-content": data["production"]["matcha-content"] + "<p>Tencha is used.</p>"})
        write(paths["production"], bad_japanese)
        expect_rejected(invoke("--lane", "production", str(paths["production"])), "untranslated Japanese term")

        banned = dict(data["production"], **{"matcha-content": data["production"]["matcha-content"] + "<p>Premium matcha.</p>"})
        write(paths["production"], banned)
        expect_rejected(invoke("--lane", "production", str(paths["production"])), "banned phrase")

        generic_attribution = dict(data["foundation"], **{
            "history-content": data["foundation"]["history-content"]
            + "<p>The organization says its milling practice has remained unchanged.</p>",
        })
        write(paths["foundation"], generic_attribution)
        expect_rejected_with(
            invoke("--lane", "foundation", str(paths["foundation"])),
            "generic organization attribution",
            "generic source-attribution scaffolding",
        )

        automated_profile = dict(data["faq"], faq=[
            dict(data["faq"]["faq"][0], answer="<p>Based on the provided research, this option is intended for whisked tea and is sold in a 30 g tin.</p>"),
            *data["faq"]["faq"][1:],
        ])
        write(paths["faq"], automated_profile)
        expect_rejected_with(
            invoke("--lane", "faq", str(paths["faq"])),
            "automated FAQ scaffolding",
            "automated-profile scaffolding",
        )

        automated_tagline = dict(data["foundation"], tagline="Based on provided research, Brand matcha craft")
        write(paths["foundation"], automated_tagline)
        expect_rejected_with(
            invoke("--lane", "foundation", str(paths["foundation"])),
            "automated tagline scaffolding",
            "automated-profile scaffolding",
        )

        generic_faq_question = dict(data["faq"], faq=[
            dict(data["faq"]["faq"][0], question="What does the brand say about whisked matcha?"),
            *data["faq"]["faq"][1:],
        ])
        write(paths["faq"], generic_faq_question)
        expect_rejected_with(
            invoke("--lane", "faq", str(paths["faq"])),
            "generic attribution in FAQ question",
            "generic source-attribution scaffolding",
        )

        named_attribution = dict(data["production"], **{
            "harvest-location": data["production"]["harvest-location"]
            + "<p>Brand's 2024 sourcing report states that the documented harvest came from Uji.</p>",
        })
        write(paths["production"], named_attribution)
        expect_ok(
            invoke("--lane", "production", str(paths["production"])),
            "necessary attribution to a named source",
        )

        write(paths["foundation"], data["foundation"])
        write(paths["faq"], data["faq"])
        write(paths["production"], data["production"])
        expect_rejected(
            invoke("--merge", *merge_args, "--brand-name", "Brand", "--required-term", "Exact Product 40 g"),
            "missing exact evidence term",
        )

        duplicate_contact_type = dict(data["contact"], contact=[
            {"canal-type": ["phone"], "canal-value": "+371 1111 1111"},
            {"canal-type": ["phone"], "canal-value": "+371 2222 2222"},
        ])
        write(paths["contact"], duplicate_contact_type)
        expect_ok(invoke("--lane", "contact", str(paths["contact"])), "multiple verified values for one contact taxonomy")

    print("Organization profile validator tests OK (CLI help/errors, strict scalar types, deterministic merge, editorial and validation rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
