#!/usr/bin/env python3
"""Derive and validate one field-metadata run from immutable artifacts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "references/voxel/field-metadata-contract.json"
ERRORS: list[str] = []
UPPER_LIMITS = {"maxlength", "max", "max-count", "max-size", "max_count", "max_date_count"}
LOWER_LIMITS = {"minlength", "min"}
NUMERIC_LIMITS = UPPER_LIMITS | LOWER_LIMITS | {"step"}


def fail(message: str) -> None:
    ERRORS.append(message)


def load_json(path: Path, name: str | None = None) -> Any:
    try:
        value = json.loads(path.read_text())
        if isinstance(value, str):
            value = json.loads(value)
        return value
    except Exception as exc:
        fail(f"{name or path.name}: invalid JSON: {exc}")
        return None


def obj(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{name}: expected object")
        return {}
    return value


def array(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{name}: expected array")
        return []
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def canonical_hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def canonical_diff(before: Any, after: Any, before_name: str, after_name: str) -> str:
    return "".join(unified_diff(canonical_json(before).splitlines(keepends=True), canonical_json(after).splitlines(keepends=True), fromfile=before_name, tofile=after_name))


def exact_keys(value: dict[str, Any], expected: set[str], name: str) -> bool:
    if set(value) != expected:
        fail(f"{name}: keys must equal {sorted(expected)}")
        return False
    return True


def string_array(value: Any, name: str, *, nonempty: bool = False) -> list[Any]:
    rows = array(value, name)
    if (nonempty and not rows) or any(not isinstance(item, str) or not item for item in rows):
        fail(f"{name}: expected {'non-empty ' if nonempty else ''}string array")
    return rows


def scope_id(cpt: str, field_path: list[str]) -> str:
    return f"field-definition:{cpt}:{canonical_hash(field_path)}"


def mutation_id(scope: str, attribute: str) -> str:
    return f"{scope}:{attribute}"


def reject_repeated_options(argv: list[str]) -> None:
    for option in ("--phase", "--contract"):
        count = sum(argument == option or argument.startswith(f"{option}=") for argument in argv)
        if count > 1:
            raise SystemExit(f"duplicate option rejected: {option}")


def scalar_ok(attribute: str, value: Any) -> bool:
    if attribute in {"description", "placeholder", "pattern"}:
        return isinstance(value, str)
    if attribute in NUMERIC_LIMITS:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def artifact(run_dir: Path, raw: Any, name: str) -> Path | None:
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
        fail(f"{name}: artifact path must be non-empty relative string")
        return None
    candidate = run_dir / raw
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(run_dir.resolve(strict=True))
        metadata = os.stat(candidate, follow_symlinks=False)
    except (OSError, ValueError):
        fail(f"{name}: artifact must resolve inside run directory")
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        fail(f"{name}: artifact must be regular non-symlink single-link file")
        return None
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        fail(f"{name}: artifact must be current-user-owned and mode 0600 or stricter")
        return None
    return candidate


def validate_run_proof(run_dir: Path) -> None:
    proof_path = artifact(run_dir, "run.json", "run")
    if proof_path is None:
        return
    proof = obj(load_json(proof_path, "run"), "run")
    exact_keys(proof, {"version", "nonce", "created_at", "path", "site", "uid", "mode", "device", "inode"}, "run")
    try:
        created = datetime.fromisoformat(proof.get("created_at", "").replace("Z", "+00:00"))
    except (TypeError, ValueError):
        fail("run.created_at: invalid ISO-8601 timestamp")
        return
    metadata = os.stat(run_dir, follow_symlinks=False)
    fresh = created.tzinfo is not None and datetime.now(timezone.utc).timestamp() - created.timestamp() <= 86400 and created.timestamp() <= datetime.now(timezone.utc).timestamp() + 60
    valid = proof.get("version") == 1 and isinstance(proof.get("nonce"), str) and re.fullmatch(r"[0-9a-f]{32}", proof["nonce"]) is not None and proof.get("path") == str(run_dir.resolve()) and proof.get("uid") == os.getuid() == metadata.st_uid and proof.get("mode") == "0700" and stat.S_IMODE(metadata.st_mode) == 0o700 and proof.get("device") == metadata.st_dev and proof.get("inode") == metadata.st_ino and fresh
    if not valid:
        fail("run: identity, ownership, mode, nonce, or freshness proof mismatch")


def cpt_config(root: Any, cpt: str) -> dict[str, Any] | None:
    if not isinstance(root, dict):
        return None
    if isinstance(root.get(cpt), dict):
        return root[cpt]
    if isinstance(root.get("post_types"), dict) and isinstance(root["post_types"].get(cpt), dict):
        return root["post_types"][cpt]
    if root.get("key") == cpt and isinstance(root.get("fields"), list):
        return root
    if isinstance(root.get("fields"), list):
        return root
    return None


def resolve_field(config: dict[str, Any], field_path: list[str]) -> tuple[dict[str, Any] | None, list[Any]]:
    fields = config.get("fields")
    pointer: list[Any] = ["fields"]
    if not isinstance(fields, list):
        return None, pointer
    found: dict[str, Any] | None = None
    for depth, key in enumerate(field_path):
        matches = [(index, row) for index, row in enumerate(fields) if isinstance(row, dict) and row.get("key") == key]
        if len(matches) != 1:
            return None, pointer
        index, found = matches[0]
        pointer.extend([index])
        if depth < len(field_path) - 1:
            fields = found.get("fields")
            pointer.append("fields")
            if not isinstance(fields, list):
                return None, pointer
    return found, pointer


def derive_inventory(option: Any, cpts: set[str], types: dict[str, Any], rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    metadata = {"description", "placeholder", "minlength", "maxlength", "min", "max", "step", "max-count", "max-size", "max_count", "max_date_count", "pattern"}
    skip_types = set(rules.get("skip_types", []))
    skip_keys = set(rules.get("skip_keys", []))

    def walk(cpt: str, fields: Any, prefix: list[str]) -> None:
        if not isinstance(fields, list):
            fail(f"baseline {cpt}:{prefix}: fields must be array")
            return
        sibling_keys = [row.get("key") for row in fields if isinstance(row, dict)]
        duplicates = {key for key in sibling_keys if key is not None and sibling_keys.count(key) > 1}
        if duplicates:
            fail(f"baseline {cpt}:{prefix}: duplicate keys {sorted(duplicates)}")
        for row in fields:
            if not isinstance(row, dict) or not isinstance(row.get("key"), str) or not isinstance(row.get("type"), str):
                fail(f"baseline {cpt}:{prefix}: malformed field row")
                continue
            path = prefix + [row["key"]]
            sid = scope_id(cpt, path)
            if row["type"] not in types:
                fail(f"baseline {cpt}:{path}: unknown field type {row['type']}")
                continue
            excluded = row["type"] in skip_types or row["key"] in skip_keys
            rows[sid] = {
                "scope_id": sid,
                "cpt": cpt,
                "field_path": path,
                "key": row["key"],
                "type": row["type"],
                "label": row.get("label", ""),
                "current": {key: row[key] for key in metadata if key in row},
                "excluded": excluded,
                "overrides_debt": bool(row.get("overrides")),
            }
            if row.get("type") == "repeater":
                walk(cpt, row.get("fields", []), path)

    for cpt in sorted(cpts):
        config = cpt_config(option, cpt)
        if config is None:
            fail(f"baseline option missing CPT {cpt}")
            continue
        walk(cpt, config.get("fields"), [])
    return rows


def required_for(row: dict[str, Any], type_policy: dict[str, Any]) -> list[str]:
    required: list[str] = []
    if type_policy.get("description") == "required":
        required.append("description")
    if type_policy.get("placeholder") == "required":
        required.append("placeholder")
    return required


def supported_for(type_policy: dict[str, Any]) -> list[str]:
    supported = ["description"] if type_policy.get("description") != "unsupported" else []
    if type_policy.get("placeholder") != "unsupported":
        supported.append("placeholder")
    supported.extend(type_policy.get("limit_keys", []))
    return supported


def compare_inventory(supplied: list[Any], derived: dict[str, dict[str, Any]]) -> None:
    supplied_by_scope: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(supplied):
        row = obj(raw, f"inventory[{index}]")
        exact_keys(row, {"scope_id", "cpt", "field_path", "key", "type", "label", "current", "excluded", "overrides_debt"}, f"inventory[{index}]")
        cpt, path = row.get("cpt"), row.get("field_path")
        if not isinstance(cpt, str) or not isinstance(path, list) or not path or not all(isinstance(item, str) for item in path):
            fail(f"inventory[{index}]: invalid cpt/field_path")
            continue
        sid = scope_id(cpt, path)
        if sid in supplied_by_scope:
            fail(f"inventory: duplicate scope {sid}")
        supplied_by_scope[sid] = row
        expected = derived.get(sid)
        if expected is None:
            fail(f"inventory[{index}]: path absent from baseline")
        elif row != expected:
            fail(f"inventory[{index}]: row differs from canonical baseline inventory")
    if set(supplied_by_scope) != set(derived):
        fail("inventory: scope set differs from recursive baseline derivation")


def validate_journal_row(row: dict[str, Any], name: str, mutation: tuple[str, str, Any], candidates: dict[str, dict[str, Any]], expected_status: str, site: str, before: Any) -> None:
    exact_keys(row, {"mutation_id", "status", "writer", "argv"}, name)
    sid, attribute, value = mutation
    output = candidates[sid]["output"]
    nested = len(output["field_path"]) > 1
    writer = "voxel:settings set" if nested else "voxel:field-schema"
    argv = row.get("argv")
    if row.get("status") != expected_status or row.get("writer") != writer or not isinstance(argv, list) or any(not isinstance(item, str) or not item for item in argv):
        fail(f"{name}: status/writer/argv mismatch")
        return
    scalar = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if nested:
        config = cpt_config(before, output["cpt"])
        _, pointer = resolve_field(config or {}, output["field_path"])
        path = "/".join([output["cpt"], *[str(part) for part in pointer], attribute])
        expected_argv = ["wpdev", "voxel:settings", site, "set", path, f"--value={scalar}", "--dry" if expected_status == "pass" else "--yes"]
    else:
        expected_argv = ["wpdev", "voxel:field-schema", site, f"--key={output['field_key']}", f"--cpts={output['cpt']}", "--no-insert-if-missing", f"--patch={json.dumps({attribute: value}, ensure_ascii=False, separators=(',', ':'))}"]
        if expected_status == "pass":
            expected_argv.append("--dry-run")
    if argv != expected_argv:
        fail(f"{name}: argv must exactly equal derived depth-specific invocation")


def apply_manifest(option: Any, candidates: dict[str, dict[str, Any]], cpts: set[str] | None = None) -> Any:
    result = copy.deepcopy(option)
    for sid in sorted(candidates):
        env = candidates[sid]
        output = env["output"]
        cpt = output["cpt"]
        if cpts is not None and cpt not in cpts:
            continue
        config = cpt_config(result, cpt)
        field, _ = resolve_field(config or {}, output["field_path"])
        if field is None:
            fail(f"manifest target missing during apply: {sid}")
            continue
        field.update(output["patch"])
    return result


def main() -> int:
    reject_repeated_options(sys.argv[1:])
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--phase", choices=("prewrite", "final"), required=True)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    run_dir = args.run_dir

    if not run_dir.exists() or not run_dir.is_dir() or run_dir.is_symlink():
        fail("run directory must be existing non-symlink directory")
    else:
        if stat.S_IMODE(run_dir.stat().st_mode) != 0o700:
            fail("run directory mode must be 0700")
        if run_dir.stat().st_uid != os.getuid():
            fail("run directory must be owned by current user")

    base_required = {"run.json", "before-option.json", "before-option.sha256", "before-db.sql", "source-owner.json", "inventory.json", "expected-scopes.json", "candidates.json", "validated.json"}
    final_required = {"dry-run.json", "apply.json", "after-option.json", "option.diff", "verification.json"}
    required = base_required | (final_required if args.phase == "final" else set())
    present = {path.name for path in run_dir.iterdir()} if run_dir.exists() and run_dir.is_dir() else set()
    for name in sorted(required - present):
        fail(f"missing artifact {name}")
    for path in run_dir.iterdir() if run_dir.exists() and run_dir.is_dir() else []:
        if path.is_symlink():
            fail(f"artifact must not be symlink: {path.name}")
        elif path.is_file():
            artifact(run_dir, path.name, f"artifact {path.name}")
    if run_dir.exists() and run_dir.is_dir():
        validate_run_proof(run_dir)

    contract = obj(load_json(args.contract, "contract"), "contract")
    types = obj(contract.get("types"), "contract.types")
    rules = obj(contract.get("system_rules"), "contract.system_rules")
    attributes = set(array(contract.get("attributes"), "contract.attributes"))

    run_proof = obj(load_json(run_dir / "run.json"), "run")
    site = run_proof.get("site") if isinstance(run_proof.get("site"), str) and run_proof.get("site") else ""
    if not site:
        fail("run.site: non-empty site identifier required")
    before_path = run_dir / "before-option.json"
    before = load_json(before_path) if before_path.exists() else {}
    hash_path = run_dir / "before-option.sha256"
    if before_path.exists() and hash_path.exists():
        recorded = hash_path.read_text().strip().split()[0] if hash_path.read_text().strip() else ""
        if hashlib.sha256(before_path.read_bytes()).hexdigest() != recorded:
            fail("before-option hash mismatch")

    owner_rows = array(load_json(run_dir / "source-owner.json"), "source-owner")
    owners: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(owner_rows):
        row = obj(raw, f"source-owner[{index}]")
        state = row.get("state")
        owner_schema = {"cpt", "state", "before_artifact", "after_artifact", "diff_artifact"} if state == "blueprint-managed" else {"cpt", "state", "debt"} if state == "runtime-only-debt" else {"cpt", "state"}
        exact_keys(row, owner_schema, f"source-owner[{index}]")
        cpt = row.get("cpt")
        if not isinstance(cpt, str) or state not in {"blueprint-managed", "runtime-only-debt", "not-applicable"}:
            fail(f"source-owner[{index}]: invalid cpt/state")
            continue
        if cpt in owners:
            fail(f"source-owner: duplicate CPT {cpt}")
        owners[cpt] = row
        if state == "runtime-only-debt" and not isinstance(row.get("debt"), str):
            fail(f"source-owner {cpt}: debt text required")
        if state == "blueprint-managed":
            before_art = artifact(run_dir, row.get("before_artifact"), f"source-owner {cpt}.before_artifact")
            if args.phase == "final":
                artifact(run_dir, row.get("after_artifact"), f"source-owner {cpt}.after_artifact")
                artifact(run_dir, row.get("diff_artifact"), f"source-owner {cpt}.diff_artifact")
            if before_art is None:
                fail(f"source-owner {cpt}: blueprint baseline unavailable")

    derived = derive_inventory(before, set(owners), types, rules)
    compare_inventory(array(load_json(run_dir / "inventory.json"), "inventory"), derived)

    expected_rows = array(load_json(run_dir / "expected-scopes.json"), "expected-scopes")
    expected: dict[str, dict[str, Any]] = {}
    derived_expected = {sid: row for sid, row in derived.items() if not row["excluded"]}
    for index, raw in enumerate(expected_rows):
        row = obj(raw, f"expected[{index}]")
        exact_keys(row, {"scope_id", "cpt", "field_path", "field_type", "required", "supported", "missing"}, f"expected[{index}]")
        cpt, path, sid = row.get("cpt"), row.get("field_path"), row.get("scope_id")
        if not isinstance(cpt, str) or not isinstance(path, list) or sid != scope_id(cpt, path):
            fail(f"expected[{index}]: canonical scope mismatch")
            continue
        source = derived_expected.get(sid)
        if source is None:
            fail(f"expected[{index}]: scope absent/excluded in baseline")
            continue
        policy = types[source["type"]]
        required = required_for(source, policy)
        supported = supported_for(policy)
        missing = [key for key in required if source["current"].get(key) in (None, "")]
        if row.get("field_type") != source["type"] or row.get("required") != required or row.get("supported") != supported or row.get("missing") != missing:
            fail(f"expected[{index}]: row not derived from contract/baseline")
        expected[sid] = row
    if set(expected) != set(derived_expected):
        fail("expected scope set differs from recursive baseline+contract derivation")

    candidate_rows = array(load_json(run_dir / "candidates.json"), "candidates")
    candidates: dict[str, dict[str, Any]] = {}
    envelope_keys = {"scope_id", "mode", "status", "evidence", "output", "open_questions"}
    output_keys = {"cpt", "field_path", "field_key", "field_type", "patch", "preserved", "tightening_evidence"}
    for index, raw in enumerate(candidate_rows):
        env = obj(raw, f"candidate[{index}]")
        if set(env) != envelope_keys:
            fail(f"candidate[{index}]: envelope keys mismatch")
        sid = env.get("scope_id")
        if sid not in expected or sid in candidates:
            fail(f"candidate[{index}]: unexpected/duplicate scope")
            continue
        candidates[sid] = env
        if env.get("mode") != "build-material" or env.get("status") != "ready":
            fail(f"candidate[{index}]: every expected scope must be ready")
        if string_array(env.get("open_questions"), f"candidate[{index}].open_questions"):
            fail(f"candidate[{index}]: ready candidate must have no open questions")
        evidence_rows = array(env.get("evidence"), f"candidate[{index}].evidence")
        for evidence_index, raw_evidence in enumerate(evidence_rows):
            evidence = obj(raw_evidence, f"candidate[{index}].evidence[{evidence_index}]")
            evidence_name = f"candidate[{index}].evidence[{evidence_index}]"
            exact_keys(evidence, {"claim", "artifact"}, evidence_name)
            claim = evidence.get("claim")
            evidence_path = artifact(run_dir, evidence.get("artifact"), f"{evidence_name}.artifact")
            if not isinstance(claim, str) or not claim or evidence_path is None:
                fail(f"{evidence_name}: invalid claim/artifact proof")
                continue
            evidence_proof = obj(load_json(evidence_path, f"{evidence_name}.artifact"), f"{evidence_name}.artifact")
            if not exact_keys(evidence_proof, {"scope_id", "claim"}, f"{evidence_name}.artifact") or evidence_proof.get("scope_id") != sid or evidence_proof.get("claim") != claim:
                fail(f"{evidence_name}: artifact must bind exact scope_id and claim")
        output = obj(env.get("output"), f"candidate[{index}].output")
        if set(output) != output_keys:
            fail(f"candidate[{index}]: output keys mismatch")
        source = derived_expected[sid]
        if output.get("cpt") != source["cpt"] or output.get("field_path") != source["field_path"] or output.get("field_key") != source["key"] or output.get("field_type") != source["type"]:
            fail(f"candidate[{index}]: target identity mismatch")
        patch = obj(output.get("patch"), f"candidate[{index}].patch")
        supported = set(expected[sid]["supported"])
        if not patch.keys() <= supported <= attributes:
            fail(f"candidate[{index}]: unsupported patch attribute")
        if any(not scalar_ok(key, value) for key, value in patch.items()):
            fail(f"candidate[{index}]: invalid scalar type")
        preserved = array(output.get("preserved"), f"candidate[{index}].preserved")
        current = source["current"]
        if not set(expected[sid]["required"]) <= (set(patch) | {key for key in preserved if current.get(key) not in (None, "")}):
            fail(f"candidate[{index}]: required metadata not patched/preserved")
        evidence_map = obj(output.get("tightening_evidence"), f"candidate[{index}].tightening_evidence")
        required_evidence: set[str] = set()
        for key, value in patch.items():
            old = current.get(key)
            if key in UPPER_LIMITS and (old is None or value < old):
                required_evidence.add(key)
            elif key in LOWER_LIMITS and (old is None or value > old):
                required_evidence.add(key)
            elif key == "step" and (old is None or value != old):
                required_evidence.add(key)
        if set(evidence_map) != required_evidence:
            fail(f"candidate[{index}]: tightening evidence set mismatch")
        for key, raw_evidence in evidence_map.items():
            evidence = obj(raw_evidence, f"candidate[{index}].tightening_evidence.{key}")
            common = {"previous", "proposed", "result", "artifact"}
            exact = common | ({"observed_min", "observed_max", "incompatible_count"} if key == "step" else {"observed_extreme"})
            if not exact_keys(evidence, exact, f"candidate[{index}].tightening_evidence.{key}") or evidence.get("previous") != current.get(key) or evidence.get("proposed") != patch.get(key):
                fail(f"candidate[{index}]: tightening evidence mismatch for {key}")
            numeric_keys = ("proposed", "observed_min", "observed_max", "incompatible_count") if key == "step" else ("proposed", "observed_extreme")
            numeric_ok = all(isinstance(evidence.get(item), (int, float)) and not isinstance(evidence.get(item), bool) for item in numeric_keys)
            safe = numeric_ok
            if key in UPPER_LIMITS:
                safe = safe and evidence.get("observed_extreme") <= evidence.get("proposed")
            elif key in LOWER_LIMITS:
                safe = safe and evidence.get("observed_extreme") >= evidence.get("proposed")
            elif key == "step":
                safe = safe and evidence.get("proposed") > 0 and evidence.get("observed_min") <= evidence.get("observed_max") and evidence.get("incompatible_count") == 0
            if evidence.get("result") != ("safe" if safe else "unsafe") or not safe:
                fail(f"candidate[{index}]: computed unsafe evidence for {key}")
            if artifact(run_dir, evidence.get("artifact"), f"candidate[{index}].tightening_evidence.{key}.artifact") is None:
                fail(f"candidate[{index}]: evidence artifact invalid")

    if set(candidates) != set(expected):
        fail("candidate scope set differs from expected")
    validated_rows = array(load_json(run_dir / "validated.json"), "validated")
    for index, raw in enumerate(validated_rows):
        exact_keys(obj(raw, f"validated[{index}]"), {"scope_id"}, f"validated[{index}]")
    validated_ids = [row.get("scope_id") for row in validated_rows if isinstance(row, dict)]
    if set(validated_ids) != set(expected) or len(validated_ids) != len(set(validated_ids)):
        fail("validated scopes must exactly equal expected ready scopes")

    mutations = {mutation_id(sid, key): (sid, key, value) for sid, env in candidates.items() for key, value in env["output"]["patch"].items()}
    expected_after = apply_manifest(before, candidates)
    status = "prewrite"

    if args.phase == "final":
        dry_rows = array(load_json(run_dir / "dry-run.json"), "dry-run")
        dry = {row.get("mutation_id"): row for row in dry_rows if isinstance(row, dict)}
        if set(dry) != set(mutations) or len(dry_rows) != len(dry):
            fail("dry-run journal must contain one row per scalar mutation")
        for mid, mutation in mutations.items():
            if mid in dry:
                validate_journal_row(dry[mid], f"dry-run[{mid}]", mutation, candidates, "pass", site, before)

        apply_data = obj(load_json(run_dir / "apply.json"), "apply")
        exact_keys(apply_data, {"cpts", "mutations"}, "apply")
        apply_rows = array(apply_data.get("mutations"), "apply.mutations")
        applied = {row.get("mutation_id"): row for row in apply_rows if isinstance(row, dict)}
        if set(applied) != set(mutations) or len(apply_rows) != len(applied):
            fail("apply journal must contain one row per scalar mutation")
        for mid, mutation in mutations.items():
            if mid in applied:
                validate_journal_row(applied[mid], f"apply.mutations[{mid}]", mutation, candidates, "applied", site, before)

        state = copy.deepcopy(before)
        applied_cpts: set[str] = set()
        for index, raw in enumerate(array(apply_data.get("cpts"), "apply.cpts")):
            row = obj(raw, f"apply.cpts[{index}]")
            exact_keys(row, {"cpt", "pre_apply_artifact", "pre_apply_sha256"}, f"apply.cpts[{index}]")
            cpt = row.get("cpt")
            if cpt not in owners or cpt in applied_cpts:
                fail(f"apply.cpts[{index}]: unexpected/duplicate CPT")
                continue
            pre_path = artifact(run_dir, row.get("pre_apply_artifact"), f"apply.cpts[{index}].pre_apply_artifact")
            if pre_path is not None:
                pre = load_json(pre_path)
                if pre != state or canonical_hash(pre) != row.get("pre_apply_sha256"):
                    fail(f"apply.cpts[{index}]: concurrent drift or bad pre-apply hash")
            state = apply_manifest(state, candidates, {cpt})
            applied_cpts.add(cpt)
        if applied_cpts != set(owners):
            fail("apply.cpts must cover every target CPT exactly once")
        if state != expected_after:
            fail("derived sequential apply state mismatch")

        verification = obj(load_json(run_dir / "verification.json"), "verification")
        exact_keys(verification, {"status", "source_owner", "counts", "gates", "blocked_scopes", "open_questions"} | ({"rollback_artifact"} if verification.get("status") in {"rolled-back", "rollback-failed"} else set()), "verification")
        status = verification.get("status")
        if status not in {"pass", "rolled-back", "rollback-failed", "blocked"}:
            fail("verification: invalid status")
        after = load_json(run_dir / "after-option.json")
        expected_final = expected_after if status == "pass" else before if status == "rolled-back" else None
        if expected_final is not None and after != expected_final:
            fail("after-option does not equal computed final state")
        option_diff = canonical_diff(before, after, "before-option.json", "after-option.json")
        if (run_dir / "option.diff").read_text() != option_diff:
            fail("option.diff does not equal canonical computed full diff")

        for cpt, owner in owners.items():
            if owner.get("state") != "blueprint-managed":
                continue
            before_blue = load_json(artifact(run_dir, owner.get("before_artifact"), f"source-owner {cpt}.before") or Path("/nonexistent"))
            after_path = artifact(run_dir, owner.get("after_artifact"), f"source-owner {cpt}.after")
            if after_path is not None:
                after_blue = load_json(after_path)
                expected_blue = apply_manifest(before_blue, candidates, {cpt}) if status == "pass" else before_blue if status == "rolled-back" else None
                if expected_blue is not None and after_blue != expected_blue:
                    fail(f"source-owner {cpt}: blueprint after-state mismatch")
                diff_path = artifact(run_dir, owner.get("diff_artifact"), f"source-owner {cpt}.diff")
                if diff_path is not None and diff_path.read_text() != canonical_diff(before_blue, after_blue, f"blueprints/{cpt}/before.json", f"blueprints/{cpt}/after.json"):
                    fail(f"source-owner {cpt}: blueprint diff not canonical/full")
                if cpt_config(after, cpt) != cpt_config(after_blue, cpt):
                    fail(f"source-owner {cpt}: complete blueprint/live CPT definitions diverge")

        counts = obj(verification.get("counts"), "verification.counts")
        exact_keys(counts, {"expected", "ready", "applied", "verified", "scalar_mutations"}, "verification.counts")
        string_array(verification.get("blocked_scopes"), "verification.blocked_scopes")
        string_array(verification.get("open_questions"), "verification.open_questions")
        expected_count = len(expected)
        derived_counts = {"expected": expected_count, "ready": expected_count, "applied": expected_count, "verified": expected_count, "scalar_mutations": len(mutations)}
        if status == "pass" and counts != derived_counts:
            fail("verification: counts differ from derived manifest/journals/read-back")
        gate_keys = {"coverage", "attribute_support", "key_existence", "dry_run", "read_back", "diff_clean", "record_safety", "cache", "rollback"}
        gates = obj(verification.get("gates"), "verification.gates")
        if set(gates) != gate_keys:
            fail("verification: gate set mismatch")
        if status == "pass" and (any(gates.get(key) != "pass" for key in gate_keys - {"rollback"}) or gates.get("rollback") != "not-needed"):
            fail("verification: pass gate claims mismatch")

        source_results = array(verification.get("source_owner"), "verification.source_owner")
        if {row.get("cpt") for row in source_results if isinstance(row, dict)} != set(owners):
            fail("verification: source-owner CPT set mismatch")
        for index, raw in enumerate(source_results):
            row = obj(raw, f"verification.source_owner[{index}]")
            exact_keys(row, {"cpt", "state", "read_back"}, f"verification.source_owner[{index}]")
            owner_state = owners.get(row.get("cpt"), {}).get("state")
            required_read_back = "debt" if owner_state == "runtime-only-debt" else "pass"
            if row.get("state") != owner_state or row.get("read_back") not in {"pass", "fail", "debt"} or (status == "pass" and row.get("read_back") != required_read_back):
                fail(f"verification: source-owner row mismatch for {row.get('cpt')}")

        if status in {"rolled-back", "rollback-failed"}:
            rollback_path = artifact(run_dir, verification.get("rollback_artifact"), "verification.rollback_artifact")
            rollback = obj(load_json(rollback_path) if rollback_path else None, "rollback")
            exact_keys(rollback, {"restored_option_artifact", "restored_blueprints", "cache_clear"}, "rollback")
            restored_blueprints = obj(rollback.get("restored_blueprints"), "rollback.restored_blueprints")
            expected_blueprints = {cpt for cpt, owner in owners.items() if owner.get("state") == "blueprint-managed"}
            if set(restored_blueprints) != expected_blueprints:
                fail("rollback.restored_blueprints: keys must exactly equal blueprint-managed CPTs")
            if rollback.get("cache_clear") not in {"pass", "fail"}:
                fail("rollback.cache_clear: invalid status")
            restored_path = artifact(run_dir, rollback.get("restored_option_artifact"), "rollback.restored_option_artifact")
            if restored_path is not None:
                load_json(restored_path, "rollback.restored_option_artifact")
            rollback_ok = restored_path is not None and restored_path.read_bytes() == before_path.read_bytes() and rollback.get("cache_clear") == "pass"
            for cpt, owner in owners.items():
                if owner.get("state") == "blueprint-managed":
                    restored_blue_path = artifact(run_dir, restored_blueprints.get(cpt), f"rollback blueprint {cpt}")
                    baseline_blue_path = artifact(run_dir, owner.get("before_artifact"), f"baseline blueprint {cpt}")
                    if restored_blue_path is not None:
                        load_json(restored_blue_path, f"rollback blueprint {cpt}")
                    if restored_blue_path is None or baseline_blue_path is None or restored_blue_path.read_bytes() != baseline_blue_path.read_bytes():
                        rollback_ok = False
            if status == "rolled-back" and (not rollback_ok or gates.get("rollback") != "pass"):
                fail("rolled-back status lacks computed baseline/cache equality")
            if status == "rollback-failed" and rollback_ok:
                fail("rollback-failed contradicts computed successful restoration")

    if ERRORS:
        print("Field-metadata run validation failures:")
        for error in ERRORS:
            print(f"  - {error}")
        return 1
    print(f"Field-metadata run OK ({len(expected)} scopes; phase={status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
