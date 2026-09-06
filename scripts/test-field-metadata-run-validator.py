#!/usr/bin/env python3
"""Exercise valid and rejected field-metadata run artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate-field-metadata-run.py"


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, separators=(",", ":")))
    path.chmod(0o600)


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def diff(before: object, after: object, before_name: str, after_name: str) -> str:
    return "".join(unified_diff(canonical(before).splitlines(keepends=True), canonical(after).splitlines(keepends=True), fromfile=before_name, tofile=after_name))


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", str(VALIDATOR), *args], text=True, capture_output=True, check=False)


def run(path: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return invoke(str(path), "--phase", phase)


def fixture(root: Path, *, rolled_back: bool = False, owner_state: str = "runtime-only-debt", field_type: str = "title", field_path: list[str] | None = None) -> dict[str, object]:
    os.chmod(root, 0o700)
    metadata = root.stat()
    write(root / "run.json", {"version": 1, "nonce": "0123456789abcdef0123456789abcdef", "created_at": datetime.now(timezone.utc).isoformat(), "path": str(root.resolve()), "site": "fixture-site", "uid": os.getuid(), "mode": "0700", "device": metadata.st_dev, "inode": metadata.st_ino})
    current_limits = {"maxlength": 120} if field_type == "title" else {"min": 0, "max": 100, "step": 1}
    path = field_path or ["title"]
    field = {"type": field_type, "key": path[-1], "label": "Title", "description": "", "placeholder": "", **current_limits}
    for key in reversed(path[:-1]):
        field = {"type": "repeater", "key": key, "label": key.title(), "description": "Nested group.", "fields": [field]}
    before = {"products": {"fields": [field]}}
    raw = json.dumps(before, separators=(",", ":")).encode()
    (root / "before-option.json").write_bytes(raw)
    (root / "before-option.sha256").write_text(hashlib.sha256(raw).hexdigest())
    (root / "before-db.sql").write_text("-- fixture")
    if owner_state == "blueprint-managed":
        blueprints = root / "blueprints" / "products"
        blueprints.mkdir(parents=True)
        write(blueprints / "before.json", before)
        owner = {"cpt": "products", "state": "blueprint-managed", "before_artifact": "blueprints/products/before.json", "after_artifact": "blueprints/products/after.json", "diff_artifact": "blueprints/products/blueprint.diff"}
    elif owner_state == "runtime-only-debt":
        owner = {"cpt": "products", "state": "runtime-only-debt", "debt": "no committed blueprint"}
    else:
        owner = {"cpt": "products", "state": owner_state}
    write(root / "source-owner.json", [owner])
    inventory = []
    expected = []
    candidates = []
    for depth, key in enumerate(path):
        candidate_path = path[: depth + 1]
        candidate_type = field_type if depth == len(path) - 1 else "repeater"
        sid = "field-definition:products:" + hashlib.sha256(json.dumps(candidate_path, separators=(",", ":")).encode()).hexdigest()
        current = ({"description": "", "placeholder": "", **current_limits} if candidate_type == field_type else {"description": "Nested group."})
        supported = (["description", "placeholder", "minlength", "maxlength", "pattern"] if field_type == "title" else ["description", "placeholder", "min", "max", "step"]) if candidate_type == field_type else ["description", "min", "max"]
        required = ["description", "placeholder"] if candidate_type == field_type else ["description"]
        missing = [attribute for attribute in required if current.get(attribute) in (None, "")]
        patch = {"description": "Name shown as product title.", "placeholder": "e.g. Ceremonial Matcha 30g"} if candidate_type == field_type else {}
        inventory.append({"scope_id": sid, "cpt": "products", "field_path": candidate_path, "key": key, "type": candidate_type, "label": "Title" if candidate_type == field_type else key.title(), "current": current, "excluded": False, "overrides_debt": False})
        expected.append({"scope_id": sid, "cpt": "products", "field_path": candidate_path, "field_type": candidate_type, "required": required, "supported": supported, "missing": missing})
        candidates.append({"scope_id": sid, "mode": "build-material", "status": "ready", "evidence": [], "output": {"cpt": "products", "field_path": candidate_path, "field_key": key, "field_type": candidate_type, "patch": patch, "preserved": list(current), "tightening_evidence": {}}, "open_questions": []})
    envelope = candidates[-1]
    write(root / "inventory.json", inventory)
    write(root / "expected-scopes.json", expected)
    write(root / "candidates.json", candidates)
    write(root / "validated.json", [{"scope_id": candidate["scope_id"]} for candidate in candidates])
    mids = [f"{envelope['scope_id']}:description", f"{envelope['scope_id']}:placeholder"]
    def journal(mid: str, status: str, dry: bool) -> dict[str, object]:
        attribute = mid.rsplit(":", 1)[1]
        value = envelope["output"]["patch"][attribute]
        if len(path) == 1:
            writer = "voxel:field-schema"
            argv = ["wpdev", writer, "fixture-site", f"--key={path[-1]}", "--cpts=products", "--no-insert-if-missing", f"--patch={json.dumps({attribute: value}, separators=(',', ':'))}"]
            if dry:
                argv.append("--dry-run")
        else:
            writer = "voxel:settings set"
            pointer: list[object] = ["fields"]
            for index, _key in enumerate(path):
                pointer.append(0)
                if index < len(path) - 1:
                    pointer.append("fields")
            target = "/".join(["products", *[str(part) for part in pointer], attribute])
            argv = ["wpdev", "voxel:settings", "fixture-site", "set", target, f"--value={json.dumps(value, separators=(',', ':'))}", "--dry" if dry else "--yes"]
        return {"mutation_id": mid, "status": status, "writer": writer, "argv": argv}
    write(root / "dry-run.json", [journal(mid, "pass", True) for mid in mids])
    (root / "pre-apply-products.json").write_bytes(raw)
    write(root / "apply.json", {"cpts": [{"cpt": "products", "pre_apply_artifact": "pre-apply-products.json", "pre_apply_sha256": hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}], "mutations": [journal(mid, "applied", False) for mid in mids]})
    intended = copy.deepcopy(before)
    target = intended["products"]["fields"][0]
    for _key in path[1:]:
        target = target["fields"][0]
    target.update(envelope["output"]["patch"])
    after = before if rolled_back else intended
    write(root / "after-option.json", after)
    (root / "option.diff").write_text(diff(before, after, "before-option.json", "after-option.json"))
    if owner_state == "blueprint-managed":
        after_blue = before if rolled_back else intended
        write(root / "blueprints/products/after.json", after_blue)
        (root / "blueprints/products/blueprint.diff").write_text(diff(before, after_blue, "blueprints/products/before.json", "blueprints/products/after.json"))
    gates = {"coverage": "pass", "attribute_support": "pass", "key_existence": "pass", "dry_run": "pass", "read_back": "pass", "diff_clean": "pass", "record_safety": "pass", "cache": "pass", "rollback": "pass" if rolled_back else "not-needed"}
    verification: dict[str, object] = {"status": "rolled-back" if rolled_back else "pass", "source_owner": [{"cpt": "products", "state": owner_state, "read_back": "debt" if owner_state == "runtime-only-debt" else "pass"}], "counts": {"expected": len(expected), "ready": len(expected), "applied": len(expected), "verified": len(expected), "scalar_mutations": 2}, "gates": gates, "blocked_scopes": [], "open_questions": []}
    if rolled_back:
        write(root / "restored-option.json", before)
        restored_blueprints = {}
        if owner_state == "blueprint-managed":
            write(root / "restored-blueprint.json", before)
            restored_blueprints["products"] = "restored-blueprint.json"
        write(root / "rollback.json", {"restored_option_artifact": "restored-option.json", "restored_blueprints": restored_blueprints, "cache_clear": "pass"})
        verification["rollback_artifact"] = "rollback.json"
    write(root / "verification.json", verification)
    for artifact_path in root.rglob("*"):
        if artifact_path.is_file():
            artifact_path.chmod(0o600)
    return {"before": before, "inventory": inventory, "expected": expected, "candidates": [envelope], "sid": sid}


def expect_rejected(label: str, mutate, *, blueprint_managed: bool = False, rolled_back: bool = False, field_type: str = "title", field_path: list[str] | None = None, owner_state: str | None = None) -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        data = fixture(root, owner_state=owner_state or ("blueprint-managed" if blueprint_managed else "runtime-only-debt"), rolled_back=rolled_back, field_type=field_type, field_path=field_path)
        mutate(root, data)
        result = run(root, "final")
        if result.returncode == 0:
            raise AssertionError(f"validator accepted {label}")


def expect_prewrite_valid(label: str, mutate, *, field_type: str = "title") -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        data = fixture(root, field_type=field_type)
        mutate(root, data)
        result = run(root, "prewrite")
        if result.returncode != 0:
            raise AssertionError(f"validator rejected valid {label}:\n{result.stdout}{result.stderr}")


def set_bound(root: Path, data: dict[str, object], key: str, proposed: float, observed: float, *, safe: bool = True) -> None:
    (root / "extreme.json").write_text("{}")
    (root / "extreme.json").chmod(0o600)
    candidate = data["candidates"][0]
    candidate["output"]["patch"][key] = proposed
    candidate["output"]["tightening_evidence"][key] = {"previous": candidate["output"].get("current"), "proposed": proposed, "observed_extreme": observed, "result": "safe" if safe else "unsafe", "artifact": "extreme.json"}
    candidate["output"]["tightening_evidence"][key]["previous"] = data["inventory"][0]["current"].get(key)
    write(root / "candidates.json", data["candidates"])


def main() -> int:
    for rolled_back, owner_state in ((False, "runtime-only-debt"), (True, "runtime-only-debt"), (False, "blueprint-managed"), (False, "not-applicable")):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture(root, rolled_back=rolled_back, owner_state=owner_state)
            result = run(root, "final")
            if result.returncode != 0:
                print(result.stdout + result.stderr)
                return 1

    cases = {
        "unknown type": lambda root, data: (data["before"]["products"]["fields"][0].update({"type": "mystery"}), write(root / "before-option.json", data["before"]), (root / "before-option.sha256").write_text(hashlib.sha256((root / "before-option.json").read_bytes()).hexdigest())),
        "inventory extra key": lambda root, data: (data["inventory"][0].update({"extra": True}), write(root / "inventory.json", data["inventory"])),
        "expected missing key": lambda root, data: (data["expected"][0].pop("missing"), write(root / "expected-scopes.json", data["expected"])),
        "ready open question": lambda root, data: (data["candidates"][0].update({"open_questions": ["unknown"]}), write(root / "candidates.json", data["candidates"])),
        "malformed evidence": lambda root, data: (data["candidates"][0].update({"evidence": ["self-attested"]}), write(root / "candidates.json", data["candidates"])),
        "evidence scope divergence": lambda root, data: (write(root / "proof.json", {"scope_id": "wrong", "claim": "Inventory matches."}), data["candidates"][0].update({"evidence": [{"claim": "Inventory matches.", "artifact": "proof.json"}]}), write(root / "candidates.json", data["candidates"])),
        "evidence claim divergence": lambda root, data: (write(root / "proof.json", {"scope_id": data["sid"], "claim": "Different claim."}), data["candidates"][0].update({"evidence": [{"claim": "Inventory matches.", "artifact": "proof.json"}]}), write(root / "candidates.json", data["candidates"])),
        "new upper no evidence": lambda root, data: (data["candidates"][0]["output"]["patch"].update({"maxlength": 100}), data["candidates"][0]["output"]["tightening_evidence"].clear(), write(root / "candidates.json", data["candidates"])),
        "unsafe lower evidence": lambda root, data: ((root / "extreme.json").write_text("{}"), data["candidates"][0]["output"]["patch"].update({"minlength": 5}), data["candidates"][0]["output"]["tightening_evidence"].update({"minlength": {"previous": None, "proposed": 5, "observed_extreme": 3, "result": "safe", "artifact": "extreme.json"}}), write(root / "candidates.json", data["candidates"])),
        "unsafe step evidence": lambda root, data: ((root / "extreme.json").write_text("{}"), data["candidates"][0]["output"].update({"field_type": "title"}), data["candidates"][0]["output"]["patch"].update({"step": 2}), write(root / "candidates.json", data["candidates"])),
        "wrong writer": lambda root, data: (lambda rows: (rows[0].update({"writer": "voxel:settings set"}), write(root / "dry-run.json", rows)))(json.loads((root / "dry-run.json").read_text())),
        "shell argv": lambda root, data: (lambda rows: (rows[0].update({"argv": "wpdev voxel:field-schema ..."}), write(root / "dry-run.json", rows)))(json.loads((root / "dry-run.json").read_text())),
        "option diff lie": lambda root, data: (root / "option.diff").write_text("fixture"),
        "path escape": lambda root, data: (data["candidates"][0].update({"evidence": [{"claim": "x", "artifact": "../outside"}]}), write(root / "candidates.json", data["candidates"])),
        "artifact symlink": lambda root, data: ((root / "before-db.sql").unlink(), (root / "before-db.sql").symlink_to(root / "before-option.json")),
    }
    for label, mutate in cases.items():
        expect_rejected(label, mutate)

    expect_prewrite_valid("tightened upper", lambda root, data: set_bound(root, data, "maxlength", 100, 90))
    expect_prewrite_valid("new lower", lambda root, data: set_bound(root, data, "minlength", 2, 3))

    def compatible_step(root: Path, data: dict[str, object]) -> None:
        (root / "step.json").write_text("{}")
        (root / "step.json").chmod(0o600)
        candidate = data["candidates"][0]
        candidate["output"]["patch"]["step"] = 2
        candidate["output"]["tightening_evidence"]["step"] = {"previous": 1, "proposed": 2, "observed_min": 0, "observed_max": 100, "incompatible_count": 0, "result": "safe", "artifact": "step.json"}
        write(root / "candidates.json", data["candidates"])
    expect_prewrite_valid("compatible step", compatible_step, field_type="number")

    expect_rejected("unsafe tightened upper", lambda root, data: set_bound(root, data, "maxlength", 100, 101))
    expect_rejected("unsafe new lower", lambda root, data: set_bound(root, data, "minlength", 5, 4))

    def incompatible_step(root: Path, data: dict[str, object]) -> None:
        (root / "step.json").write_text("{}")
        (root / "step.json").chmod(0o600)
        candidate = data["candidates"][0]
        candidate["output"]["patch"]["step"] = 2
        candidate["output"]["tightening_evidence"]["step"] = {"previous": 1, "proposed": 2, "observed_min": 0, "observed_max": 99, "incompatible_count": 1, "result": "safe", "artifact": "step.json"}
        write(root / "candidates.json", data["candidates"])
    expect_rejected("incompatible step", incompatible_step, field_type="number")

    def bad_argv(extra: str) -> None:
        expect_rejected(extra, lambda root, data: (lambda rows: (rows[0]["argv"].append(extra), write(root / "dry-run.json", rows)))(json.loads((root / "dry-run.json").read_text())))
    bad_argv("--force")
    bad_argv("--cpts=other")

    expect_rejected("source-owner bad read_back", lambda root, data: (lambda value: (value["source_owner"][0].update({"read_back": "pass"}), write(root / "verification.json", value)))(json.loads((root / "verification.json").read_text())))
    expect_rejected("not-applicable bad read_back", lambda root, data: (lambda value: (value["source_owner"][0].update({"read_back": "debt"}), write(root / "verification.json", value)))(json.loads((root / "verification.json").read_text())), owner_state="not-applicable")
    expect_rejected("invalid run proof", lambda root, data: (lambda value: (value.update({"nonce": "reused"}), write(root / "run.json", value)))(json.loads((root / "run.json").read_text())))
    expect_rejected("hard-linked artifact", lambda root, data: os.link(root / "before-db.sql", root / "before-db-link.sql"))
    expect_rejected("rollback extra key", lambda root, data: (lambda value: (value.update({"extra": True}), write(root / "rollback.json", value)))(json.loads((root / "rollback.json").read_text())), rolled_back=True)
    expect_rejected("rollback option byte divergence", lambda root, data: ((root / "restored-option.json").write_text(canonical(data["before"])), (root / "restored-option.json").chmod(0o600)), rolled_back=True)
    expect_rejected("rollback blueprint byte divergence", lambda root, data: ((root / "restored-blueprint.json").write_text(canonical(data["before"])), (root / "restored-blueprint.json").chmod(0o600)), rolled_back=True, blueprint_managed=True)
    expect_rejected("blueprint/live divergence", lambda root, data: write(root / "blueprints/products/after.json", data["before"]), blueprint_managed=True)
    expect_rejected("truncated blueprint diff", lambda root, data: (root / "blueprints/products/blueprint.diff").write_text("truncated"), blueprint_managed=True)

    nested_path = ["sections", "groups", "items", "title"]
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture(root, field_path=nested_path)
        result = run(root, "final")
        if result.returncode != 0:
            raise AssertionError(f"validator rejected arbitrary-depth nested writer:\n{result.stdout}{result.stderr}")
    expect_rejected("nested exact path divergence", lambda root, data: (lambda rows: (rows[0]["argv"].__setitem__(4, rows[0]["argv"][4].replace("/0/fields/0/", "/1/fields/0/", 1)), write(root / "dry-run.json", rows)))(json.loads((root / "dry-run.json").read_text())), field_path=nested_path)
    expect_rejected("nested phase divergence", lambda root, data: (lambda rows: (rows[0]["argv"].__setitem__(-1, "--yes"), write(root / "dry-run.json", rows)))(json.loads((root / "dry-run.json").read_text())), field_path=nested_path)

    boundary_cases = (
        ("duplicate phase", lambda root: invoke(str(root), "--phase", "prewrite", "--phase", "final")),
        ("conflicting phase", lambda root: invoke(str(root), "--phase=prewrite", "--phase=final")),
        ("duplicate contract", lambda root: invoke(str(root), "--phase", "prewrite", "--contract", str(ROOT / "references/voxel/field-metadata-contract.json"), "--contract", str(ROOT / "references/voxel/field-metadata-contract.json"))),
        ("extra positional", lambda root: invoke(str(root), "extra", "--phase", "prewrite")),
    )
    for label, command in boundary_cases:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture(root)
            if command(root).returncode == 0:
                raise AssertionError(f"validator accepted {label}")

    rejection_count = len(cases) + 16
    print(f"Field-metadata run validator tests OK (pass, rolled-back, blueprint-managed, not-applicable, arbitrary-depth nested writer, {rejection_count} rejection cases, 3 valid bound cases, 4 CLI boundary cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
