#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Deterministic metadata, immutable reviews and bounded repair accounting.

Semantic findings, impact and resolution evidence are supplied by reviewers.
This script validates their structure; it never judges specification meaning.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

POLICY = "full-spec-v1"
CHECKS = ("requirements_preserved", "acceptance_observable", "references_resolved", "decisions_resolved")
STATES = ("active", "ready", "needs_user", "incomplete_review", "stalled", "budget_exhausted")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if exclusive:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(data)
    else:
        handle, temporary = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(data)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def fingerprint(path, kind):
    path = Path(path).resolve(strict=True)
    content = path.read_bytes()
    content.decode("utf-8")
    return {"path": str(path), "kind": kind, "sha256": hashlib.sha256(content).hexdigest()}


def digest(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def snapshot(document, companions=(), dependencies=()):
    files = [fingerprint(document, "document")]
    for kind, paths in (("companion", companions), ("dependency", dependencies)):
        files.extend(fingerprint(path, kind) for path in paths)
    require(len({entry["path"] for entry in files}) == len(files), "Duplicate snapshot path")
    files.sort(key=lambda entry: entry["path"])
    return {"document": str(Path(document).resolve()), "files": files, "digest": digest(files)}


def verify_snapshot(value):
    files = value["files"]
    require(files and len({entry["path"] for entry in files}) == len(files), "Invalid snapshot inventory")
    require(sum(entry["kind"] == "document" for entry in files) == 1, "One primary document required")
    require(any(entry["path"] == value["document"] and entry["kind"] == "document" for entry in files), "Document mismatch")
    require(digest(files) == value["digest"], "Snapshot digest mismatch")
    for entry in files:
        require(fingerprint(entry["path"], entry["kind"]) == entry, f"Stale snapshot: {entry['path']}")


def text_field(value, key):
    require(isinstance(value.get(key), str) and bool(value[key].strip()), f"Nonempty {key} required")


def strings(value, name):
    require(isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value), f"Invalid {name}")


def evaluate(result):
    require(result.get("status") in ("complete", "incomplete"), "Invalid review status")
    require(result.get("coverage") == "full", "Only full reviews supported")
    for key in ("required_lenses", "executed_lenses", "pending_decisions", "failures"):
        strings(result.get(key), key)
    require(result["required_lenses"], "Review must require at least one lens")
    require(isinstance(result.get("checks"), dict), "checks required")
    require(all(type(result["checks"].get(key)) is bool for key in CHECKS), "All readiness checks must be boolean")
    findings = result.get("findings")
    require(isinstance(findings, list), "findings array required")
    for index, finding in enumerate(findings, 1):
        require(finding.get("id") == f"R{index}", "Finding IDs must be consecutive R1...")
        require(finding.get("severity") in ("blocker", "major", "minor"), "Invalid severity")
        for key in ("section", "finding", "correction", "evidence", "consequence"):
            text_field(finding, key)
        strings(finding.get("lenses"), "finding lenses")
        require(finding["lenses"] and set(finding["lenses"]) <= set(result["executed_lenses"]), "Unknown finding lens")
    excluded = result.get("excluded_findings", [])
    require(isinstance(excluded, list), "excluded_findings must be array")
    for finding in excluded:
        for key in ("finding", "reason", "evidence"):
            text_field(finding, key)
    complete = result["status"] == "complete"
    if complete:
        require(set(result["required_lenses"]) <= set(result["executed_lenses"]) and not result["failures"], "Required review incomplete")
    else:
        require(result["failures"], "Incomplete review needs failure reason")
    ready = complete and all(result["checks"][key] for key in CHECKS) and not result["pending_decisions"] and not any(f["severity"] != "minor" for f in findings)
    verdict = None if not complete else ("NO LISTO" if not ready else "LISTO CON OBSERVACIONES" if findings else "LISTO")
    return ready, verdict


def load_review(path, current=True):
    value = read(path)
    require(value.get("policy") == POLICY and value.get("schema_version") == 1, "Unsupported review protocol")
    ready, verdict = evaluate(value)
    require(value.get("ready_for_dev") is ready and value.get("verdict") == verdict, "Readiness metadata mismatch")
    if current:
        verify_snapshot(value["snapshot"])
    return value


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def render(value):
    lines = ["# Revisión de preparación", "", f"Review ID: {value['review_id']}", f"Informe histórico: {value['report_path']}", f"Política: {POLICY}; cobertura: full", f"Estado: {value['status']}; ready_for_dev: {str(value['ready_for_dev']).lower()}", f"Snapshot: {value['snapshot']['digest']}", "", "## Fuentes", ""]
    lines.extend(f"- {entry['kind']}: {entry['path']} — SHA-256 {entry['sha256']}" for entry in value["snapshot"]["files"])
    lines.extend(["", f"Lentes requeridas: {', '.join(value['required_lenses'])}", f"Lentes ejecutadas: {', '.join(value['executed_lenses'])}", "", "## Hallazgos", "", "| ID | Severidad | Sección | Hallazgo | Corrección | Evidencia | Consecuencia | Lentes |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    for finding in value["findings"]:
        lines.append("| " + " | ".join(cell(finding[key]) for key in ("id", "severity", "section", "finding", "correction", "evidence", "consequence")) + " | " + cell(", ".join(finding["lenses"])) + " |")
    lines.extend(["", "## Comprobaciones", ""])
    lines.extend(f"- {key}: {str(value['checks'][key]).lower()}" for key in CHECKS)
    for key in ("pending_decisions", "failures", "excluded_findings", "exclusions"):
        lines.extend(["", f"{key}: {json.dumps(value.get(key, []), ensure_ascii=False)}"])
    if value["verdict"]:
        lines.extend(["", f"Veredicto final: {value['verdict']}"])
    return "\n".join(lines) + "\n"


def make_report(result_path, snapshot_path, output, latest=None):
    result = read(result_path)
    ready, verdict = evaluate(result)
    source = read(snapshot_path)
    verify_snapshot(source)
    output = Path(output).resolve()
    require(output.suffix == ".md", "Report output must end in .md")
    metadata = output.with_suffix(".json")
    require(not output.exists() and not metadata.exists(), "Round reports are immutable")
    protected = {entry["path"] for entry in source["files"]} | {str(Path(result_path).resolve()), str(Path(snapshot_path).resolve())}
    targets = {str(output), str(metadata)}
    if latest:
        latest = Path(latest).resolve()
        require(latest.suffix == ".md", "Latest report must end in .md")
        require(latest == Path(source["document"]).with_suffix(".review.md").resolve(), "Latest alias must be the document's canonical review neighbor")
        targets.update((str(latest), str(latest.with_suffix(".json"))))
    require(not targets & protected, "Output would overwrite an input")
    if latest:
        require(latest != output and latest.with_suffix(".json") != metadata, "Latest alias cannot be round report")
    value = {**result, "schema_version": 1, "policy": POLICY, "review_id": uuid4().hex, "created_at": now(), "snapshot": source, "ready_for_dev": ready, "verdict": verdict, "report_path": str(output)}
    write(metadata, value, exclusive=True)
    write(output, render(value), exclusive=True)
    if latest and value["status"] == "complete":
        write(latest.with_suffix(".json"), value)
        write(latest, render(value))
    return value


def init_run(document, review_path, max_rounds):
    document = Path(document).resolve(strict=True)
    review_path = Path(review_path).resolve(strict=True)
    require(max_rounds > 0, "max_rounds must be positive")
    folder = document.parent / ".reviews" / document.stem / uuid4().hex
    folder.mkdir(parents=True)
    shutil.copyfile(review_path, folder / "input.review.md")
    metadata = review_path.with_suffix(".json")
    if metadata.exists():
        shutil.copyfile(metadata, folder / "input.review.json")
    value = {"schema_version": 1, "policy": POLICY, "run_id": folder.name, "document": str(document), "max_rounds": max_rounds, "rounds_used": 0, "status": "active", "reason": "Baseline required", "defects": [], "reviews": [], "attempts": [], "events": [], "created_at": now()}
    path = folder / "run.json"
    write(path, value, exclusive=True)
    return {"run": str(path), "state": value}


def load_run(path):
    value = read(path)
    require(value.get("policy") == POLICY and value.get("schema_version") == 1, "Unsupported run protocol")
    require(value["status"] in STATES, "Invalid run status")
    require(0 <= value["rounds_used"] <= value["max_rounds"], "Invalid round accounting")
    require(len(value["attempts"]) == value["rounds_used"], "Attempt accounting mismatch")
    return value


def begin(path):
    value = load_run(path)
    require(value["status"] in ("active", "needs_user", "incomplete_review", "stalled"), "Run cannot begin repair")
    require(value["reviews"], "Baseline required before repair")
    review = load_review(value["reviews"][-1]["path"])
    require(review["status"] == "complete", "Complete review required before writing")
    require(value["rounds_used"] < value["max_rounds"], "Repair budget exhausted")
    value["rounds_used"] += 1
    value["attempts"].append({"number": value["rounds_used"], "started_at": now(), "baseline": review["review_id"], "completed": False})
    value["status"], value["reason"] = "active", "Repair attempt started"
    write(path, value)
    return value


def nonnegative(value, name):
    require(value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0), f"Invalid metric {name}")


def record(path, review_path, reconcile_path, refresh_reason=None):
    value = load_run(path)
    review = load_review(review_path)
    require(review["snapshot"]["document"] == value["document"], "Review is for another document")
    require(review["review_id"] not in {r["review_id"] for r in value["reviews"]}, "Review already recorded")
    require(Path(review_path).resolve() == Path(review["report_path"]).with_suffix(".json").resolve(), "Record immutable historical report, not latest alias")
    pending_attempt = bool(value["attempts"] and not value["attempts"][-1]["completed"])
    if value["reviews"] and review["snapshot"]["digest"] != value["reviews"][-1]["snapshot"]:
        require(pending_attempt or bool(refresh_reason and refresh_reason.strip()), "Changed contract requires consumed repair attempt or explicit external refresh")
        if not pending_attempt:
            require(value["status"] == "incomplete_review", "Stop stale run before external refresh")
            value["events"].append({"event": "external_refresh", "reason": refresh_reason, "at": now()})
    rec = read(reconcile_path)
    reopen = rec.get("reopen_rejected", {})
    require(isinstance(reopen, dict), "Invalid reopen_rejected")
    for identifier, evidence in reopen.items():
        require(any(d["id"] == identifier and d["state"] == "rejected" for d in value["defects"]), "Reopen requires previously rejected defect")
        text_field(evidence, "reason")
        text_field(evidence, "evidence")
    keys = rec.get("keys")
    require(isinstance(keys, dict) and set(keys) == {f["id"] for f in review["findings"]}, "Map every local finding to a stable key")
    require(all(isinstance(key, str) and key.strip() for key in keys.values()), "Invalid defect key")
    metrics = rec.get("metrics", {})
    for name in ("duration_seconds", "tokens", "cost"):
        nonnegative(metrics.get(name), name)
    by_key = {d["key"]: d for d in value["defects"]}
    rank = {"minor": 0, "major": 1, "blocker": 2}
    seen = set()
    for finding in review["findings"]:
        key = keys[finding["id"]]
        if key not in by_key:
            defect = {"id": f"D{len(value['defects']) + 1}", "key": key, "severity": finding["severity"], "state": "open", "observations": [], "history": []}
            value["defects"].append(defect)
            by_key[key] = defect
        defect = by_key[key]
        defect["severity"] = max((defect["severity"], finding["severity"]), key=lambda severity: rank[severity])
        keep_rejected = defect["state"] == "rejected" and defect["id"] not in reopen
        if defect["state"] == "resolved" or defect["id"] in reopen:
            defect["history"].append({"event": "reopened", "review_id": review["review_id"], "at": now()})
            if defect["id"] in reopen:
                defect["history"].append({"event": "new_evidence", **reopen[defect["id"]], "at": now()})
        if not keep_rejected:
            defect["state"] = "open"
        defect["observations"].append({"review_id": review["review_id"], "local_id": finding["id"], "evidence": finding["evidence"], "lenses": finding["lenses"]})
        seen.add(defect["id"])
    dispositions = rec.get("dispositions", {})
    require(isinstance(dispositions, dict), "Invalid dispositions")
    by_id = {d["id"]: d for d in value["defects"]}
    for identifier, decision in dispositions.items():
        require(identifier in by_id, f"Unknown defect {identifier}")
        require(decision.get("state") in ("open", "applied", "resolved", "rejected", "deferred"), "Invalid disposition")
        text_field(decision, "reason")
        text_field(decision, "evidence")
        defect = by_id[identifier]
        require(not (identifier in seen and decision["state"] == "resolved"), "Current finding cannot be resolved without another review")
        require(decision["state"] != "deferred" or defect["severity"] == "minor", "Valid blocker/major cannot be deferred")
        defect["state"] = decision["state"]
        defect["history"].append({**decision, "review_id": review["review_id"], "at": now()})
    unresolved = [d for d in value["defects"] if d["severity"] != "minor" and d["state"] not in ("resolved", "rejected")]
    current_required = [d for d in value["defects"] if d["id"] in seen and d["severity"] != "minor" and d["state"] != "rejected"]
    checks_ok = all(review["checks"][key] for key in CHECKS)
    ready = review["status"] == "complete" and checks_ok and not review["pending_decisions"] and not unresolved and not current_required
    if review["status"] != "complete":
        status, reason = "incomplete_review", "; ".join(review["failures"])
    elif review["pending_decisions"] or not review["checks"]["decisions_resolved"]:
        status, reason = "needs_user", "Necessary decisions unresolved"
    elif ready:
        status, reason = "ready", "Full current review and all required defects verified"
    elif value["rounds_used"] >= value["max_rounds"]:
        status, reason = "budget_exhausted", "Repair limit reached with unresolved preparation"
    else:
        status, reason = "active", "Required defects or readiness checks unresolved"
    # A report's positive gate is necessary too: rejecting a current major must
    # produce a corrected triage report, not an inconsistent green run.
    if status == "ready" and not review["ready_for_dev"]:
        status, reason = "active", "Re-triage current report before readiness"
        if value["rounds_used"] >= value["max_rounds"]:
            status = "budget_exhausted"
    value["status"], value["reason"] = status, reason
    changed = []
    if value["reviews"]:
        old = load_review(value["reviews"][-1]["path"], current=False)["snapshot"]["files"]
        old_hashes = {f["path"]: f["sha256"] for f in old}
        new_hashes = {f["path"]: f["sha256"] for f in review["snapshot"]["files"]}
        changed = sorted(p for p in old_hashes.keys() | new_hashes.keys() if old_hashes.get(p) != new_hashes.get(p))
    value["reviews"].append({"review_id": review["review_id"], "path": str(Path(review_path).resolve()), "round": value["rounds_used"], "snapshot": review["snapshot"]["digest"], "coverage": "full", "changed_files": changed, "metrics": {k: metrics.get(k) for k in ("duration_seconds", "tokens", "cost")}, "observations": rec.get("observations", "")})
    if value["attempts"]:
        value["attempts"][-1]["completed"] = True
    write(path, value)
    return value


def adopt(review_path, output):
    value = load_review(review_path)
    require(value["status"] == "complete", "Cannot adopt incomplete baseline")
    output = Path(output).resolve()
    require(output.suffix == ".md", "Report output must end in .md")
    require(not output.exists() and not output.with_suffix(".json").exists(), "Round reports are immutable")
    value["report_path"] = str(output)
    write(output.with_suffix(".json"), value, exclusive=True)
    write(output, render(value), exclusive=True)
    return value


def stop(path, status, reason):
    require(status in ("needs_user", "incomplete_review", "stalled", "budget_exhausted"), "Invalid stop status")
    require(bool(reason.strip()), "Stop reason required")
    value = load_run(path)
    value["status"], value["reason"] = status, reason
    value["events"].append({"status": status, "reason": reason, "at": now()})
    write(path, value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    snap = commands.add_parser("snapshot", help="Hash primary, declared companions and read dependencies")
    snap.add_argument("target")
    snap.add_argument("--companion", action="append", default=[])
    snap.add_argument("--dependency", action="append", default=[])
    snap.add_argument("-o", required=True)
    report = commands.add_parser("report", help="Validate full result, compute readiness and render immutable report")
    report.add_argument("target")
    report.add_argument("--snapshot", required=True)
    report.add_argument("-o", required=True)
    report.add_argument("--latest")
    check = commands.add_parser("verify", help="Check review schema/readiness and current file hashes")
    check.add_argument("target")
    init = commands.add_parser("init", help="Create run and archive supplied review; no source modifications")
    init.add_argument("target")
    init.add_argument("--review", required=True)
    init.add_argument("--max-rounds", type=int, default=3)
    start = commands.add_parser("begin", help="Verify baseline and consume repair budget before writing")
    start.add_argument("target")
    rec = commands.add_parser("record", help="Reconcile stable defects with a full review; absence does not close defects")
    rec.add_argument("target")
    rec.add_argument("--review", required=True)
    rec.add_argument("--reconcile", required=True)
    rec.add_argument("--refresh-reason", help="Explicit external-change revalidation after stopping stale run; never own uncounted repair")
    adoption = commands.add_parser("adopt", help="Archive a complete current baseline without rerunning lenses")
    adoption.add_argument("target")
    adoption.add_argument("-o", required=True)
    halt = commands.add_parser("stop", help="Persist honest stop state and reason")
    halt.add_argument("target")
    halt.add_argument("--status", required=True)
    halt.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            result = snapshot(args.target, args.companion, args.dependency)
            require(str(Path(args.o).resolve()) not in {f["path"] for f in result["files"]}, "Snapshot output would overwrite input")
            write(args.o, result)
        elif args.command == "report":
            result = make_report(args.target, args.snapshot, args.o, args.latest)
        elif args.command == "verify":
            result = load_review(args.target)
        elif args.command == "init":
            result = init_run(args.target, args.review, args.max_rounds)
        elif args.command == "begin":
            result = begin(args.target)
        elif args.command == "record":
            result = record(args.target, args.review, args.reconcile, args.refresh_reason)
        elif args.command == "adopt":
            result = adopt(args.target, args.o)
        else:
            result = stop(args.target, args.status, args.reason)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
