# ML Fest

**A three-round machine learning competition platform — an MCQ quiz, a notebook-debugging round, and a server-evaluated ML capture-the-flag — run as one Docker Compose stack.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![Django](https://img.shields.io/badge/Django_5.1-092E20?style=flat&logo=django&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=flat&logo=postgresql&logoColor=white) ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikitlearn&logoColor=white) ![pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white) ![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?style=flat&logo=docker&logoColor=white) ![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=flat&logo=gunicorn&logoColor=white)

## Overview

ML Fest is the platform that ran the ML competition at **Yugam 2026**, the annual tech fest of Kumaraguru College of Technology (KCT). It was built by **Team Qernels** under the college's iQube innovation center, and I was the primary developer.

The event has three rounds, each with a completely different format: a timed MCQ quiz, a debug-the-notebook challenge graded by human evaluators, and an ML-security capture-the-flag where the server actually trains models and scores submissions. Rather than cram three unrelated formats into one app, I built three separate Django applications — each with its own database and auth table — and wired them together behind a single `docker-compose.yml` so the whole event comes up with one command.

It wasn't just a demo. The repo ships `pg_dump` backups of all three round databases (`DB Backup/round-1.sql`, `round-2.sql`, `round-3.sql`) captured after the event, so the platform ran live with real participant registrations, submissions, and scores.

## Key Features

- **Three independent rounds**, each a full Django app: MCQ quiz, notebook debugging, and an ML CTF.
- **One-command deployment** — a single Postgres instance serving three databases plus three app containers, all defined in one Compose file.
- **Registration → admin-approval gate** in every round; nobody competes until an admin approves them.
- **Per-participant countdown timers** — each person's clock starts when *they* enter the challenge, not at a global gun.
- **Fullscreen proctoring with tab-switch detection** — leaving the tab too many times (default 3) auto-submits and disqualifies.
- **Live leaderboards** with auto-refresh, public/private toggle, and a time-based tiebreaker.
- **XLSX export** of results from any round's admin dashboard (via openpyxl).
- **Evaluator role and grading workflows** in Rounds 2 and 3 — admins assign evaluators to participants, who then grade submissions.
- **Server-side ML evaluation** in Round 3 — notebooks POST their artifacts to endpoints that train/score real scikit-learn models and only return a flag on success.
- **Per-user cryptographic flags** — every CTF participant gets their own deterministic SHA-256 flags, so a leaked flag is useless to anyone else.
- **Jupyter integration** — a JSON login endpoint lets a participant's notebook authenticate against the platform directly.
- **Management commands** to seed each round (`import_questions`, `setup_challenges`, `seed_challenges`, `create_admin`).

## How It Works

### Shared platform

All three rounds are Django 5.1 apps that share the same patterns: a custom user model extending `AbstractUser`, an admin approval flag, an event start/stop switch, per-participant timers, and leaderboards. Each round writes to its own Postgres database (`mlfest_r1`, `mlfest_r2`, `mlfest_r3`) and its own auth table (`r1_user`, `r2_user`, `r3_user`), so the rounds are fully isolated even though they share one database server and one admin login. There's also a `shared_auth/` app holding a consolidated `CustomUser` (role + `is_approved` + `total_points` + `last_flag_at`) that unifies the auth fields the rounds had diverged on.

Deployment is one `docker-compose.yml`: a `postgres:16-alpine` container exposed on port **7737**, and three Gunicorn/WhiteNoise app containers on **7738 / 7739 / 7740**. An `init-db.sh` mounted into the Postgres init directory creates the round-2 and round-3 databases automatically on first boot; round 1 owns the default database. Everything is configured through environment variables with sane defaults.

### Round 1 — MCQ Quiz (`quiz` app, port 7738)

A timed, proctored multiple-choice round. A 60-question mixed-ML question bank (`Final-Mixed_60_MCQ.csv`) is loaded with a custom `import_questions` management command. Each participant gets a 30-minute individual timer; answers save over AJAX as they go. The `Participant` model tracks `tab_switch_count`, and crossing the limit flips `tab_switch_violated` and auto-submits. Scoring is correct-answer count with `time_taken_ms` as the tiebreaker, ordered straight in the model's `Meta`. Models: `Event`, `Question`, `Participant`, `Answer`.

### Round 2 — ML Debugging Challenge (`debugchallenge` app, port 7739)

Participants download two deliberately broken Jupyter notebooks — **Titanic classification (11 bugs)** and **California Housing regression (8 bugs)** — fix them locally in a 60-minute fullscreen window, and upload the corrected `.ipynb` files (validated as notebooks, 10 MB cap). Downloads come as two ZIPs: one with the notebooks plus data, and one with environment setup scripts (`setup.bat` / `setup.sh` that build a `Task_2_venv` and install numpy/pandas/matplotlib/seaborn/scikit-learn). Both are available right after approval so people can set up before the clock starts.

Grading is human-in-the-loop. Admins assign an evaluator to each participant; the evaluator opens the submission and marks each bug fixed-or-not in a per-bug JSON map (`bug_results`), and the score is the count of correctly fixed bugs (1 point each). Models: `Event`, `Challenge`, `Participant` (with participant/evaluator roles and an evaluator FK), `Evaluation` (per-bug JSON), `Submission`. This is the most documented round — it has its own `README.md`.

### Round 3 — ML Capture The Flag (`ctf` app, port 7740)

The technical centerpiece. Five "Gatekeeper"-themed challenges of rising difficulty, each backed by a live evaluation endpoint in `ctf/evaluation.py`. A participant solves in their notebook, POSTs the artifact, and the server runs the actual ML check — returning a flag only on a genuine pass:

1. **Data Poisoning** (Easy) — submit a tampered training CSV; the server fits a `LogisticRegression` and checks whether the planted "thief" row (ID 10) is now predicted as a citizen.
2. **Constrained Poisoning** (Medium) — same goal, but the server first diffs your CSV against the original and rejects it if the protected last row or the `Label` column was touched.
3. **Model Repair** (Hard) — upload a fixed `.pkl`; the server `joblib`-loads it and requires exactly **100% accuracy** on the gatekeeper dataset.
4. **Model Evaluation** ("The Model That Refused To Learn", Expert) — submit prediction probabilities on the bank-marketing dataset; the server reproduces `y_test` with the exact `random_state=42` preprocessing pipeline (label-encode, class-balance, scale, stratified split) and computes ROC-AUC with a hand-rolled trapezoidal integration, requiring **AUC ≥ 0.85**.
5. **Model Recovery** ("The Weight of Truth", Medium) — recover a `LinearRegression` exactly; the server requires **R² = 1.0, MSE = 0, and max absolute error = 0**.

The notable engineering is the flag system. Instead of one shared flag per challenge, every participant gets five **per-user flags** generated on registration: `UserFlag.generate_flag()` hashes `SECRET_KEY:user_id:challenge_order` with SHA-256 and formats it as `MLFEST{<prefix>_<8 hex>}`. A flag is therefore worthless to anyone but the person it was minted for. An `ApprovalGateMiddleware` blocks unapproved users from everything except the auth/home pages, and a `notebook_login` JSON endpoint lets Jupyter notebooks authenticate so submissions are tied to the right user even when they come from outside a browser session.

Scoring here is dual: separate **flag points** and **explanation points**, both subject to evaluator approval before they count. A correct submission creates a pending `Score`; an assigned evaluator approves it with a point split, and `recalculate_points()` rolls the approved totals into the leaderboard, which breaks ties by who reached the score first (`last_flag_at`). Models: `CustomUser` (RBAC + points), `SiteSettings` (singleton event/leaderboard/reveal switches), `Challenge`, `Flag`, `ChallengeResource`, `Submission`, `Score`, `EvaluatorAssignment`, `UserFlag`.

## Results / Highlights

- Ran live for **Yugam 2026** at KCT; post-event Postgres dumps for all three rounds are included (~95 KB / 78 KB / 109 KB), so the schema and real event data are preserved.
- Round 1 ships a **60-question** ML quiz bank with full registration → approval → quiz → result → leaderboard flow.
- Round 3 evaluates submissions against real ML thresholds: **100% accuracy** (model repair), **ROC-AUC ≥ 0.85** (model evaluation, AUC computed by hand), and an exact fit of **R² = 1.0 / MSE = 0** (weight recovery).
- One Compose stack brings up **1 database + 3 apps** across four ports with a single `docker-compose up`.

## Tech Stack

- **Language:** Python 3.12+ (with Jupyter notebooks as challenge material)
- **Framework:** Django 5.1.5, django-widget-tweaks
- **Data / ML:** scikit-learn, pandas, numpy, joblib (Round 3 evaluation)
- **Database:** PostgreSQL 16 (one server, three databases)
- **Serving / infra:** Gunicorn (WSGI), WhiteNoise (static), Docker & Docker Compose, dj-database-url / python-dotenv for config, openpyxl for XLSX export
- **Frontend:** Django templates with vanilla HTML / CSS / JavaScript (no build step)

## Getting Started

### Prerequisites
- Docker and Docker Compose (the supported path — brings up all three rounds together)
- Or, for a single round locally: Python 3.12+ and PostgreSQL 16

### Installation
```bash
git clone https://github.com/DCode-v05/ML-Fest.git
cd ML-Fest
```

### Running (all three rounds via Docker Compose)
Optionally create a `.env` in the project root to override defaults:
```
DB_USER=postgres
DB_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
ADMIN_USERNAME=admin@example.com
ADMIN_PASSWORD=your_admin_password
ADMIN_EMAIL=admin@example.com
DEBUG=False
ALLOWED_HOSTS=*
```
Then bring up the stack:
```bash
docker-compose up --build
```
This starts PostgreSQL on `7737` and the three rounds on `7738` (Quiz), `7739` (Debug), `7740` (CTF). Admin credentials are shared across all three rounds.

### Running a single round locally
Each round is a standalone Django project. For example, Round 2:
```bash
cd "Round 2"
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_challenges       # seeds the event + challenges
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:7741
```
Round 1 uses `import_questions` to load the MCQ bank; Round 3 uses `seed_challenges` and `create_admin`.

## Usage

- **Admins** log into any round's dashboard to start/stop the event, approve participants, assign evaluators, toggle leaderboard visibility, reset attempts, and export results to XLSX.
- **Participants** register, wait for approval, then compete in the active round inside their personal timer. In Round 2 they download the notebooks and upload fixes; in Round 3 they solve in a notebook and POST artifacts (or submit their per-user flag) to the evaluation endpoints.
- **Evaluators** (Rounds 2 and 3) review their assigned submissions — grading each bug fix in Round 2, or approving flag and explanation points in Round 3.
- **Leaderboards** update live; admins can flip them public or private and export at any time.

## Project Structure

```
ML-Fest/
├── docker-compose.yml          # 1 Postgres + 3 round apps, ports 7737–7740
├── init-db.sh                  # creates mlfest_r2 / mlfest_r3 on first DB boot
├── shared_auth/                # consolidated CustomUser (role, approval, points)
│
├── Round 1/                    # MCQ Quiz (port 7738)
│   ├── quiz/
│   │   ├── models.py           # Event, Question, Participant, Answer
│   │   ├── views.py            # quiz flow, AJAX answer save, admin dashboard
│   │   └── management/commands/import_questions.py
│   ├── Final-Mixed_60_MCQ.csv  # 60-question ML bank
│   └── Dockerfile.prod · requirements.txt · entrypoint.prod.sh
│
├── Round 2/                    # ML Debugging Challenge (port 7739)
│   ├── debugchallenge/
│   │   ├── models.py           # Event, Challenge, Participant, Evaluation, Submission
│   │   ├── views.py            # challenge flow, evaluator panel, downloads, grading
│   │   └── management/commands/setup_challenges.py
│   ├── challenge_materials/    # buggy notebooks + titanic/california CSVs
│   └── README.md               # the round's own setup + usage docs
│
├── Round 3/                    # ML Capture The Flag (port 7740)
│   ├── ctf/
│   │   ├── models.py           # Challenge, Flag, Score, UserFlag, EvaluatorAssignment, …
│   │   ├── evaluation.py       # 5 server-side ML evaluation endpoints
│   │   ├── challenge_catalog.py# canonical challenge metadata (seeded to DB)
│   │   ├── middleware.py       # ApprovalGateMiddleware
│   │   └── management/commands/ {seed_challenges, create_admin}
│   └── challenge_files/        # notebooks, datasets, tampered .pkl model
│
└── DB Backup/                  # pg_dump exports of all three round databases
```

---

## Contact

<table>
  <tr><td><b>Portfolio:</b> <a href="https://www.denistan.me">Denistan</a></td><td><b>LinkedIn:</b> <a href="https://www.linkedin.com/in/denistanb">denistanb</a></td></tr>
  <tr><td><b>GitHub:</b> <a href="https://github.com/DCode-v05">DCode-v05</a></td><td><b>LeetCode:</b> <a href="https://leetcode.com/u/Denistan_B">Denistan_B</a></td></tr>
  <tr><td colspan="2" align="center"><b>Email:</b> <a href="mailto:denistanb05@gmail.com">denistanb05@gmail.com</a></td></tr>
</table>

Made with ❤️ by **Denistan B**
