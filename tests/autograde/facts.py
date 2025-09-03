"""Ground truth about the student's repository. Read-only: never changes the repo and never uses the network."""
from __future__ import annotations

import os
import re
import subprocess
from typing import List, NamedTuple, Optional, Set, Tuple

STAFF_SUBJECT = "chore: add lab assignment and grader"
COURSE_SLUG = "qbit-glitch/26ra2308-gitlab-12-rover-ci-lab"  # lower case; the course repository students start from
REPO_NAME = "rover-ci-lab"
WORKFLOW = ".github/workflows/ci.yml"
V1_SUBJECT = "ci: add lint and test workflow"
V2_SUBJECT = "ci: add manual workflow_dispatch trigger"
RED_SUBJECT = "feat(vision): add distance helper"
GREEN_SUBJECT = "fix(vision): remove unused import"
BADGE_SUBJECT = "docs: add CI status badge to README"
V3_SUBJECT = "ci: deploy a build artifact when a tag is pushed"
EXPECTED_HISTORY = [V1_SUBJECT, V2_SUBJECT, RED_SUBJECT, GREEN_SUBJECT, BADGE_SUBJECT, V3_SUBJECT]  # oldest first
TAG1, TAG1_MESSAGE = "v1.0.0", "First stable release of the vision module"
TAG2, TAG2_MESSAGE = "v1.1.0", "Add the distance helper"
CI_V1 = "name: CI\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\njobs:\n  build-and-test:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out the repository\n        uses: actions/checkout@v4\n      - name: Set up Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install flake8 pytest\n      - name: Lint with flake8\n        run: flake8 src --max-line-length=100\n      - name: Run tests with pytest\n        run: pytest -v\n"
CI_V2 = "name: CI\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n  workflow_dispatch:   # manual trigger\njobs:\n  build-and-test:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out the repository\n        uses: actions/checkout@v4\n      - name: Set up Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install flake8 pytest\n      - name: Lint with flake8\n        run: flake8 src --max-line-length=100\n      - name: Run tests with pytest\n        run: pytest -v\n"
CI_V3 = "name: CI\non:\n  push:\n    branches: [ main ]\n    tags: [ 'v*' ]\n  pull_request:\n    branches: [ main ]\n  workflow_dispatch:   # manual trigger\njobs:\n  build-and-test:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out the repository\n        uses: actions/checkout@v4\n      - name: Set up Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install flake8 pytest\n      - name: Lint with flake8\n        run: flake8 src --max-line-length=100\n      - name: Run tests with pytest\n        run: pytest -v\n  deploy:\n    needs: build-and-test\n    if: startsWith(github.ref, 'refs/tags/v')\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out the repository\n        uses: actions/checkout@v4\n      - name: Build an artifact\n        run: |\n          mkdir dist\n          tar -czf dist/rover-ci-lab.tar.gz src\n      - name: Upload the artifact\n        uses: actions/upload-artifact@v4\n        with:\n          name: rover-ci-lab\n          path: dist/\n"
DETECTOR_GREEN = '"""Obstacle detector for the Kestrel-1 camera."""\n\nTHRESHOLD_CM = 30\n\n\ndef detect_obstacle(distance_cm, threshold_cm=THRESHOLD_CM):\n    """Return True when something is closer than threshold_cm."""\n    return distance_cm < threshold_cm\n\n\ndef closest(distances):\n    """Return the smallest distance in the list, or None when it is empty."""\n    return min(distances) if distances else None\n'
GIT_TIMEOUT = 60
SLUG_RE = re.compile(r"github\.com[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/|\s|$)")


class GitError(RuntimeError):
    """Raised when the repository is not set up the way the grader expects."""


class Commit(NamedTuple):
    """A commit with the facts the grader needs."""

    sha: str
    author: str
    email: str
    committer_email: str
    subject: str
    parents: List[str]


FORMAT = "--format=%H%x1f%an%x1f%ae%x1f%ce%x1f%s%x1f%P"


def _commit(line: str) -> Optional[Commit]:
    parts = line.rstrip("\n").split("\x1f")
    return Commit(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5].split()) if len(parts) == 6 else None


def slug_of(url: str) -> str:
    """'owner/repo' (lower case) of a GitHub address in any of its forms ('' if it is not a GitHub address)."""
    match = SLUG_RE.search(url.strip() + " ")
    return f"{match.group(1)}/{match.group(2)}".lower() if match else ""


def run_git_rc(repo: str, *args: str) -> Tuple[int, str]:
    """Run git in 'repo' and return (exit code, stdout); a git call that hangs is stopped and reported as 124."""
    env = dict(os.environ, LC_ALL="C", GIT_PAGER="cat", GIT_TERMINAL_PROMPT="0")
    try:
        proc = subprocess.run(["git", *args], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return 124, ""
    return proc.returncode, proc.stdout


def run_git(repo: str, *args: str) -> str:
    """Run git in 'repo' and return stdout ('' on failure)."""
    return run_git_rc(repo, *args)[1]


class Facts:
    """Everything the grader needs to know about the repository."""

    def __init__(self, repo: str) -> None:
        self.repo = os.path.abspath(repo)
        if run_git_rc(self.repo, "rev-parse", "--verify", "-q", "refs/heads/main^{commit}")[0] != 0:
            raise GitError("branch main not found. Run the grader inside your clone of the lab repository.")
        log = [c for c in map(_commit, run_git(self.repo, "log", "refs/heads/main", FORMAT).splitlines()) if c]
        staff = [c for c in log if c.subject == STAFF_SUBJECT]
        if not staff:
            raise GitError(f"the starting commit '{STAFF_SUBJECT}' is not in the history of main. "
                           "Run the grader inside your clone of the lab repository (made with 'git clone').")
        self.base: str = staff[-1].sha
        self.published: List[Commit] = [c for c in map(_commit, run_git(self.repo, "log", self.base, FORMAT).splitlines()) if c]

    def published_emails(self) -> Set[str]:
        """E-mail addresses of the people who wrote the starting history."""
        return {c.email.lower() for c in self.published}

    def published_names(self) -> Set[str]:
        """Names of the people who wrote the starting history."""
        return {c.author.lower() for c in self.published}

    def config_value(self, key: str) -> str:
        """Value of a repository-local config key ('' if unset)."""
        return run_git(self.repo, "config", "--local", "--get", key).strip()

    def effective_config(self, key: str) -> str:
        """Value of a config key as Git uses it here, local or global ('' if unset)."""
        return run_git(self.repo, "config", "--get", key).strip()

    def remote_url(self, name: str) -> str:
        """The address stored for remote 'name' ('' if there is none)."""
        return self.config_value(f"remote.{name}.url")

    def branch_config(self, branch: str) -> Tuple[str, str]:
        """(remote, merge ref) a local branch is set up to track ('' for unset values)."""
        return self.config_value(f"branch.{branch}.remote"), self.config_value(f"branch.{branch}.merge")

    def rev(self, ref: str) -> str:
        """Full SHA of 'ref' ('' if it does not name a commit)."""
        return run_git(self.repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").strip()

    def commit_exists(self, token: str) -> bool:
        """True if 'token' names a commit object in this repository."""
        return bool(token) and run_git_rc(self.repo, "cat-file", "-e", f"{token}^{{commit}}")[0] == 0

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """True if commit 'ancestor' is 'descendant' itself or part of its history."""
        return bool(ancestor) and bool(descendant) \
            and run_git_rc(self.repo, "merge-base", "--is-ancestor", ancestor, descendant)[0] == 0

    def file_at(self, ref: str, path: str) -> Optional[str]:
        """Content of 'path' at 'ref' (None if absent)."""
        code, out = run_git_rc(self.repo, "show", f"{ref}:{path}")
        return out if code == 0 else None

    def commit(self, ref: str) -> Optional[Commit]:
        """The commit 'ref' names (None if it names nothing)."""
        sha = self.rev(ref)
        return _commit(run_git(self.repo, "show", "-s", FORMAT, sha)) if sha else None

    def above_base(self) -> List[Commit]:
        """Every commit of main that is not part of the starting history, oldest first."""
        out = run_git(self.repo, "log", "--reverse", FORMAT, f"{self.base}..refs/heads/main")
        return [c for c in map(_commit, out.splitlines()) if c]

    def with_subject(self, subject: str, prefix: bool = False) -> Optional[Commit]:
        """The newest commit above the starting commit with this subject (or starting with it)."""
        for commit in reversed(self.above_base()):
            if commit.subject == subject or (prefix and commit.subject.startswith(subject)):
                return commit
        return None

    def main_tip(self) -> str:
        """Full SHA of the local branch main."""
        return self.rev("refs/heads/main")

    def local_branch(self, name: str) -> str:
        """SHA of a local branch ('' if there is none)."""
        return self.rev(f"refs/heads/{name}")

    def tag_type(self, name: str) -> str:
        """'tag' for an annotated tag, 'commit' for a lightweight one, '' when there is no such tag."""
        return run_git(self.repo, "cat-file", "-t", f"refs/tags/{name}").strip()

    def tag_message(self, name: str) -> str:
        """The first line of the message of an annotated tag ('' for a lightweight tag)."""
        return run_git(self.repo, "for-each-ref", "--format=%(contents:subject)", f"refs/tags/{name}").strip() \
            if self.tag_type(name) == "tag" else ""

    def tag_target(self, name: str) -> str:
        """The commit a tag points at ('' when there is no such tag)."""
        return self.rev(f"refs/tags/{name}")

    def reflog(self, ref: str) -> List[str]:
        """Reflog messages of 'ref', newest first (empty if there is no reflog)."""
        return run_git(self.repo, "log", "-g", "--format=%gs", ref, "--").splitlines()

    def working_tree_clean(self) -> bool:
        """True when 'git status --porcelain' prints nothing and no merge or rebase is in progress."""
        clean = run_git(self.repo, "status", "--porcelain").strip() == ""
        merging = run_git_rc(self.repo, "rev-parse", "-q", "--verify", "MERGE_HEAD")[0] == 0
        return clean and not merging
