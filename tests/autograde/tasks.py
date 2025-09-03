"""Graders for the five tasks of the CI/CD lab."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from .context import Ctx
from .facts import (
    BADGE_SUBJECT, CI_V1, CI_V2, CI_V3, COURSE_SLUG, DETECTOR_GREEN, EXPECTED_HISTORY, GREEN_SUBJECT, RED_SUBJECT, REPO_NAME, TAG1,
    TAG1_MESSAGE, TAG2, TAG2_MESSAGE, V1_SUBJECT, V2_SUBJECT, V3_SUBJECT, WORKFLOW, slug_of,
)
from .framework import Task
from .textutil import get_answer

PLACEHOLDER_NAMES = {"", "your full name", "your name"}
PLACEHOLDER_EMAILS = {"", "your.email@example.com", "your-email@example.com"}
TO_LINE_RE = re.compile(r"(?m)^To (\S+)\s*$")
COMMIT_LINE_RE = r"(?m)^\[(\S+) (?:\(root-commit\) )?([0-9a-f]{7,40})\] (.*)$"
RANGE_RE = r"(?m)^\s+([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s+(\S+)\s+->\s+(\S+)\s*$"
SUCCESS, FAILURE = {"✓", "success", "completed success"}, {"X", "failure", "x"}


def clean(text: str) -> str:
    """The pasted text without the '$ command' lines a student may have copied along with the output."""
    return "\n".join(ln for ln in text.split("\n") if not ln.startswith("$ "))


def norm(text: str) -> str:
    """A file's text with line endings normalised and the end of file made uniform."""
    return text.replace("\r\n", "\n").rstrip("\n") + "\n"


def own_slug(ctx: Ctx) -> str:
    """'owner/repo' of the student's own repository: from the clone's config when it can be read, else from the pasted 1.1."""
    live = slug_of(ctx.facts.remote_url("origin")) if ctx.repo_mode else ""
    if live and live != COURSE_SLUG:
        return live
    match = TO_LINE_RE.search(clean(ctx.step("1.1")))
    return slug_of(match.group(1)) if match else ""


def to_slug(text: str) -> str:
    """'owner/repo' named by the first 'To <address>' line of a pasted push ('' if there is none)."""
    match = TO_LINE_RE.search(clean(text))
    return slug_of(match.group(1)) if match else ""


def _answer(ctx: Ctx, number: int) -> str:
    return get_answer(ctx.text, number).strip("`'\" ").strip()


def _commit(text: str) -> Optional["re.Match[str]"]:
    return re.search(COMMIT_LINE_RE, clean(text))


def runs(text: str) -> List[Dict[str, str]]:
    """The rows of 'gh run list' as dicts (status, title, workflow, branch, event, id), from a terminal or from a pipe."""
    rows: List[Dict[str, str]] = []
    for line in clean(text).split("\n"):
        fields = [f for f in re.split(r"\t|\s{2,}", line.strip()) if f]
        if fields and fields[0] in ("completed", "in_progress", "queued"):
            fields = fields[1:]  # piped output: 'completed  success  <title> ...'
        if len(fields) >= 6 and re.fullmatch(r"\d{6,}", fields[5] if len(fields) > 5 else ""):
            rows.append({"status": fields[0], "title": fields[1], "workflow": fields[2], "branch": fields[3], "event": fields[4],
                         "id": fields[5]})
    return rows


def passed(row: Dict[str, str]) -> bool:
    """True for a run that succeeded."""
    return row["status"] in SUCCESS


def failed(row: Dict[str, str]) -> bool:
    """True for a run that failed."""
    return row["status"] in FAILURE


def own_identity(ctx: Ctx) -> bool:
    """True when the identity Git uses here is the student's own (not a placeholder, not a teammate's)."""
    f = ctx.facts
    name, email = f.effective_config("user.name"), f.effective_config("user.email")
    return name.lower() not in PLACEHOLDER_NAMES and "@" in email and email.lower() not in PLACEHOLDER_EMAILS \
        and name.lower() not in f.published_names() and email.lower() not in f.published_emails()


def _pushed_to_main(text: str, mine: str) -> bool:
    return re.search(RANGE_RE, clean(text)) is not None and bool(mine) and to_slug(text) == mine and "! [" not in text


# -- Task 1 -----------------------------------------------------------------
def grade_task1(ctx: Ctx) -> Task:
    """Task 1: the first workflow, pushed, and its first run."""
    t = Task(1, "The CI workflow", 20, ctx.repo_mode)
    f = ctx.facts
    mine = own_slug(ctx)
    s11, s12, s14, s15 = clean(ctx.step("1.1")), clean(ctx.step("1.2")), clean(ctx.step("1.4")), ctx.step("1.5")
    t.check(1, "1.1 push output: '* [new branch]  main -> main'", lambda: re.search(r"\* \[new branch\]\s+main -> main", s11) is not None)
    t.check(1, "1.1 push output: branch 'main' set up to track 'origin/main'",
            lambda: re.search(r"(?i)branch 'main' set up to track (?:remote branch 'main' from 'origin'|'origin/main')", s11) is not None)
    t.check(1, "1.1 the push went to your own GitHub repository (not the course repository)",
            lambda: bool(to_slug(s11)) and to_slug(s11) != COURSE_SLUG and to_slug(s11) == mine)
    t.check(4, "1.2 cat ci.yml: name CI, push and pull_request on main, runs-on ubuntu-latest, actions/checkout@v4, setup-python@v5, "
               "'flake8 src --max-line-length=100' and 'pytest -v'",
            lambda: norm(s12) == CI_V1 or all(x in s12 for x in (
                "name: CI", "push:", "pull_request:", "branches: [ main ]", "runs-on: ubuntu-latest", "actions/checkout@v4",
                "actions/setup-python@v5", "flake8 src --max-line-length=100", "pytest -v")))
    c = _commit(ctx.step("1.3"))
    t.check(3, "1.3 commit output: '[main <sha>] ci: add lint and test workflow', create mode .github/workflows/ci.yml",
            lambda: c is not None and c.group(1) == "main" and c.group(3).strip() == V1_SUBJECT
            and "create mode 100644 .github/workflows/ci.yml" in clean(ctx.step("1.3")))
    t.check(3, "1.4 push output: '<old>..<new>  main -> main' to your own repository",
            lambda: _pushed_to_main(s14, mine))
    rows = runs(s15)
    t.check(3, "1.5 gh run list: the run 'ci: add lint and test workflow', workflow CI, branch main, event push, finished with a success (a check mark)",
            lambda: any(r["title"] == V1_SUBJECT and r["workflow"] == "CI" and r["branch"] == "main" and r["event"] == "push" and passed(r)
                        for r in rows))
    t.check(1, "ANSWER-1 is ubuntu-latest", lambda: _answer(ctx, 1).lower() == "ubuntu-latest")
    commit = f.with_subject(V1_SUBJECT) if ctx.repo_mode else None
    t.check(2, "live repo: the commit 'ci: add lint and test workflow' holds .github/workflows/ci.yml exactly as in the handout, "
               "and its number is the pasted one",
            lambda: commit is not None and norm(f.file_at(commit.sha, WORKFLOW) or "") == CI_V1 and c is not None
            and commit.sha.startswith(c.group(2)), needs_repo=True,
            why=lambda: "the workflow file must be typed exactly as in the handout (indentation matters in YAML)")
    t.check(1, "live repo: your identity is set in this clone (not a placeholder, not a teammate's)", lambda: own_identity(ctx), needs_repo=True)
    return t


# -- Task 2 -----------------------------------------------------------------
def grade_task2(ctx: Ctx) -> Task:
    """Task 2: workflow_dispatch, pushed and used."""
    t = Task(2, "Run it by hand", 20, ctx.repo_mode)
    f = ctx.facts
    mine = own_slug(ctx)
    s21, s22, s23, s24 = ctx.step("2.1"), ctx.step("2.2"), clean(ctx.step("2.3")), ctx.step("2.4")
    c = _commit(s21)
    t.check(3, "2.1 commit output: '[main <sha>] ci: add manual workflow_dispatch trigger', 1 file changed, 1 insertion(+)",
            lambda: c is not None and c.group(3).strip() == V2_SUBJECT and re.search(r"\b1 file changed, 1 insertion\(\+\)", clean(s21)) is not None)
    t.check(3, "2.2 push output: '<old>..<new>  main -> main' to your own repository", lambda: _pushed_to_main(s22, mine))
    t.check(4, "2.3 gh workflow run: 'Created workflow_dispatch event for ci.yml at main'",
            lambda: re.search(r"Created workflow_dispatch event for ci\.yml at main", s23) is not None)
    rows = runs(s24)
    t.check(3, "2.4 gh run list: a run with event workflow_dispatch (the manual one) that succeeded",
            lambda: any(r["event"] == "workflow_dispatch" and r["workflow"] == "CI" and passed(r) for r in rows))
    t.check(2, "2.4 gh run list: the push run 'ci: add manual workflow_dispatch trigger' that succeeded",
            lambda: any(r["title"] == V2_SUBJECT and r["event"] == "push" and passed(r) for r in rows))
    commit = f.with_subject(V2_SUBJECT) if ctx.repo_mode else None
    first = f.with_subject(V1_SUBJECT) if ctx.repo_mode else None
    t.check(3, "live repo: ci.yml has the workflow_dispatch trigger and is otherwise the file of Task 1",
            lambda: commit is not None and norm(f.file_at(commit.sha, WORKFLOW) or "") == CI_V2, needs_repo=True,
            why=lambda: "add exactly the line '  workflow_dispatch:   # manual trigger' under the on: block")
    t.check(2, "live repo: the commit sits straight on top of the commit of Task 1, and its number is the pasted one",
            lambda: commit is not None and first is not None and commit.parents == [first.sha] and c is not None
            and commit.sha.startswith(c.group(2)), needs_repo=True)
    return t


# -- Task 3 -----------------------------------------------------------------
def grade_task3(ctx: Ctx) -> Task:
    """Task 3: a lint error makes a run fail, the fix makes it pass."""
    t = Task(3, "Red, then green", 25, ctx.repo_mode)
    f = ctx.facts
    mine = own_slug(ctx)
    s = {k: ctx.step(k) for k in ("3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7")}
    c1, c2 = _commit(s["3.1"]), _commit(s["3.5"])
    t.check(2, "3.1 commit output: '[main <sha>] feat(vision): add distance helper'", lambda: c1 is not None and c1.group(3).strip() == RED_SUBJECT)
    t.check(3, "3.2 push output: '<old>..<new>  main -> main' to your own repository", lambda: _pushed_to_main(s["3.2"], mine))
    rows3 = runs(s["3.3"])
    t.check(4, "3.3 gh run list: the run 'feat(vision): add distance helper' FAILED (an X)",
            lambda: any(r["title"] == RED_SUBJECT and failed(r) for r in rows3))
    log = clean(s["3.4"])
    t.check(5, "3.4 the failed log names the file and the problem: 'src/detector.py', a flake8 code, and 'imported but unused'",
            lambda: "src/detector.py" in log and re.search(r"\bF401\b", log) is not None and "imported but unused" in log)
    t.check(2, "3.5 commit output: '[main <sha>] fix(vision): remove unused import', 1 deletion(-)",
            lambda: c2 is not None and c2.group(3).strip() == GREEN_SUBJECT and re.search(r"\b1 deletion\(-\)", clean(s["3.5"])) is not None)
    t.check(3, "3.6 push output: '<old>..<new>  main -> main' to your own repository", lambda: _pushed_to_main(s["3.6"], mine))
    rows7 = runs(s["3.7"])
    t.check(4, "3.7 gh run list: newest first, the fix run succeeded (a check mark) and the run before it, 'feat(vision): add distance helper', failed (an X)",
            lambda: len(rows7) >= 2 and rows7[0]["title"] == GREEN_SUBJECT and passed(rows7[0]) and rows7[1]["title"] == RED_SUBJECT
            and failed(rows7[1]))
    t.check(1, "ANSWER-2 is F401", lambda: _answer(ctx, 2).upper() == "F401")
    red = f.with_subject(RED_SUBJECT) if ctx.repo_mode else None
    green = f.with_subject(GREEN_SUBJECT) if ctx.repo_mode else None
    t.check(1, "live repo: the first commit has 'import os' (the unused import), the fix removes it, and their numbers are the pasted ones",
            lambda: red is not None and green is not None and "import os" in (f.file_at(red.sha, "src/detector.py") or "")
            and f.file_at(green.sha, "src/detector.py") == DETECTOR_GREEN and green.parents == [red.sha]
            and c1 is not None and red.sha.startswith(c1.group(2)) and c2 is not None and green.sha.startswith(c2.group(2)),
            needs_repo=True, why=lambda: "expected: a commit with the lint error, then a commit on top of it that removes the line")
    return t


# -- Task 4 -----------------------------------------------------------------
def grade_task4(ctx: Ctx) -> Task:
    """Task 4: a badge, an annotated tag and a release."""
    t = Task(4, "The badge, a tag and a release", 20, ctx.repo_mode)
    f = ctx.facts
    mine = own_slug(ctx)
    s = {k: clean(ctx.step(k)) for k in ("4.1", "4.2", "4.3", "4.4", "4.5", "4.6")}
    c = _commit(s["4.1"])
    t.check(2, "4.1 commit output: '[main <sha>] docs: add CI status badge to README'", lambda: c is not None and c.group(3).strip() == BADGE_SUBJECT)
    t.check(2, "4.2 push output: '<old>..<new>  main -> main' to your own repository", lambda: _pushed_to_main(s["4.2"], mine))
    lines = [ln.strip() for ln in s["4.3"].split("\n") if ln.strip()]
    t.check(2, "4.3 git tag lists v1.0.0", lambda: TAG1 in lines)
    t.check(2, "4.3 git cat-file -t v1.0.0 prints 'tag' (an annotated tag is an object of its own; a lightweight tag would print 'commit')",
            lambda: "tag" in lines)
    t.check(3, "4.4 push output: '* [new tag]  v1.0.0 -> v1.0.0' to your own repository",
            lambda: re.search(r"\* \[new tag\]\s+v1\.0\.0 -> v1\.0\.0", s["4.4"]) is not None and to_slug(s["4.4"]) == mine)
    t.check(3, "4.5 gh release create: the address of the release, https://github.com/<you>/rover-ci-lab/releases/tag/v1.0.0",
            lambda: bool(mine) and re.search(rf"https://github\.com/{re.escape(mine)}/releases/tag/v1\.0\.0", s["4.5"], re.I) is not None)
    t.check(2, "4.6 gh release list: v1.0.0, marked Latest", lambda: re.search(r"(?m)^v1\.0\.0\s+Latest\s+v1\.0\.0\b", s["4.6"]) is not None)
    t.check(1, "ANSWER-3 is MAJOR", lambda: _answer(ctx, 3).upper() == "MAJOR")
    target = f.tag_target(TAG1) if ctx.repo_mode else ""
    commit = f.commit(target) if target else None
    readme = (f.file_at(target, "README.md") or "") if target else ""
    badge = f"![CI](https://github.com/{mine}/actions/workflows/ci.yml/badge.svg)"
    t.check(3, "live repo: v1.0.0 is an annotated tag with the message 'First stable release of the vision module', on the badge commit, "
               "whose README starts with the badge of your own repository",
            lambda: f.tag_type(TAG1) == "tag" and f.tag_message(TAG1) == TAG1_MESSAGE and commit is not None
            and commit.subject == BADGE_SUBJECT and bool(mine) and readme.lower().startswith(badge.lower()), needs_repo=True,
            why=lambda: "create it with: git tag -a v1.0.0 -m \"First stable release of the vision module\" (after the badge commit)")
    return t


# -- Task 5 -----------------------------------------------------------------
def grade_task5(ctx: Ctx) -> Task:
    """Task 5: a deploy job that runs only when a tag is pushed."""
    t = Task(5, "Deploy only on a tag", 15, ctx.repo_mode)
    f = ctx.facts
    mine = own_slug(ctx)
    s = {k: ctx.step(k) for k in ("5.1", "5.2", "5.3", "5.4", "5.5")}
    c = _commit(s["5.1"])
    t.check(2, "5.1 commit output: '[main <sha>] ci: deploy a build artifact when a tag is pushed'", lambda: c is not None and c.group(3).strip() == V3_SUBJECT)
    t.check(2, "5.2 push output: '<old>..<new>  main -> main' to your own repository", lambda: _pushed_to_main(s["5.2"], mine))
    t.check(3, "5.3 push output: '* [new tag]  v1.1.0 -> v1.1.0' to your own repository",
            lambda: re.search(r"\* \[new tag\]\s+v1\.1\.0 -> v1\.1\.0", clean(s["5.3"])) is not None and to_slug(s["5.3"]) == mine)
    rows = runs(s["5.4"])
    t.check(3, "5.4 gh run list: the newest run is on the tag v1.1.0 (BRANCH column), event push, and succeeded",
            lambda: bool(rows) and rows[0]["branch"] == TAG2 and rows[0]["event"] == "push" and passed(rows[0]))
    view = clean(s["5.5"])
    t.check(3, "5.5 gh run view: two jobs, 'build-and-test' and 'deploy', both with a check mark (the deploy job ran because of the tag)",
            lambda: re.search(r"(?m)^[✓]\s+build-and-test\b", view) is not None and re.search(r"(?m)^[✓]\s+deploy\b", view) is not None)
    tip = f.with_subject(V3_SUBJECT) if ctx.repo_mode else None
    t.check(2, "live repo: ci.yml has the tags filter and the deploy job (needs build-and-test, only for tags starting with v), and v1.1.0 is "
               "an annotated tag with the message 'Add the distance helper' on that commit",
            lambda: tip is not None and norm(f.file_at(tip.sha, WORKFLOW) or "") == CI_V3 and f.tag_type(TAG2) == "tag"
            and f.tag_message(TAG2) == TAG2_MESSAGE and f.tag_target(TAG2) == tip.sha, needs_repo=True,
            why=lambda: "create it with: git tag -a v1.1.0 -m \"Add the distance helper\" (after the commit of 5.1)")
    return t
