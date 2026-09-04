# Run a work unit

Needs: Python 3.11+, git, a GitHub account. gmpy2 wheels install on Linux, macOS and Windows (x86-64 and arm64).

Honest framing first: the whole pilot range (n ≤ 200 000) is about 2.5 core-days of work; one desktop
could finish it. The pilot exists to rehearse the identity → verification → credit → OEIS pipeline with
real volunteers, on a design that stays correct at the next scale (n ≤ 10^6, about 1.5 core-years).
Because the pilot is small, **CI recomputes every line of every result**; a second volunteer's result
is an additional, credit-bearing double check, not the trust anchor.

1. Fork and clone once:

       gh repo fork greenrobotllc/optimus-prime-triangle --clone
       cd optimus-prime-triangle
       python -m venv .venv
       . .venv/bin/activate            # Windows: .venv\Scripts\activate
       pip install -e distributed      # installs gmpy2 and cryptography only

   No gmpy2 wheel for your platform? `oeis-home run` falls back to pure Python (about 20× slower).

2. Create your key and registration file (once):

       oeis-home keygen
       oeis-home register --login YOURLOGIN --display-name "Your Name" [--oeis-credit-name "Your Real Name"]

   `register` looks up your numeric GitHub id online; offline, pass `--github-id N` (find it at
   `https://api.github.com/users/YOURLOGIN`). The login must be your own GitHub login: CI compares it with
   the PR author. This writes `distributed/contributors/yourlogin.json`. It can go in the same pull request as your first
   result. Use a GitHub noreply commit e-mail if you do not want your e-mail in the public history.

3. Pick and run a unit (claims are optional; two people finishing the same unit is the double check):

       oeis-home claim --count 1                     # prints e.g. lehmer-q2-00020000-00021000
       oeis-home run --unit lehmer-q2-00020000-00021000

   Progress is printed per line; a checkpoint is written every 60 s; rerun the same command to resume.
   Output: `distributed/results/lehmer-q2/<unit>/YOURLOGIN.json` (signed).

4. Check and submit (one pull request per batch of units; always branch from main):

       oeis-home check distributed/results/lehmer-q2/<unit>/YOURLOGIN.json
       git fetch upstream && git checkout -b results/YOURLOGIN/<unit> upstream/main
       git add distributed/contributors/YOURLOGIN.json distributed/results distributed/claims
       git commit -m "results: lehmer-q2 <unit> by YOURLOGIN"
       git push -u origin HEAD
       gh pr create --fill

CI recomputes every line of your file with its own code and your personal test base; a maintainer merges
green PRs within about two days. The results page is rebuilt on every merge.

## Rules

- One key per GitHub account, one account per key. Never edit a signed file. Merged results are add-only:
  if one of yours turns out wrong, open an issue so a maintainer withdraws it; a fresh run of the same unit
  is written as `YOURLOGIN-2.json` (`oeis-home run --force`).
- You cannot be the second result for your own unit (two keys of one account count once).
- Key rotation: `oeis-home register ... --old-key <old file>`; your earlier results stay valid.
- Discoverer = earliest pull request (creation time) containing a verified probable-prime line;
  verifier = second distinct account (or a maintainer verifier key). Both are named on the page and in
  the OEIS extension line, using your `--oeis-credit-name` if you gave one.
- Results are CC0; code is MIT. Only your login and display name are published.
- No GitHub account? Run steps 2–3 with `--login ext-yourname` and e-mail the two files to a maintainer.
