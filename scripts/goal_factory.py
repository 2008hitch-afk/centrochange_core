#!/usr/bin/env python3
"""EMPV AI Software Factory v1.1 — goal-driven local structural validator.

Not an AI orchestrator. Does not prove external authorization, execution of
skills, independence of review, or quality. Never merges or deploys.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SOP = "EMPV-AI-SOFTWARE-FACTORY"
VERSION = "1.1"
GOAL_STATUS = {"PLANNED", "ACTIVE", "BLOCKED", "READY_FOR_REVIEW", "VERIFIED"}
SHA = re.compile(r"[0-9a-f]{40}\Z")
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,63}\Z")
REF = re.compile(r"(github:|decision:|approval:|https://)\S+\Z")


PROJECT_BUNDLE = (
    "SOP-v1.1.md",
    "decisions/DECISION-002.md",
    "docs/AUTOMATED-OWNER-UAT.md",
    "docs/EXPERIENCE-FIRST.md",
    "docs/UI-QUALITY-GATE.md",
    "docs/DEVELOPMENT-FEEDBACK-LOOP.md",
    "docs/HANDOFF-CONTRACT.md",
)

class GateError(Exception):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"Cannot read {path}: {exc}") from exc


def is_ref(value):
    return isinstance(value, str) and bool(REF.fullmatch(value))


def evidence(root, name):
    if not isinstance(name, str) or not name.strip():
        raise GateError("Missing evidence path")
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise GateError(f"Unsafe evidence path: {name}")
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise GateError(f"Evidence symlink escapes root: {name}")
    if not target.is_file() or target.stat().st_size < 1:
        raise GateError(f"Missing or empty evidence: {name}")
    return target


def check_contract(c):
    if c.get("sop_id") != SOP or c.get("version") != VERSION or c.get("execution_model") != "GOAL_DRIVEN":
        raise GateError("Unsupported contract; expected EMPV SOP v1.1 GOAL_DRIVEN")
    kinds = c.get("goal_types")
    if not isinstance(kinds, dict) or set(kinds) != {"FOUNDATION", "FEATURE", "RELEASE", "MAINTENANCE"}:
        raise GateError("Invalid Goal types")
    for name, rule in kinds.items():
        skills = rule.get("required_skills")
        if not isinstance(skills, list) or not skills or len(skills) != len(set(skills)):
            raise GateError("Invalid required skills in " + name)
        if type(rule.get("founder_gate")) is not bool:
            raise GateError("Invalid founder gate policy")
    flags = c.get("risk_flags")
    if not isinstance(flags, list) or not flags or len(set(flags)) != len(flags):
        raise GateError("Invalid risk flags")
    if not isinstance(c.get("max_active_goals"), int) or not (1 <= c["max_active_goals"] <= 10):
        raise GateError("Invalid WIP limit")
    if len(c.get("internal_method_guide", [])) != 10:
        raise GateError("Missing internal methodology guide")
    if c.get("ui_uat_required_checks") != ["interactions", "negative_cases", "roles_permissions",
                                         "data_persistence", "responsive", "visual_accessibility"]:
        raise GateError("Invalid UI UAT coverage policy")
    if c.get("ui_required_skills") != ["ux-prototyping", "premium-ui-reviewer"]:
        raise GateError("Invalid conditional UI skills policy")
    if c.get("ui_identity_skill") != "product-art-director":
        raise GateError("Invalid UI identity skill policy")
    if c.get("ui_design_required_checks") != [
        "workflow_fit", "approved_visual_fidelity", "information_hierarchy",
        "user_friendly_forms", "responsive_quality"
    ]:
        raise GateError("Invalid approved design checks policy")
    if c.get("ui_experience_required_fields") != [
        "user_role", "user_goal", "entry_point", "primary_action",
        "success_outcome", "journey_steps", "backend_mapping", "technical_fields_policy"
    ]:
        raise GateError("Invalid experience-first contract fields")
    if c.get("ui_experience_required_checks") != [
        "user_task_completed", "plain_language", "minimum_user_input",
        "backend_complexity_hidden", "error_recovery"
    ]:
        raise GateError("Invalid experience-first review checks")


def project(root):
    root = Path(root).resolve()
    c = read_json(root / "factory" / "contract.json")
    s = read_json(root / "factory" / "state.json")
    check_contract(c)
    if s.get("sop_id") != SOP or s.get("sop_version") != VERSION:
        raise GateError("Project version does not match approved Goal contract")
    if not IDENT.fullmatch(str(s.get("project_id", ""))) or not is_ref(s.get("handoff_ref")):
        raise GateError("Missing project identity or valid handoff reference")
    goals = s.get("goals")
    if not isinstance(goals, list):
        raise GateError("Goals must be a list")
    ids = [g.get("id") for g in goals if isinstance(g, dict)]
    if len(ids) != len(goals) or len(ids) != len(set(ids)) or any(
        not isinstance(g, str) or not IDENT.fullmatch(g) for g in ids
    ):
        raise GateError("Invalid or duplicate goal IDs")
    if sum(g.get("status") == "ACTIVE" for g in goals) > c["max_active_goals"]:
        raise GateError("Too many concurrently active goals")
    for g in goals:
        if g.get("status") not in GOAL_STATUS or g.get("type") not in c["goal_types"]:
            raise GateError("Invalid goal status or type")
        if not isinstance(g.get("title"), str) or not g["title"].strip():
            raise GateError("Goal must have a title")
        if not isinstance(g.get("outcome"), str) or not g["outcome"].strip():
            raise GateError("Goal must have a business outcome")
        deps = g.get("dependencies", [])
        if not isinstance(deps, list) or len(deps) != len(set(deps)) or g["id"] in deps:
            raise GateError("Invalid goal dependencies")
        if any(dep not in ids for dep in deps):
            raise GateError("Unknown goal dependency")
        if g["status"] in {"ACTIVE", "READY_FOR_REVIEW", "VERIFIED"}:
            for dep in deps:
                if next(x for x in goals if x["id"] == dep)["status"] != "VERIFIED":
                    raise GateError(f"Goal {g['id']} bypasses dependency {dep}")
            if not is_ref(g.get("authorization_ref")):
                raise GateError(f"Goal {g['id']} lacks authorization reference")
    return root, c, s


def check_approved_ui_contract(root, goal, errors, interface_ids):
    """Validate recorded Owner-approved design references, never claim real approval."""
    identity_change = goal.get("ui_identity_change", "NO")
    if identity_change not in ("YES", "NO"):
        errors.append("UI identity change must be YES or NO")
    if identity_change == "YES":
        approval = goal.get("approvals", {}).get("ui_identity_change", {})
        if approval.get("status") != "APPROVED" or not is_ref(approval.get("reference")):
            errors.append("UI identity change requires separate Founder approval reference")
    try:
        approved_path = evidence(root, goal.get("ui_design_contract"))
        approved = read_json(approved_path)
    except GateError as exc:
        errors.append(f"Missing approved UI design contract: {exc}")
        return
    if not isinstance(approved, dict):
        errors.append("Invalid approved UI design contract")
        return
    if approved.get("status") != "APPROVED" or not is_ref(approved.get("approval_ref")):
        errors.append("UI design contract lacks Founder approval reference")
    if not isinstance(approved.get("design_id"), str) or not approved["design_id"].strip():
        errors.append("UI design contract lacks design identity/version")
    if identity_change == "YES":
        approval = goal.get("approvals", {}).get("ui_identity_change", {})
        if approval.get("reference") != approved.get("approval_ref"):
            errors.append("New UI design approval must match identity-change approval")
    screens = approved.get("interfaces")
    if not isinstance(screens, list) or any(not isinstance(x, dict) for x in screens):
        errors.append("UI design contract needs per-interface references")
        return
    ids = [x.get("interface_id") for x in screens]
    if len(ids) != len(set(ids)) or not interface_ids.issubset(set(ids)):
        errors.append("Approved UI design contract must cover EVERY affected interface")
    for screen in screens:
        iid = screen.get("interface_id")
        if not isinstance(iid, str) or not IDENT.fullmatch(iid):
            errors.append("Invalid design interface ID")
            continue
        for viewport in ("reference_screenshot", "reference_mobile_screenshot"):
            try:
                evidence(root, screen.get(viewport))
            except GateError as exc:
                errors.append(f"Design reference for {iid} ({viewport}): {exc}")
        for field in ("user_journey", "layout_rationale", "visual_identity"):
            if not isinstance(screen.get(field), str) or not screen[field].strip():
                errors.append(f"Design reference for {iid} lacks {field}")
        for field in ("user_role", "user_goal", "entry_point", "primary_action",
                      "success_outcome", "backend_mapping", "technical_fields_policy"):
            if not isinstance(screen.get(field), str) or not screen[field].strip():
                errors.append(f"Experience-first contract for {iid} lacks {field}")
        steps = screen.get("journey_steps")
        if not isinstance(steps, list) or len(steps) < 2 or any(
            not isinstance(step, str) or not step.strip() for step in steps
        ):
            errors.append(f"Experience-first contract for {iid} needs at least two meaningful journey_steps")


def check_goal_ui_uat(root, contract, goal, errors):
    """Check claimed per-interface Codex UAT; NOT proof of execution or identity."""
    impact = goal.get("ui_impact")
    if impact == "NO":
        if not isinstance(goal.get("ui_rationale"), str) or not goal["ui_rationale"].strip():
            errors.append("UI impact NO requires a documented rationale for independent review")
        return
    if impact != "YES":
        errors.append("Goal requires UI impact assessment YES/NO before review")
        return
    scope = goal.get("ui_interfaces")
    if not isinstance(scope, list) or not scope or any(
        not isinstance(x, str) or not IDENT.fullmatch(x) for x in scope
    ) or len(scope) != len(set(scope)):
        errors.append("Invalid or empty affected UI interface inventory")
        return
    check_approved_ui_contract(root, goal, errors, set(scope))
    def attached(label, path):
        try:
            evidence(root, path)
        except GateError as exc:
            errors.append(f"{label}: {exc}")
    attached("Consolidated Goal UAT report", goal.get("uat_report"))
    results = goal.get("uat_results")
    if not isinstance(results, list):
        errors.append("Missing per-interface Codex UAT results")
        return
    ids = [x.get("interface_id") for x in results if isinstance(x, dict)]
    if len(ids) != len(results) or len(ids) != len(set(ids)) or set(ids) != set(scope):
        errors.append("Codex UAT must cover EVERY affected UI interface")
        return
    for entry in results:
        iid = entry["interface_id"]
        status = entry.get("status")
        if status not in ("PASS_OFFLINE", "PASS_LIVE"):
            errors.append(f"Interface {iid}: UAT FAIL/BLOCKED/NOT_TESTED is not complete")
        if entry.get("commit_sha") != goal.get("commit_sha"):
            errors.append(f"Interface {iid}: UAT SHA does not match Goal commit")
        if not isinstance(entry.get("environment"), str) or not entry["environment"].strip():
            errors.append(f"Interface {iid}: missing environment")
        attached(f"Interface {iid} test report", entry.get("evidence"))
        attached(f"Interface {iid} screenshot", entry.get("screenshot"))
        attached(f"Interface {iid} mobile screenshot", entry.get("mobile_screenshot"))
        design = entry.get("design_review")
        if not isinstance(design, dict):
            errors.append(f"Interface {iid}: missing independent premium UI design review")
        else:
            if design.get("status") != "PASS":
                errors.append(f"Interface {iid}: premium UI review is not PASS")
            if design.get("commit_sha") != goal.get("commit_sha"):
                errors.append(f"Interface {iid}: design review SHA does not match Goal")
            if not isinstance(design.get("reviewer"), str) or not design["reviewer"].strip() or design["reviewer"] == goal.get("implementer"):
                errors.append(f"Interface {iid}: UI reviewer must differ from implementer")
            attached(f"Interface {iid} design review evidence", design.get("evidence"))
            attached(f"Interface {iid} visual comparison", design.get("comparison"))
            design_checks = design.get("checks")
            for check in contract["ui_design_required_checks"] + contract["ui_experience_required_checks"]:
                if not isinstance(design_checks, dict) or design_checks.get(check) != "PASS":
                    errors.append(f"Interface {iid}: design check {check} not PASS")
        user_task = entry.get("user_task_test")
        if not isinstance(user_task, dict) or user_task.get("status") != "PASS":
            errors.append(f"Interface {iid}: real user task test not PASS")
        else:
            if not isinstance(user_task.get("scenario"), str) or not user_task["scenario"].strip():
                errors.append(f"Interface {iid}: missing user task scenario")
            attached(f"Interface {iid} user task evidence", user_task.get("evidence"))
        checks = entry.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"Interface {iid}: missing UAT checks")
        else:
            for check in contract["ui_uat_required_checks"]:
                if checks.get(check) != "PASS":
                    errors.append(f"Interface {iid}: {check} not PASS")
        if status == "PASS_LIVE":
            risk_flags = goal.get("risk_flags", [])
            dev = goal.get("approvals", {}).get("controlled_dev_deploy", {})
            if not isinstance(risk_flags, list) or "controlled_dev_deploy" not in risk_flags or dev.get("status") != "APPROVED" or not is_ref(dev.get("reference")):
                errors.append(f"Interface {iid}: PASS_LIVE requires declared controlled DEV authorization")
    if goal.get("status") == "VERIFIED":
        accepted = goal.get("owner_ui_acceptance")
        if not isinstance(accepted, list):
            errors.append("VERIFIED Goal lacks Founder UI acceptance")
            return
        accept_ids = [x.get("interface_id") for x in accepted if isinstance(x, dict)]
        if len(accept_ids) != len(accepted) or len(accept_ids) != len(set(accept_ids)) or set(accept_ids) != set(scope):
            errors.append("Founder acceptance must cover EVERY affected UI interface")
        else:
            for entry in accepted:
                if entry.get("status") != "ACCEPTED" or not is_ref(entry.get("reference")):
                    errors.append(f"Interface {entry['interface_id']}: missing Founder acceptance reference")


def goal_check(root, contract, state, goal_id):
    goal = next((g for g in state["goals"] if g["id"] == goal_id), None)
    if goal is None:
        raise GateError("Unknown goal " + goal_id)
    errors = []
    def has(label, value):
        try:
            evidence(root, value)
        except GateError as exc:
            errors.append(f"{label}: {exc}")
    if goal.get("status") not in ("READY_FOR_REVIEW", "VERIFIED"):
        errors.append("Goal is not READY_FOR_REVIEW or VERIFIED")
    if not is_ref(goal.get("issue_ref")):
        errors.append("Missing GitHub goal issue reference")
    if not isinstance(goal.get("commit_sha"), str) or not SHA.fullmatch(goal["commit_sha"]):
        errors.append("Missing commit SHA")
    accept = goal.get("acceptance", [])
    if not isinstance(accept, list) or not accept:
        errors.append("Missing Goal acceptance criteria")
    else:
        seen = set()
        for a in accept:
            if not isinstance(a, dict) or not a.get("id") or not a.get("description"):
                errors.append("Invalid acceptance criterion")
                continue
            if a["id"] in seen:
                errors.append("Duplicate acceptance criterion")
            seen.add(a["id"])
            if a.get("status") != "PASS":
                errors.append(f"Criterion {a['id']} not PASS")
            has("Acceptance " + a["id"], a.get("evidence"))
    tests = goal.get("tests", [])
    if not isinstance(tests, list) or not tests:
        errors.append("No test evidence for Goal")
    else:
        for test in tests:
            if not isinstance(test, dict) or test.get("status") != "PASS":
                errors.append("Test incomplete / failed")
                continue
            has("Test", test.get("evidence"))
    rule = contract["goal_types"][goal["type"]]
    skill_runs = goal.get("skill_runs", {})
    required_skills = list(rule["required_skills"])
    if goal.get("ui_impact") == "YES":
        required_skills += contract["ui_required_skills"]
        if goal.get("ui_identity_change", "NO") == "YES":
            required_skills += [contract["ui_identity_skill"]]
    for skill in dict.fromkeys(required_skills):
        if not (root / ".agents/skills" / skill / "SKILL.md").is_file():
            errors.append("Missing required skill instructions " + skill)
        run = skill_runs.get(skill, {})
        if run.get("status") != "EXECUTED":
            errors.append("No execution claim for required skill " + skill)
        has("Skill " + skill, run.get("evidence"))
    report = goal.get("review", {})
    if report.get("status") != "PASS":
        errors.append("Independent goal review not PASS")
    has("Independent review", report.get("evidence"))
    if not report.get("reviewer") or report.get("reviewer") == goal.get("implementer"):
        errors.append("Reviewer not separately identified from implementer")
    has("Goal result", goal.get("result_report"))
    check_goal_ui_uat(root, contract, goal, errors)
    approvals = goal.get("approvals", {})
    def approved(key):
        record = approvals.get(key, {})
        if record.get("status") != "APPROVED" or not is_ref(record.get("reference")):
            errors.append(f"Missing explicit {key} gate approval reference")
    if rule["founder_gate"]:
        approved("founder")
    risks = goal.get("risk_flags", [])
    if not isinstance(risks, list) or len(risks) != len(set(risks)):
        errors.append("Invalid Goal risks")
    else:
        for risk in risks:
            if risk not in contract["risk_flags"]:
                errors.append("Unknown risk flag " + str(risk))
            else:
                approved(risk)
    return {
        "goal": goal_id, "structural_gate_pass": not errors, "errors": errors,
        "warning": "Self-declared evidence and approval refs are NOT independently authenticated. External reviewer and Founder gates remain required."
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="EMPV Goal-Driven Factory v1.1")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    b = sub.add_parser("bootstrap")
    b.add_argument("--project-id", required=True)
    b.add_argument("--handoff-ref", required=True)
    b.add_argument("--destination", required=True)
    for cmd in ("status", "validate-project", "validate-goal"):
        item = sub.add_parser(cmd)
        item.add_argument("--root", default=".")
        if cmd == "validate-goal":
            item.add_argument("--goal", required=True)
    a = sub.add_parser("add-goal")
    a.add_argument("--root", default=".")
    a.add_argument("--id", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--outcome", required=True)
    a.add_argument("--type", choices=("FOUNDATION", "FEATURE", "RELEASE", "MAINTENANCE"), default="FEATURE")
    a.add_argument("--issue-ref", required=True)
    args = parser.parse_args(argv)
    try:
        base = Path(__file__).resolve().parents[1]
        template = base / "templates" / "v1.1"
        if args.command == "doctor":
            c = read_json(template / "factory/contract.json")
            check_contract(c)
            skills = ({s for rule in c["goal_types"].values() for s in rule["required_skills"]}
                      | set(c["ui_required_skills"]) | {c["ui_identity_skill"]})
            missing = [s for s in skills if not (base / "template/.agents/skills" / s / "SKILL.md").is_file()]
            if missing:
                raise GateError("Missing skill(s): " + ", ".join(missing))
            print(json.dumps({"valid": True, "version": VERSION, "goal_types": len(c["goal_types"]),
                              "skills": len(skills), "remote_enforcement": False}))
            return 0
        if args.command == "bootstrap":
            if not IDENT.fullmatch(args.project_id) or not is_ref(args.handoff_ref):
                raise GateError("Invalid project ID or handoff reference")
            dest = Path(args.destination).resolve()
            if dest.exists():
                raise GateError("Refusing to overwrite existing destination")
            check_contract(read_json(template / "factory/contract.json"))
            # Package a self-contained *project* copy of the instructions referenced
            # by the scaffold's AGENTS.md; never bundle unrelated Factory internals.
            for relative in PROJECT_BUNDLE:
                source = base / relative
                if not source.is_file():
                    raise GateError("Missing canonical project instruction: " + relative)
            shutil.copytree(template, dest)
            shutil.copytree(base / "template/.agents/skills", dest / ".agents/skills")
            for relative in PROJECT_BUNDLE:
                target = dest / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(base / relative, target)
            (dest / "scripts").mkdir(exist_ok=True)
            shutil.copy2(Path(__file__), dest / "scripts/goal_factory.py")
            state_path = dest / "factory/state.json"
            state = read_json(state_path)
            state["project_id"] = args.project_id
            state["handoff_ref"] = args.handoff_ref
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"project": str(dest), "goals": 0, "operational_authorization": False}))
            return 0
        root, c, state = project(args.root)
        if args.command == "add-goal":
            if not IDENT.fullmatch(args.id) or any(g["id"] == args.id for g in state["goals"]):
                raise GateError("Invalid or duplicate goal ID")
            if not is_ref(args.issue_ref):
                raise GateError("Goal Issue ref required")
            state["goals"].append({
                "id": args.id, "title": args.title, "outcome": args.outcome,
                "type": args.type, "status": "PLANNED", "issue_ref": args.issue_ref,
                "authorization_ref": "", "dependencies": [], "acceptance": [],
                "tests": [], "skill_runs": {}, "review": {"status": "PENDING"},
                "result_report": "", "commit_sha": "", "risk_flags": [], "approvals": {},
                "implementer": "", "ui_impact": "UNASSESSED", "ui_rationale": "",
                "ui_identity_change": "NO", "ui_design_contract": "",
                "ui_interfaces": [], "uat_results": [], "uat_report": "",
                "owner_ui_acceptance": []
            })
            (root / "factory/state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"added": args.id, "status": "PLANNED"}))
            return 0
        if args.command == "status":
            print(json.dumps({"project_id": state["project_id"], "version": VERSION,
                              "goals": [{"id": g["id"], "type": g["type"], "status": g["status"]}
                                        for g in state["goals"]]}, indent=2))
            return 0
        if args.command == "validate-goal":
            result = goal_check(root, c, state, args.goal)
            print(json.dumps(result, indent=2))
            return 0 if result["structural_gate_pass"] else 2
        checked = [goal_check(root, c, state, g["id"]) for g in state["goals"]
                   if g["status"] in ("READY_FOR_REVIEW", "VERIFIED")]
        result = {
            "project_consistent": all(x["structural_gate_pass"] for x in checked),
            "all_goals_verified": bool(state["goals"]) and all(g["status"] == "VERIFIED" for g in state["goals"]),
            "goal_reviews": checked,
            "warning": "Structural claims do not authenticate approvals or actual test/skill/reviewer execution."
        }
        print(json.dumps(result, indent=2))
        return 0 if result["project_consistent"] else 2
    except (GateError, OSError, TypeError, AttributeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
