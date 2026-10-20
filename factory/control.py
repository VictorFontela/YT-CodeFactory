#!/usr/bin/env python3
"""Board transitions for the factory orchestrator. Python standard library only."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
REVIEWERS = ("security", "ux", "ui", "code")
STAGES = ("feature", "spec", "build", "review", "approve", "needs-human", "done")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def read_board():
    board = json.loads((ROOT / "board.json").read_text())
    require(board.get("version") == 1 and isinstance(board.get("jobs"), list), "Unsupported board")
    return board


def save_board(board):
    """Only the orchestrator calls this; rename prevents partial dashboard reads."""
    board["updated_at"] = now()
    fd, path = tempfile.mkstemp(prefix=".board-", dir=ROOT)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(board, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(path, ROOT / "board.json")
    finally:
        if os.path.exists(path):
            os.unlink(path)


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT.parent, capture_output=True, text=True)
    require(result.returncode == 0, result.stderr.strip() or "Git check failed")
    return result.stdout.strip()


def artifact(job, name):
    return ROOT / "jobs" / job["id"] / name


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def empty_folder(path):
    """Reuse only an empty real directory left before an interrupted board save."""
    require(not path.is_symlink(), "Refusing a symlink for a job or round folder")
    if path.exists():
        require(path.is_dir() and not any(path.iterdir()), f"Folder contains artifacts; inspect before resuming: {path.name}")
    else:
        path.mkdir(parents=True)


def check_snapshot(job):
    require(git("rev-parse", "HEAD") == job["commit"], "HEAD changed since the build")
    require(git("rev-parse", job["branch"]) == job["commit"], "Feature branch changed")
    require(digest(artifact(job, "spec.md")) == job["spec_hash"], "Spec changed during this cycle")
    # Factory reports are expected to change; application files must stay frozen.
    exclusions = [".", ":(exclude)factory/board.json", ":(exclude)factory/backlog.md",
                  f":(glob,exclude)factory/jobs/{job['id']}/round-*/**",
                  f":(exclude)factory/jobs/{job['id']}/decision.md"]
    require(not git("diff", "HEAD", "--", *exclusions), "Uncommitted application changes")
    require(not git("ls-files", "--others", "--exclude-standard", "--", *exclusions), "Untracked application files")


def report(path, commit, decision=False):
    lines = path.read_text().splitlines()
    allowed = ("APPROVE", "ESCALATE") if decision else ("VERDICT: PASS", "VERDICT: CHANGES")
    require(len(lines) >= 3 and lines[0] in allowed, f"Invalid verdict in {path.name}")
    require(lines[1] == f"COMMIT: {commit}", f"Wrong commit in {path.name}")
    require(any(line.strip() for line in lines[2:]), f"Missing evidence in {path.name}")
    return lines[0] if decision else lines[0].split(": ")[1]


def active_slot(board, excluding=None):
    require(not any(j["id"] != excluding and j["stage"] != "done" for j in board["jobs"]),
            "Finish the existing job first; this factory uses one shared checkout")


def transition(board, args):
    command = args.command
    if command == "new":
        active_slot(board)
        require(re.fullmatch(r"[0-9]{3,}-[a-z0-9]+(?:-[a-z0-9]+)*", args.job), "Use an ID such as 003-rate-limiting")
        require(not any(j["id"] == args.job for j in board["jobs"]), "Job already exists")
        require(args.request.strip(), "Empty request")
        source = None
        if args.backlog_line is not None:
            lines = (ROOT / "backlog.md").read_text().splitlines()
            require(0 < args.backlog_line <= len(lines), "Invalid backlog line")
            first = next((i + 1 for i, line in enumerate(lines) if re.match(r"^- \[ \] .+", line)), None)
            require(args.backlog_line == first, "Select the first unchecked backlog item")
            source = {"line": first, "text": lines[first - 1]}
            require(args.request == source["text"][6:], "Request must match the backlog item")
            require(not any(j.get("backlog") == source for j in board["jobs"]), "Backlog item already consumed")
        folder = ROOT / "jobs" / args.job
        empty_folder(folder)
        board["jobs"].append({
            "id": args.job, "request": args.request, "branch": f"factory/{args.job}",
            "stage": "spec", "round": 0, "cycle_start": 1, "reviews": {}, "rounds": [],
            "commit": None, "spec_hash": None, "builder_id": None, "builder_history": [],
            "feedback": [], "backlog": source, "decision": None, "human_approval": None,
            "reason": None, "created_at": now(),
        })
        return
    job = next((j for j in board["jobs"] if j["id"] == args.job), None)
    require(job is not None, "Unknown job")
    if command == "agent":
        require(job["stage"] in ("spec", "build", "review", "needs-human"), "Builder is no longer needed")
        if job["builder_id"] and job["builder_id"] != args.agent_id:
            require(args.reason, "Explain why the previous builder could not be recovered")
        job["builder_id"] = args.agent_id
        job["builder_history"].append({"id": args.agent_id, "reason": args.reason, "at": now()})
    elif command == "spec":
        require(job["stage"] == "spec", "Expected spec stage")
        require(artifact(job, "spec.md").read_text().strip(), "Empty specification")
        job["spec_hash"] = digest(artifact(job, "spec.md"))
        job["stage"] = "build"
    elif command == "built":
        require(job["stage"] == "build", "Expected build stage")
        require(job["builder_id"], "Register the builder first")
        require(artifact(job, "build.md").read_text().strip(), "Missing build evidence")
        require(git("branch", "--show-current") == job["branch"], "Builder must use its feature branch")
        job["commit"] = git("rev-parse", "HEAD")
        check_snapshot(job)
        require(not git("status", "--porcelain", "--", str(artifact(job, "build.md")), str(artifact(job, "spec.md"))),
                "Commit spec.md and build.md with the build")
        number = job["round"] + 1
        require(number - job["cycle_start"] < 2, "Automatic review limit reached")
        folder = artifact(job, f"round-{number}")
        empty_folder(folder)
        job.update(stage="review", round=number, reviews={r: "pending" for r in REVIEWERS}, decision=None)
        job["rounds"].append({"number": number, "commit": job["commit"], "reviews": dict(job["reviews"])})
    elif command == "collect":
        require(job["stage"] == "review", "Expected review stage")
        check_snapshot(job)
        reviews = {}
        for reviewer in REVIEWERS:
            path = artifact(job, f"round-{job['round']}/review-{reviewer}.md")
            reviews[reviewer] = report(path, job["commit"]) if path.exists() else "pending"
        job["reviews"] = reviews
        job["rounds"][-1]["reviews"] = dict(reviews)
        if "pending" in reviews.values():
            return
        if "CHANGES" not in reviews.values():
            job["stage"] = "approve"
        elif job["round"] - job["cycle_start"] + 1 >= 2:
            job.update(stage="needs-human", reason="review-limit")
        else:
            job["stage"] = "build"
    elif command == "decide":
        require(job["stage"] == "approve" and not job["human_approval"], "Expected automatic approval stage")
        require(all(job["reviews"].get(r) == "PASS" for r in REVIEWERS), "Four PASS verdicts required")
        check_snapshot(job)
        require(all(report(artifact(job, f"round-{job['round']}/review-{r}.md"), job["commit"]) == "PASS"
                    for r in REVIEWERS), "Current reports must still be PASS")
        verdict = report(artifact(job, "decision.md"), job["commit"], decision=True)
        job["decision"] = {"verdict": verdict, "commit": job["commit"]}
        if verdict == "ESCALATE":
            job.update(stage="needs-human", reason="approver-escalated")
    elif command == "rework":
        require(job["stage"] == "needs-human", "Only needs-human jobs accept manual rework")
        require(args.note.strip(), "Feedback is required")
        active_slot(board, job["id"])
        previous = artifact(job, "decision.md")
        job["feedback"].append({"note": args.note, "after_round": job["round"], "at": now(),
                                "decision": job["decision"],
                                "decision_text": previous.read_text() if previous.exists() else None})
        job.update(stage="build", cycle_start=job["round"] + 1, decision=None, human_approval=None, reason=None)
    elif command == "human-approve":
        require(job["stage"] == "needs-human", "Human approval requires needs-human")
        check_snapshot(job)
        job["human_approval"] = {"commit": job["commit"], "at": now()}
        job["stage"] = "approve"
    elif command == "merged":
        require(job["stage"] == "approve", "Expected approval stage")
        human = job["human_approval"]
        automatic = job["decision"]
        require((human and human["commit"] == job["commit"]) or
                (automatic and automatic == {"verdict": "APPROVE", "commit": job["commit"]}
                 and all(job["reviews"].get(r) == "PASS" for r in REVIEWERS)), "Missing merge authorization")
        require(git("rev-parse", job["branch"]) == job["commit"], "Feature branch changed after approval")
        require(git("branch", "--show-current") == "main", "Finish on main")
        git("merge-base", "--is-ancestor", job["commit"], "main")
        job.update(stage="done", merged_at=now(), reason=None)
    else:
        raise ValueError("Unknown transition")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("new", "spec", "built", "collect", "decide", "rework", "human-approve", "merged", "agent"):
        part = sub.add_parser(command)
        part.add_argument("job")
        if command == "new":
            part.add_argument("--request", required=True)
            part.add_argument("--backlog-line", type=int)
        elif command == "agent":
            part.add_argument("--agent-id", required=True)
            part.add_argument("--reason")
        elif command == "rework":
            part.add_argument("--note", required=True)
    args = parser.parse_args()
    try:
        board = copy.deepcopy(read_board())
        transition(board, args)
        save_board(board)
        print(json.dumps(board, indent=2, ensure_ascii=False))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, f"Factory: {error}\n")


if __name__ == "__main__":
    main()
