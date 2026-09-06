#!/usr/bin/env python3
"""Validate or deterministically merge a matcha Organization profile. Stdlib only."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CONTACT_TYPES = {
    "email", "facebook", "google-maps", "instagram", "linkedin", "phone", "pinterest",
    "reviewsio", "shopify", "telegram", "tiktok", "trustpilot", "twitter", "website",
    "wechat", "whatsapp", "youtube",
}
LANE_FIELDS = {
    "foundation": {"title", "url_slug", "metadescription", "tagline", "history-content", "history-events"},
    "production": {"title", "matcha-content", "harvest-location"},
    "contact": {"title", "contact", "location"},
    "faq": {"title", "faq"},
}
PROFILE_FIELDS = set().union(*LANE_FIELDS.values())
LANE_ORDER = ("foundation", "production", "contact", "faq")
MERGE_FIELDS = {
    "foundation": ("url_slug", "metadescription", "tagline", "history-content", "history-events"),
    "production": ("matcha-content", "harvest-location"),
    "contact": ("contact", "location"),
    "faq": ("faq",),
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
FORBIDDEN_HTML = re.compile(r"<(?:/?(?:h1|h2|div)\b|[^>]+\b(?:class|style)\s*=)", re.I)
HTML_TAG = re.compile(r"</?\s*([a-z][a-z0-9]*)\b", re.I)
EXTERNAL_LINK = re.compile(r"<a\s+[^>]*href=[\"']https?://[^\"']+[\"'][^>]*>", re.I)
NOFOLLOW = re.compile(r"\brel=[\"'][^\"']*\bnofollow\b[^\"']*[\"']", re.I)
HTML_FIELDS = {"history-content", "matcha-content", "harvest-location"}
BANNED_PHRASES = {
    "committed to excellence", "finest quality", "nestled in", "passionate about",
    "expert", "premium", "renowned for", "strategic", "time-honored",
}
GENERIC_SOURCE = r"(?:organization|organisation|brand|company|business|official\s+(?:website|site)|website|site)"
GENERIC_ATTRIBUTION = re.compile(
    rf"\b(?:according\s+to\s+(?:the\s+|this\s+|its\s+)?{GENERIC_SOURCE}|"
    rf"(?:the\s+|this\s+|its\s+){GENERIC_SOURCE}\s+"
    r"(?:says?|states?|claims?|notes?|explains?|reports?|mentions?|describes?|lists?|"
    r"identifies?|confirms?|indicates?))\b",
    re.I,
)
AUTOMATION_SCAFFOLDING = re.compile(
    r"\b(?:based\s+on\s+(?:the\s+)?(?:provided|supplied)\s+(?:research|information)|"
    r"(?:the\s+)?(?:provided|supplied|available)\s+(?:research|information)\s+"
    r"(?:says?|states?|shows?|indicates?|notes?)|this\s+profile\s+(?:shows?|lists?|covers?))\b",
    re.I,
)
ALLOWED_HTML_TAGS = {"a", "em", "h3", "h4", "li", "ol", "p", "strong", "ul"}
JAPANESE_TERMS = {
    "bancha", "chasen", "chawan", "genmaicha", "gyokuro", "hojicha", "kabusecha",
    "koicha", "okumidori", "samidori", "sencha", "tencha", "usucha", "yabukita",
}


def add(errors: list[str], message: str) -> None:
    errors.append(message)


def require_exact_fields(data: dict[str, Any], fields: set[str], errors: list[str]) -> None:
    for field in sorted(fields - set(data)):
        add(errors, f"missing required field: {field}")
    for field in sorted(set(data) - fields):
        add(errors, f"unexpected field: {field}")


def string(data: dict[str, Any], name: str, errors: list[str], allow_empty: bool = False) -> str | None:
    value = data.get(name)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        add(errors, f"{name} must be {'a string' if allow_empty else 'a non-empty string'}")
        return None
    return value


def validate_banned_phrases(name: str, value: str, errors: list[str]) -> None:
    lowered = value.lower()
    for phrase in sorted(BANNED_PHRASES):
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            add(errors, f"{name} contains banned phrase: {phrase}")


def validate_editorial_voice(name: str, value: str, errors: list[str]) -> None:
    if match := GENERIC_ATTRIBUTION.search(value):
        add(errors, f"{name} contains generic source-attribution scaffolding: {match.group(0)}")
    if match := AUTOMATION_SCAFFOLDING.search(value):
        add(errors, f"{name} contains automated-profile scaffolding: {match.group(0)}")


def validate_html(name: str, value: str, errors: list[str]) -> None:
    if FORBIDDEN_HTML.search(value):
        add(errors, f"{name} contains forbidden h1, h2, div, class, or style markup")
    for link in EXTERNAL_LINK.findall(value):
        if not NOFOLLOW.search(link):
            add(errors, f"{name} has an external link without rel=\"nofollow\"")
    unsupported = sorted({tag.lower() for tag in HTML_TAG.findall(value)} - ALLOWED_HTML_TAGS)
    if unsupported:
        add(errors, f"{name} contains unsupported HTML tag(s): {', '.join(unsupported)}")
    for term in sorted(JAPANESE_TERMS):
        if not re.search(rf"\b{term}\b", value, re.I):
            continue
        without_valid_uses = re.sub(
            rf"<em>\s*{term}\s*</em>\s*\([^)]+\)", "", value, flags=re.I,
        )
        if re.search(rf"\b{term}\b", without_valid_uses, re.I):
            add(errors, f"{name} must format {term} as <em>{term}</em> (translation)")
    validate_banned_phrases(name, value, errors)
    validate_editorial_voice(name, value, errors)


def validate_foundation(data: dict[str, Any], errors: list[str], brand_name: str | None) -> None:
    slug = string(data, "url_slug", errors)
    if slug and not (2 <= len(slug) <= 50 and SLUG_RE.fullmatch(slug)):
        add(errors, "url_slug must be 2-50 lowercase alphanumeric/hyphen characters")
    meta = string(data, "metadescription", errors)
    if meta and not 150 <= len(meta) <= 160:
        add(errors, f"metadescription must be 150-160 chars, got {len(meta)}")
    elif meta:
        validate_banned_phrases("metadescription", meta, errors)
        validate_editorial_voice("metadescription", meta, errors)
        if brand_name and brand_name.lower() not in meta.lower():
            add(errors, "metadescription must include the exact brand name")
    tagline = string(data, "tagline", errors)
    if tagline and not 15 <= len(tagline) <= 80:
        add(errors, f"tagline must be 15-80 chars, got {len(tagline)}")
    elif tagline and not 5 <= len(tagline.split()) <= 10:
        add(errors, f"tagline must be 5-10 words, got {len(tagline.split())}")
    elif tagline:
        validate_banned_phrases("tagline", tagline, errors)
        validate_editorial_voice("tagline", tagline, errors)
        if not re.search(r"\bmatcha\b", tagline, re.I):
            add(errors, "tagline must include the word matcha")
    history = string(data, "history-content", errors)
    if history:
        if len(history) < 200:
            add(errors, f"history-content must be at least 200 chars, got {len(history)}")
        validate_html("history-content", history, errors)
    events = data.get("history-events")
    if not isinstance(events, list):
        add(errors, "history-events must be an array")
        return
    if not 2 <= len(events) <= 10:
        add(errors, f"history-events needs 2-10 items, got {len(events)}")
    previous = ""
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            add(errors, f"history-events[{index}] must be an object")
            continue
        require_exact_fields(event, {"event-date", "event-name", "event-description"}, errors)
        date = event.get("event-date")
        if not isinstance(date, str) or not DATE_RE.fullmatch(date):
            add(errors, f"history-events[{index}].event-date must be YYYY-MM-DD")
        elif previous and date < previous:
            add(errors, "history-events must be chronological")
        else:
            previous = date
        name = event.get("event-name")
        if not isinstance(name, str) or not 5 <= len(name) <= 100:
            add(errors, f"history-events[{index}].event-name must be 5-100 chars")
        description = event.get("event-description")
        if not isinstance(description, str) or len(description) < 50:
            add(errors, f"history-events[{index}].event-description must be at least 50 chars")
        elif isinstance(description, str):
            validate_editorial_voice(f"history-events[{index}].event-description", description, errors)


def validate_production(data: dict[str, Any], errors: list[str]) -> None:
    for name, minimum in (("matcha-content", 200), ("harvest-location", 150)):
        value = string(data, name, errors)
        if value:
            if len(value) < minimum:
                add(errors, f"{name} must be at least {minimum} chars, got {len(value)}")
            validate_html(name, value, errors)


def validate_contact(data: dict[str, Any], errors: list[str]) -> None:
    location = data.get("location")
    if not isinstance(location, dict):
        add(errors, "location must be a Brand location object")
    else:
        require_exact_fields(location, {"address", "map_picker", "latitude", "longitude"}, errors)
        address = location.get("address")
        if address is not None and not isinstance(address, str):
            add(errors, "location.address must be a string or null")
        if location.get("map_picker") not in (False, None):
            add(errors, "location.map_picker must be false or null in generated profiles")
        for coordinate, minimum, maximum in (("latitude", -90, 90), ("longitude", -180, 180)):
            value = location.get(coordinate)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                add(errors, f"location.{coordinate} must be a number or null")
            elif value is not None and not minimum <= value <= maximum:
                add(errors, f"location.{coordinate} must be between {minimum} and {maximum}")
    contacts = data.get("contact")
    if not isinstance(contacts, list):
        add(errors, "contact must be an array")
        return
    for index, contact in enumerate(contacts):
        if not isinstance(contact, dict):
            add(errors, f"contact[{index}] must be an object")
            continue
        require_exact_fields(contact, {"canal-type", "canal-value"}, errors)
        kinds, value = contact.get("canal-type"), contact.get("canal-value")
        if not isinstance(kinds, list) or len(kinds) != 1 or not isinstance(kinds[0], str):
            add(errors, f"contact[{index}].canal-type must contain exactly one taxonomy slug")
            kind = None
        else:
            kind = kinds[0]
        if kind not in CONTACT_TYPES:
            add(errors, f"contact[{index}].canal-type is invalid: {kind!r}")
        if not isinstance(value, str) or not value.strip():
            add(errors, f"contact[{index}].canal-value must be a non-empty string")
        if kind in CONTACT_TYPES - {"email", "phone", "wechat", "whatsapp"} and isinstance(value, str) and not re.match(r"^https://", value):
            add(errors, f"contact[{index}].canal-value must be a full https:// URL")


def validate_faq(data: dict[str, Any], errors: list[str]) -> None:
    faq = data.get("faq")
    if not isinstance(faq, list):
        add(errors, "faq must be an array")
        return
    if not 4 <= len(faq) <= 6:
        add(errors, f"faq needs 4-6 pairs, got {len(faq)}")
    for index, row in enumerate(faq):
        if not isinstance(row, dict):
            add(errors, f"faq[{index}] must be an object")
            continue
        require_exact_fields(row, {"question", "answer"}, errors)
        question, answer = row.get("question"), row.get("answer")
        if not isinstance(question, str) or not 10 <= len(question) <= 160 or not question.endswith("?"):
            add(errors, f"faq[{index}].question must be 10-160 chars and end with ?")
        elif isinstance(question, str):
            validate_editorial_voice(f"faq[{index}].question", question, errors)
        if not isinstance(answer, str) or len(answer) < 50:
            add(errors, f"faq[{index}].answer must be at least 50 chars")
        elif isinstance(answer, str):
            validate_html(f"faq[{index}].answer", answer, errors)


def validate(data: Any, lane: str | None, brand_name: str | None, required_terms: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]
    fields = LANE_FIELDS[lane] if lane else PROFILE_FIELDS
    require_exact_fields(data, fields, errors)
    title = string(data, "title", errors)
    if title and brand_name and title != brand_name:
        add(errors, f"title must exactly equal brand name {brand_name!r}")
    lanes = [lane] if lane else list(LANE_FIELDS)
    if "foundation" in lanes:
        validate_foundation(data, errors, brand_name)
    if "production" in lanes:
        validate_production(data, errors)
    if "contact" in lanes:
        validate_contact(data, errors)
    if "faq" in lanes:
        validate_faq(data, errors)
    searchable = json.dumps(data, ensure_ascii=False).casefold()
    for term in required_terms or []:
        if term.casefold() not in searchable:
            add(errors, f"required evidence term is missing: {term!r}")
    return errors


def merge_lanes(paths: list[Path], brand_name: str | None, required_terms: list[str]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if len(paths) != len(LANE_ORDER):
        return None, [f"--merge requires {len(LANE_ORDER)} files in this order: {', '.join(LANE_ORDER)}"]
    lane_data: dict[str, dict[str, Any]] = {}
    for lane, path in zip(LANE_ORDER, paths):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{lane}: cannot read JSON: {error}")
            continue
        lane_errors = validate(data, lane, brand_name)
        errors.extend(f"{lane}: {error}" for error in lane_errors)
        if isinstance(data, dict):
            lane_data[lane] = data
    if errors:
        return None, errors
    titles = {lane_data[lane]["title"] for lane in LANE_ORDER}
    if len(titles) != 1:
        return None, ["all lane titles must match exactly"]
    merged: dict[str, Any] = {"title": lane_data["foundation"]["title"]}
    for lane in LANE_ORDER:
        for field in MERGE_FIELDS[lane]:
            merged[field] = lane_data[lane][field]
    errors.extend(validate(merged, None, brand_name, required_terms))
    return (None, errors) if errors else (merged, [])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Organization profile JSON lane or merge four validated lane files.",
    )
    parser.add_argument("file", type=Path, nargs="?", help="profile JSON file to validate")
    parser.add_argument("--lane", choices=sorted(LANE_FIELDS), help="validate one lane instead of a merged profile")
    parser.add_argument("--brand-name", help="require title and metadata to use this exact brand name")
    parser.add_argument("--required-term", action="append", default=[], help="exact evidence-backed term that must survive in the output")
    parser.add_argument(
        "--merge",
        nargs=4,
        type=Path,
        metavar=tuple(LANE_ORDER),
        help="merge foundation, production, contact, and FAQ lane JSON files in that order",
    )
    parser.add_argument("--output", type=Path, help="write a merged profile to this path instead of stdout")
    args = parser.parse_args()
    if args.merge:
        merged, errors = merge_lanes(args.merge, args.brand_name, args.required_term)
        if errors:
            print(f"INVALID - {len(errors)} problem(s):")
            for error in errors:
                print(f"  - {error}")
            return 1
        assert merged is not None
        payload = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
            print(f"OK - merged profile is valid: {args.output}")
        else:
            print(payload, end="")
        return 0
    if args.file is None:
        parser.error("file is required unless --merge is used")
    try:
        data = json.loads(args.file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"INVALID - cannot read JSON: {error}")
        return 1
    errors = validate(data, args.lane, args.brand_name, args.required_term)
    if errors:
        print(f"INVALID - {len(errors)} problem(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"OK - {args.lane or 'merged'} profile is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
