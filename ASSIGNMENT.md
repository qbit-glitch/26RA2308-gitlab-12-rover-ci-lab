# Git Lab Assignment: Kestrel-1 Rover, Let the Robot Check the Code

**Course:** 26RA2308 Git for Software Development and Collaboration
**Builds on:** Experiments 1 to 11. **Based on:** Experiment 12 (CI/CD Automation, Tags and Releases with GitHub Actions)
**Time allowed:** 1 hour. **Marks:** 100

---

## The story

Last week a teammate pushed a vision change that did not even import, and the rover's camera was dead for a morning. **Ben**'s fix
is not another rule for humans: it is a **machine that checks every push**. GitHub Actions runs a **workflow** on every push: it
installs Python, runs the linter (`flake8`) and the tests (`pytest`), and shows a green check or a red cross next to the commit. When
the code is good, you **tag** a release and publish it. The lab has one rule:

> **If the check is red, nobody builds on it. Fix it first.**

In the next hour you write the workflow, start it by hand, break the code on purpose and watch the check turn red, fix it and watch
it turn green, add a status **badge** to the README, tag a **release** `v1.0.0` (Semantic Versioning) and publish it, and add a second
job that deploys only when a tag is pushed. You reuse `git push`, `git tag`-style refs (Experiments 9 and 10), the heredoc
`cat > file << 'EOF'` (Experiment 4), the Conventional Commits `ci:` and `fix:` (Experiment 5), and `gh` from Experiment 11.

## What you need

`git`, `python3`, a free **GitHub account** with your SSH key added (`ssh -T git@github.com` must greet you by name; Experiment 3 or
10), and the **GitHub CLI `gh`**, installed and logged in. Check:

```bash
gh auth status
```

It must say `Logged in to github.com account <your user name>`. If `gh` is missing or not logged in, install it (**macOS** `brew install
gh`; **Windows** `winget install --id GitHub.cli`, then open a new Git Bash; **Ubuntu** the `apt` instructions at
`https://github.com/cli/cli/blob/trunk/docs/install_linux.md`) and run `gh auth login`: choose **GitHub.com**, **SSH**, **Login with a web
browser**, copy the one-time code, paste it in the page that opens. If your terminal does not print English messages, run `export
LC_ALL=C` first, because the grader reads what Git and `gh` print. If a long output opens in a pager (a screen with `:` or `(END)` at
the bottom), press `q` to leave it.

## Rules

1. Work **only inside your clone** `rover-ci-lab`, on `main`. Push **only to `origin`**, your own GitHub repository. Never use `--force`.
2. Make your repository **Public** when you create it (Task 1): GitHub Actions is free and unlimited for public repositories.
3. A **workflow file is YAML**: indentation is part of the syntax, with **spaces only** (never tabs). Type the blocks exactly as shown.
4. Type the commands yourself. The grader checks that your pasted output matches what is really in your repository (your commit
   numbers, your user name), so output copied from a classmate is detected.
5. A workflow run takes **20 to 60 seconds** on GitHub. After a push, run `gh run list` until the newest run no longer shows a `*`
   (in progress), then paste. The steps say when to wait.
6. Keep the commit messages, tag names and file contents exactly as written.

## How you hand in your work

1. In Task 1 you copy `submission/outputs.template.txt` to `submission/outputs.txt`.
2. After **each step** (numbered **1.1**, **1.2**, ...), paste what the terminal printed under the matching `--- N.M` line of
   `submission/outputs.txt`, replacing `(paste output here)`. Do not edit or delete the `=== TASK` and `--- N.M` lines. Type your
   answers after the colon of the `ANSWER-n :` lines (the line just below each `# Qn` question).
3. Fill in your name and registration number at the top of the file.
4. Run the automatic grader whenever you want to see where you stand:

   ```bash
   python3 tests/grade.py
   ```

   It prints **PASS** or **FAIL** for every task, tells you exactly which check failed, and shows your score out of 100. The grader
   never uses the internet: it reads your clone and what you pasted.
5. When you are done, show the final grader output to your instructor (it is also saved in `submission/results.txt`), and submit
   `submission/outputs.txt` as instructed. The file is not pushed to GitHub on purpose: `.gitignore` keeps it local.

## Time plan

| Task | Time on the clock | Topic | Suggested time | Marks |
|---|---|---|---|---|
| 1 | 09:00 | The CI workflow | 14 min | 20 |
| 2 | 09:14 | Run it by hand | 8 min | 20 |
| 3 | 09:22 | Red, then green | 14 min | 25 |
| 4 | 09:36 | The badge, a tag and a release | 12 min | 20 |
| 5 | 09:48 | Deploy only on a tag | 8 min | 15 |
| | | Buffer for running the grader and fixing mistakes | 4 min | |

**Skipped a task, or running behind?** You do not lose the rest of the lab. A **catch-up box** at the start of the next task
brings your clone and your GitHub repository to the state you need, in a few lines. If you skipped several tasks, run their boxes in
order. You lose only the marks of the task you skipped.

---

## Task 1: The CI workflow (20 marks)

Get the project, give it a home of your own on GitHub, and teach GitHub to check it. The project already has code (`src/`) and tests
(`tests/`) that pass; it has no workflow yet.

```bash
cd ~
git clone https://github.com/qbit-glitch/26RA2308-gitlab-12-rover-ci-lab.git rover-ci-lab
cd rover-ci-lab
cp submission/outputs.template.txt submission/outputs.txt
git config user.name "Your Full Name"
git config user.email "your-email@example.com"
git remote rename origin upstream
```

Use your own real name and e-mail (not the placeholders, and not one of the teammates'). Do **not** use `--global` here. The clone's
`origin` points at the **course** repository; renaming it to `upstream` frees the name `origin` for **your own** repository.

Now, in the browser: sign in to github.com, click **New repository**, call it `rover-ci-lab`, choose **Public**, leave everything
else empty (**no** README, **no** .gitignore, **no** license) and click **Create repository**. Copy its SSH address. Then, back in
the terminal (replace `YOUR-USERNAME` with your GitHub user name):

```bash
git remote add origin git@github.com:YOUR-USERNAME/rover-ci-lab.git
git push -u origin main
```

* **1.1** Paste the output of `git push -u origin main`.

A **workflow** is a YAML file in `.github/workflows/`. It names an **event** (`on:`), one or more **jobs**, each job runs on a
**runner** (a fresh virtual machine, `runs-on:`) and is made of **steps**. Type the whole block (there is nothing to paste for it).

```bash
mkdir -p .github/workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest
      - name: Lint with flake8
        run: flake8 src --max-line-length=100
      - name: Run tests with pytest
        run: pytest -v
EOF
```

```bash
cat .github/workflows/ci.yml
```

* **1.2** Paste the output. Read it: the **event** is a push (or a pull request) on `main`; the **job** is `build-and-test`; the
  **runner** is `ubuntu-latest`; the **steps** check out the code, set up Python, install the two tools, lint `src` and run the tests.

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add lint and test workflow"
```

* **1.3** Paste the output of the `git commit` command.

```bash
git push origin main
```

* **1.4** Paste the output. This push is the event: GitHub starts the workflow by itself.

```bash
gh run list
```

* **1.5** Paste the output. The first column is the **status**: `*` means still running, a check mark means every step passed, `X`
  means a step failed. If you see `*`, wait ten seconds and run the command again until it has finished. Paste the finished line.
* Then type your answer to `ANSWER-1` in the file (there is no pasted output for it): which runner does the job run on? (the value
  of `runs-on`)

## Task 2: Run it by hand (20 marks)

Sometimes you want to run the checks without pushing anything: a manual trigger, `workflow_dispatch`. Add it to the `on:` block.

*Needs:* the pushed workflow of Task 1.

> **Catch-up box: only if you skipped Task 1.** Make your repository on GitHub as described in Task 1 (the browser part, and the
> `git remote add origin ...` line). Then run these lines, once. They do what Task 1 does. If you did Task 1, do **not** run them.
> There is nothing to paste for them, and you lose only the marks of Task 1.
>
> ```bash
> git push -u origin main
> mkdir -p .github/workflows
> cat > .github/workflows/ci.yml << 'EOF'
> name: CI
> on:
>   push:
>     branches: [ main ]
>   pull_request:
>     branches: [ main ]
> jobs:
>   build-and-test:
>     runs-on: ubuntu-latest
>     steps:
>       - name: Check out the repository
>         uses: actions/checkout@v4
>       - name: Set up Python
>         uses: actions/setup-python@v5
>         with:
>           python-version: '3.11'
>       - name: Install dependencies
>         run: |
>           python -m pip install --upgrade pip
>           pip install flake8 pytest
>       - name: Lint with flake8
>         run: flake8 src --max-line-length=100
>       - name: Run tests with pytest
>         run: pytest -v
> EOF
> git add .github/workflows/ci.yml
> git commit -m "ci: add lint and test workflow"
> git push origin main
> ```

Retype the whole file with one more line (`workflow_dispatch:`) under `on:`. There is nothing to paste for this block.

```bash
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:   # manual trigger
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest
      - name: Lint with flake8
        run: flake8 src --max-line-length=100
      - name: Run tests with pytest
        run: pytest -v
EOF
```

```bash
git commit -am "ci: add manual workflow_dispatch trigger"
```

* **2.1** Paste the output of `git commit`.

```bash
git push origin main
```

* **2.2** Paste the output.

Now start the workflow by hand: no push, no commit, just a request to GitHub.

```bash
gh workflow run ci.yml
```

* **2.3** Paste the output. (If `gh` says `Workflow does not have 'workflow_dispatch' trigger`, the push of 2.2 has not arrived or
  the line is missing from the file: check with `cat .github/workflows/ci.yml`.)

```bash
gh run list --limit 3
```

* **2.4** Paste the output once the runs have finished (wait and repeat if you see `*`). You see two new runs: one whose EVENT is
  `push` (your commit) and one whose EVENT is `workflow_dispatch` (your manual request). Its title is the workflow's name, `CI`,
  because no commit started it.

## Task 3: Red, then green (25 marks)

A check that never fails proves nothing. Break the code on purpose with a mistake that the linter catches: an `import` that nothing
uses.

*Needs:* the workflow of Task 2.

> **Catch-up box: only if you skipped Task 2.** Run these lines, once. They do what Task 2 does. If you did Task 2, do **not** run
> them. There is nothing to paste for them, and you lose only the marks of Task 2. (If you skipped Task 1 as well, run its box first.)
>
> ```bash
> cat > .github/workflows/ci.yml << 'EOF'
> name: CI
> on:
>   push:
>     branches: [ main ]
>   pull_request:
>     branches: [ main ]
>   workflow_dispatch:   # manual trigger
> jobs:
>   build-and-test:
>     runs-on: ubuntu-latest
>     steps:
>       - name: Check out the repository
>         uses: actions/checkout@v4
>       - name: Set up Python
>         uses: actions/setup-python@v5
>         with:
>           python-version: '3.11'
>       - name: Install dependencies
>         run: |
>           python -m pip install --upgrade pip
>           pip install flake8 pytest
>       - name: Lint with flake8
>         run: flake8 src --max-line-length=100
>       - name: Run tests with pytest
>         run: pytest -v
> EOF
> git commit -am "ci: add manual workflow_dispatch trigger"
> git push origin main
> ```

Add a helper function to the detector, and an `import os` that it does not need. Type the whole block (nothing to paste for it).

```bash
cat > src/detector.py << 'EOF'
"""Obstacle detector for the Kestrel-1 camera."""
import os

THRESHOLD_CM = 30


def detect_obstacle(distance_cm, threshold_cm=THRESHOLD_CM):
    """Return True when something is closer than threshold_cm."""
    return distance_cm < threshold_cm


def closest(distances):
    """Return the smallest distance in the list, or None when it is empty."""
    return min(distances) if distances else None
EOF
```

```bash
git commit -am "feat(vision): add distance helper"
```

* **3.1** Paste the output of `git commit`.

```bash
git push origin main
```

* **3.2** Paste the output.

```bash
gh run list --limit 1
```

* **3.3** Paste the output once the run has finished (repeat until the `*` is gone). The status is an **`X`**: the run failed, and
  GitHub shows a red cross next to your commit.

Why did it fail? Ask for the log of the failed step only. First put the number of the newest run in a variable (nothing to paste),
then read its log:

```bash
RUN=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
```

```bash
gh run view $RUN --log-failed
```

* **3.4** Paste the output of the second command. Find the line `src/detector.py:2:1: F401 'os' imported but unused`: the file, the
  line, the **flake8 code** and the problem. (If your terminal does not keep the variable, type the number printed by `gh run list` in
  place of `$RUN`.)

Fix it: retype the file without the `import os` line (nothing to paste for the block), commit, push.

```bash
cat > src/detector.py << 'EOF'
"""Obstacle detector for the Kestrel-1 camera."""

THRESHOLD_CM = 30


def detect_obstacle(distance_cm, threshold_cm=THRESHOLD_CM):
    """Return True when something is closer than threshold_cm."""
    return distance_cm < threshold_cm


def closest(distances):
    """Return the smallest distance in the list, or None when it is empty."""
    return min(distances) if distances else None
EOF
```

```bash
git commit -am "fix(vision): remove unused import"
```

* **3.5** Paste the output of `git commit`.

```bash
git push origin main
```

* **3.6** Paste the output.

```bash
gh run list --limit 3
```

* **3.7** Paste the output once the newest run has finished. Read it from the top: a **check mark** for the fix, an **`X`** for the
  commit with the unused import, a check mark for the manual run before it. The history of the checks is the history of your commits.
* Then type your answer to `ANSWER-2` in the file: which flake8 code did the failed run report? (a letter and three digits)

## Task 4: The badge, a tag and a release (20 marks)

A **badge** in the README shows the state of the latest run to everybody who visits the repository. A **tag** marks the commit that
is a release, and **Semantic Versioning** names it `MAJOR.MINOR.PATCH`: MAJOR changes when the new version breaks old code, MINOR when
it adds a feature without breaking anything, PATCH when it only fixes a bug.

*Needs:* the green run of Task 3.

> **Catch-up box: only if you skipped Task 3.** Run these lines, once. They do what Task 3 does and make the same two commits. If
> you did Task 3, do **not** run them. There is nothing to paste for them, and you lose only the marks of Task 3. (If you skipped
> Task 2 as well, run its box first.)
>
> ```bash
> cat > src/detector.py << 'EOF'
> """Obstacle detector for the Kestrel-1 camera."""
> import os
>
> THRESHOLD_CM = 30
>
>
> def detect_obstacle(distance_cm, threshold_cm=THRESHOLD_CM):
>     """Return True when something is closer than threshold_cm."""
>     return distance_cm < threshold_cm
>
>
> def closest(distances):
>     """Return the smallest distance in the list, or None when it is empty."""
>     return min(distances) if distances else None
> EOF
> git commit -am "feat(vision): add distance helper"
> git push origin main
> cat > src/detector.py << 'EOF'
> """Obstacle detector for the Kestrel-1 camera."""
>
> THRESHOLD_CM = 30
>
>
> def detect_obstacle(distance_cm, threshold_cm=THRESHOLD_CM):
>     """Return True when something is closer than threshold_cm."""
>     return distance_cm < threshold_cm
>
>
> def closest(distances):
>     """Return the smallest distance in the list, or None when it is empty."""
>     return min(distances) if distances else None
> EOF
> git commit -am "fix(vision): remove unused import"
> git push origin main
> ```

Rewrite the README with the badge at the top (replace `YOUR-USERNAME` with your GitHub user name; nothing to paste for this block).

```bash
cat > README.md << 'EOF'
![CI](https://github.com/YOUR-USERNAME/rover-ci-lab/actions/workflows/ci.yml/badge.svg)

# Kestrel-1 rover

Vision and planning code for the Kestrel-1 rover.
EOF
```

```bash
git commit -am "docs: add CI status badge to README"
```

* **4.1** Paste the output of `git commit`.

```bash
git push origin main
```

* **4.2** Paste the output. Open your repository on github.com: the badge shows `passing` in green.

Tag this commit as version 1.0.0. `-a` makes an **annotated** tag, a Git object of its own with a message, the author and a date; a
tag made without `-a` would be a lightweight tag, only a name. There is nothing to paste for the first line.

```bash
git tag -a v1.0.0 -m "First stable release of the vision module"
```

```bash
git tag
git cat-file -t v1.0.0
```

* **4.3** Paste the output of the two commands: the tag is listed, and its type is `tag` (a lightweight tag would say `commit`).

```bash
git push origin v1.0.0
```

* **4.4** Paste the output. `* [new tag]` means GitHub did not have this tag. (A plain `git push` never sends tags: you push them by
  name.)

```bash
gh release create v1.0.0 --title "v1.0.0" --notes "Initial stable release."
```

* **4.5** Paste the output: the address of your **GitHub Release**, a page with the release notes built on the tag.

```bash
gh release list
```

* **4.6** Paste the output.
* Then type your answer to `ANSWER-3` in the file: which part of `MAJOR.MINOR.PATCH` changes when a release breaks backward
  compatibility? (one word)

## Task 5: Deploy only on a tag (15 marks)

Advanced: a second job that builds an artifact (a `.tar.gz` of the code) but only when a **tag** is pushed, and only after the checks
pass. Two changes to the workflow: the workflow must also start on tags starting with `v` (`tags: [ 'v*' ]`), and the new job has
`needs: build-and-test` and `if: startsWith(github.ref, 'refs/tags/v')`.

*Needs:* the release of Task 4.

> **Catch-up box: only if you skipped Task 4.** Run these lines, once. They do what Task 4 does. If you did Task 4, do **not** run
> them. There is nothing to paste for them, and you lose only the marks of Task 4. (If you skipped Task 3 as well, run its box first.)
> Replace `YOUR-USERNAME` with your GitHub user name.
>
> ```bash
> cat > README.md << 'EOF'
> ![CI](https://github.com/YOUR-USERNAME/rover-ci-lab/actions/workflows/ci.yml/badge.svg)
>
> # Kestrel-1 rover
>
> Vision and planning code for the Kestrel-1 rover.
> EOF
> git commit -am "docs: add CI status badge to README"
> git push origin main
> git tag -a v1.0.0 -m "First stable release of the vision module"
> git push origin v1.0.0
> gh release create v1.0.0 --title "v1.0.0" --notes "Initial stable release."
> ```

Retype the whole workflow with the tags filter and the deploy job. There is nothing to paste for this block.

```bash
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:   # manual trigger
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest
      - name: Lint with flake8
        run: flake8 src --max-line-length=100
      - name: Run tests with pytest
        run: pytest -v
  deploy:
    needs: build-and-test
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4
      - name: Build an artifact
        run: |
          mkdir dist
          tar -czf dist/rover-ci-lab.tar.gz src
      - name: Upload the artifact
        uses: actions/upload-artifact@v4
        with:
          name: rover-ci-lab
          path: dist/
EOF
```

```bash
git commit -am "ci: deploy a build artifact when a tag is pushed"
```

* **5.1** Paste the output of `git commit`.

```bash
git push origin main
```

* **5.2** Paste the output. This push starts a run on the branch: the `deploy` job is **skipped**, because `main` is not a tag.

Now tag this commit as version 1.1.0 (a new feature, backward compatible: MINOR) and push the tag. There is nothing to paste for the
first line.

```bash
git tag -a v1.1.0 -m "Add the distance helper"
```

```bash
git push origin v1.1.0
```

* **5.3** Paste the output.

```bash
gh run list --limit 3
```

* **5.4** Paste the output once the newest run has finished. The newest run is on the **tag**: its BRANCH column says `v1.1.0`.

```bash
RUN=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
```

```bash
gh run view $RUN
```

* **5.5** Paste the output of the second command. Under `JOBS` there are **two** jobs, both with a check mark: `build-and-test` and
  `deploy`. On the earlier run of the branch, `deploy` was skipped.

## Finish

```bash
python3 tests/grade.py
```

You want to see `PASS` for all five tasks and `TOTAL: 100/100`. Anything marked `FAIL` is listed with the reason; fix it and run the
grader again.

## Marks

| Task | Marks | How it is checked |
|---|---|---|
| 1 | 20 | the push, the workflow file, the commit, the push and the first run are pasted; one answer; the workflow file really is the file of the handout |
| 2 | 20 | the commit, the push, `gh workflow run` and the run list are pasted; `ci.yml` really has the `workflow_dispatch` trigger |
| 3 | 25 | the commit, the push, the failed run, its log, the fix, the push and the run list are pasted; one answer; the two commits really are the broken and the fixed detector |
| 4 | 20 | the badge commit, the push, the tag listing and its type, the tag push, the release address and the release list are pasted; one answer; `v1.0.0` really is an annotated tag on the badge commit |
| 5 | 15 | the commit, the push, the tag push, the run list and the run view are pasted; `ci.yml` really has the deploy job, and `v1.1.0` really is an annotated tag on that commit |

A task shows **PASS** only when every check in it passes, and you earn marks for each check that passes even if the task as a whole
fails.

## If something goes wrong

* **You skipped a task and a later one fails.** Run the catch-up box at the start of the task after the one you skipped (in order,
  if you skipped several), then carry on.
* **`gh: command not found` or `To get started with GitHub CLI, please run: gh auth login`.** Do the part "What you need" says.
* **`Permission denied (publickey)` when you push.** GitHub does not know your SSH key: redo the key step (Experiment 3 or 10), check
  with `ssh -T git@github.com`.
* **`error: remote origin already exists`.** The clone's `origin` is still the course repository. Run `git remote rename origin
  upstream`, then `git remote add origin ...` again.
* **Step 1.1 is rejected, or says `remote contains work`.** You created the repository with a README or a licence, so it is not
  empty. Delete it (its Settings, at the bottom), create it again empty and Public, and push again.
* **`gh run list` says `No runs found`, or stays empty.** The workflow did not start. Check that the file is exactly
  `.github/workflows/ci.yml` (the folder name starts with a dot), that it was committed and pushed (`git log --oneline`, and look at
  your repository on github.com), and that the indentation uses spaces and matches the handout. On github.com, the **Actions** tab
  shows a message when GitHub cannot read a workflow file.
* **The first run fails although you did not break anything.** Open the log: `gh run view $RUN --log-failed`. The usual causes are a
  typo in `flake8 src --max-line-length=100` or `pytest -v`, or a tab in the YAML. Retype the file as in the handout, commit, push.
* **`gh run list` shows `*` for a long time.** GitHub's queue can take a minute. Wait; if it is still `*` after five minutes, tell your
  instructor.
* **`$RUN` is empty or `gh` asks you to choose a run.** Your terminal did not keep the variable. Type the number from `gh run list`
  (the ID column) in place of `$RUN`.
* **`could not create workflow dispatch event: ... does not have 'workflow_dispatch' trigger`.** The push of 2.2 has not arrived, or
  the line is missing from `ci.yml`. `cat .github/workflows/ci.yml` and compare with Task 2.
* **`tag 'v1.0.0' already exists`.** You ran `git tag -a` twice. Carry on with `git tag` (it lists it).
* **`git cat-file -t v1.0.0` says `commit`, not `tag`.** You made the tag without `-a`. Delete it with `git tag -d v1.0.0` and make it
  again with the command of the handout (before you push it).
* **`gh release create` says the tag does not exist.** Push it first: `git push origin v1.0.0`.
* **An editor opened and asked for a commit message.** You left out `-m "..."`. Save and exit (nano: `Ctrl+O`, `Enter`, `Ctrl+X`; vim:
  `Esc`, then `:wq` and `Enter`).
* **`tests/grade.py` says it cannot find the starting commit.** You are not inside your clone: `cd ~/rover-ci-lab`.
