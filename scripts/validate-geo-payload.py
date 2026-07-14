#!/usr/bin/env python3
"""Validate geo content JSON payloads; emit one deterministic JSON report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Policy edits belong here; no validation logic change needed.
FORBIDDEN_URLS = ('example.com', 'localhost', '127.0.0.1', 'bit.ly/')
RISKY_CLAIM_PHRASES = ('best in', '#1', 'number one', 'guaranteed', '100% guaranteed', 'award-winning')
TEXT_FIELDS = ('h1', 'hook', 'excerpt', 'description')
SIMILARITY_LIMIT = 0.88
KNOWN_CITIES = ('Toulouse', 'Lyon')


def words(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value, re.UNICODE))


def normalize(value: str, cities: set[str]) -> str:
    for city in cities:
        value = re.sub(rf'\b{re.escape(city)}\b', '<city>', value, flags=re.IGNORECASE)
    return re.sub(r'[^\w]+', ' ', value.casefold()).strip()


def url_ok(value: Any) -> bool:
    parsed = urlparse(value) if isinstance(value, str) else None
    return bool(parsed and parsed.scheme in {'http', 'https'} and parsed.netloc)


def issue(findings: list[dict[str, str]], path: Path, field: str, message: str) -> None:
    findings.append({'file': str(path), 'field': field, 'message': message})


def source_ids(value: Any) -> set[str] | None:
    if isinstance(value, dict):
        return set(value)
    if isinstance(value, list):
        return {row['id'] for row in value if isinstance(row, dict) and isinstance(row.get('id'), str)} | {row for row in value if isinstance(row, str)}
    return None


def city_for(data: dict[str, Any]) -> str | None:
    if isinstance(data.get('city'), str) and data['city'].strip():
        return data['city'].strip()
    fields = data.get('fields', {})
    text = ' '.join(str(data.get(key, '')) for key in ('title', 'h1')) + ' ' + str(fields.get('h1', ''))
    return next((city for city in KNOWN_CITIES if re.search(rf'\b{city}\b', text, re.IGNORECASE)), None)


def family_for(data: dict[str, Any], city: str | None) -> str | None:
    title = data.get('title') or (data.get('fields') or {}).get('h1') or data.get('h1')
    if not isinstance(title, str):
        return None
    return normalize(title.split(':', 1)[0], {city} if city else set()) or None


def payload(data: dict[str, Any]) -> dict[str, Any]:
    fields = data.get('fields') if isinstance(data.get('fields'), dict) else {}
    return {
        'id': data.get('id'), 'city': city_for(data), 'h1': data.get('h1', fields.get('h1')),
        'hook': data.get('hook', fields.get('hook')), 'excerpt': data.get('excerpt', data.get('post_excerpt')),
        'description': data.get('description', fields.get('description')), 'faq': data.get('faq', fields.get('faq')),
        'timeline': data.get('timeline', fields.get('conversion-timeline')),
        'qualities': data.get('qualities', fields.get('conversion-qualities')),
        'sources': data.get('sources', fields.get('sources')), 'source_index': data.get('source_index'),
        'evidence': data.get('evidence'), 'evidence_ids': data.get('evidence_ids'), 'evidence_map': data.get('evidence_map'),
    }


def validate(path: Path) -> tuple[dict[str, Any], list[dict[str, str]], dict[str, Any] | None]:
    report = {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    findings: list[dict[str, str]] = []
    try:
        raw = json.loads(path.read_text())
    except Exception as exc:
        issue(findings, path, '$', f'invalid JSON: {exc}')
        return report, findings, None
    if not isinstance(raw, dict):
        issue(findings, path, '$', 'must be object')
        return report, findings, None
    data = payload(raw)
    if not isinstance(data['id'], (str, int)) or isinstance(data['id'], bool) or not str(data['id']).strip():
        issue(findings, path, 'id', 'must be non-empty string or numeric ID')
    if not data['city']:
        issue(findings, path, 'city', 'required or inferable from title/h1')
    for field in TEXT_FIELDS:
        if not isinstance(data[field], str):
            issue(findings, path, field, 'required string')
    for field, low, high, unit in (('h1', 20, 70, 'characters'), ('hook', 35, 120, 'characters'), ('excerpt', 120, 160, 'characters'), ('description', 700, 1100, 'words')):
        value = data[field]
        count = words(value) if field == 'description' and isinstance(value, str) else len(value) if isinstance(value, str) else None
        if count is not None and not low <= count <= high:
            issue(findings, path, field, f'must be {low}-{high} {unit}')
    for field, size, exact in (('faq', 4, False), ('timeline', 4, True), ('qualities', 3, True)):
        if not isinstance(data[field], list) or (len(data[field]) != size if exact else len(data[field]) < size):
            issue(findings, path, field, f'must contain {"exactly" if exact else "at least"} {size} rows')
    index = source_ids(data['source_index'])
    if data['source_index'] is not None and index is None:
        issue(findings, path, 'source_index', 'must be object or array')
    sources = data['sources']
    if not isinstance(sources, list):
        issue(findings, path, 'sources', 'required array')
    else:
        urls: set[str] = set()
        ids: set[str] = set()
        for number, source in enumerate(sources):
            if not isinstance(source, dict) or not isinstance(source.get('url'), str):
                issue(findings, path, f'sources[{number}]', 'must contain url string')
                continue
            url, source_id = source['url'], source.get('id')
            if not url_ok(url): issue(findings, path, f'sources[{number}].url', 'invalid URL')
            if url in urls: issue(findings, path, f'sources[{number}].url', 'duplicate URL')
            if any(token in url.casefold() for token in FORBIDDEN_URLS): issue(findings, path, f'sources[{number}].url', 'forbidden stale/dead URL')
            urls.add(url)
            if source_id is not None:
                if not isinstance(source_id, str): issue(findings, path, f'sources[{number}].id', 'must be string')
                elif source_id in ids: issue(findings, path, f'sources[{number}].id', 'duplicate source ID')
                else: ids.add(source_id)
                if index is not None and source_id not in index: issue(findings, path, f'sources[{number}].id', 'absent from source_index')
    for field in TEXT_FIELDS:
        if isinstance(data[field], str) and any(phrase in data[field].casefold() for phrase in RISKY_CLAIM_PHRASES):
            issue(findings, path, field, 'risky claim phrase')
    if data['evidence'] is not None:
        if not isinstance(data['evidence'], list): issue(findings, path, 'evidence', 'must be array')
        elif index is not None:
            for number, row in enumerate(data['evidence']):
                if not isinstance(row, dict) or row.get('source_id') not in index: issue(findings, path, f'evidence[{number}].source_id', 'absent from source_index')
    return report, findings, {**data, 'family': family_for(raw, data['city'])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    reports, findings, rows = [], [], []
    for path in args.files:
        if not path.is_file():
            findings.append({'file': str(path), 'field': '$', 'message': 'not a file'})
            continue
        report, current, data = validate(path)
        reports.append(report); findings.extend(current)
        if data is not None: rows.append((path, data))
    cities = {data['city'] for _, data in rows if data['city']}
    for left, (left_path, left_data) in enumerate(rows):
        for right_path, right_data in rows[left + 1:]:
            if not left_data['family'] or left_data['family'] != right_data['family']:
                continue
            left_text = ' '.join(str(left_data[field] or '') for field in TEXT_FIELDS)
            right_text = ' '.join(str(right_data[field] or '') for field in TEXT_FIELDS)
            score = SequenceMatcher(None, normalize(left_text, cities), normalize(right_text, cities)).ratio()
            if score >= SIMILARITY_LIMIT:
                findings.append({'file': f'{left_path}|{right_path}', 'field': 'sibling_similarity', 'message': f'normalized city-swap similarity {score:.3f} >= {SIMILARITY_LIMIT:.2f}'})
    print(json.dumps({'valid': not findings, 'inputs': reports, 'findings': findings}, ensure_ascii=False, sort_keys=True))
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
