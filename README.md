# ML-Fest

The platform behind the ML competition at Yugam 2026, the tech fest of Kumaraguru College of Technology. It has three rounds, each a separate Django app with its own database: an MCQ quiz, a notebook-debugging round, and an ML capture-the-flag where the server trains and scores submissions. One Docker Compose file starts all of them.

Built by Team Qernels. I was the main developer.

## The three rounds

Every round has registration, an admin approval step, an event start/stop switch, a per-participant timer that starts when that person enters, and a leaderboard. Each round has its own user table (`r1_user`, `r2_user`, `r3_user`) and its own Postgres database.

**Round 1, MCQ quiz** (`Round 1/quiz`). 60 ML questions loaded from `Final-Mixed_60_MCQ.csv` with the `import_questions` command. Answers save over AJAX. The default timer is 30 minutes. Switching tabs more than the allowed number of times (default 3) auto-submits and disqualifies. Ranking is correct answers, then time taken.

**Round 2, debugging challenge** (`Round 2/debugchallenge`). Participants download two notebooks with planted bugs, Titanic classification (11 bugs) and California Housing regression (8 bugs), fix them locally and upload the `.ipynb` files. Grading is manual: an admin assigns an evaluator, who marks each bug as fixed or not, one point per bug. This round has its own README with setup details.

**Round 3, ML CTF** (`Round 3/ctf`). Five challenges, each checked by an endpoint in `ctf/evaluation.py`. The server only returns a flag when the check passes:

1. Data poisoning: submit a modified training CSV so a logistic regression predicts the planted "thief" row as a citizen.
2. Constrained poisoning: same goal, but the CSV is diffed against the original and rejected if the protected row or the label column changed.
3. Model repair: upload a fixed `.pkl`; it must reach 100% accuracy on the dataset.
4. Model evaluation: submit predicted probabilities on the bank dataset; the server rebuilds the test split and requires ROC-AUC of at least 0.85.
5. Model recovery: recover a linear regression exactly (R² of 1.0, MSE 0, max error 0).

Flags are per user: `UserFlag.generate_flag()` hashes the secret key, user id and challenge order with SHA-256 and formats it as `MLFEST{<prefix>_<8 hex>}`, so a flag only works for the person it was issued to. Notebooks log in through a JSON endpoint (`notebook_login`). Points are split into flag points and explanation points, and an assigned evaluator has to approve them before they reach the leaderboard.

## Stack

Django 5.1, PostgreSQL 16, Gunicorn, WhiteNoise, scikit-learn, pandas, numpy, joblib, openpyxl (XLSX export), Docker Compose. The frontend is plain Django templates, CSS and JS.

## Run everything with Docker

```bash
git clone https://github.com/DCode-v05/ML-Fest.git
cd ML-Fest
docker-compose up --build
```

This starts Postgres on port 7737 and the rounds on 7738 (quiz), 7739 (debug) and 7740 (CTF). `init-db.sh` creates `mlfest_r2` and `mlfest_r3` on first boot; Round 1 uses the default `mlfest_r1`. Admin credentials are shared across the three rounds.

`docker-compose.yml` reads `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`, `DEBUG` and `ALLOWED_HOSTS` from a `.env` in the repo root. It has fallback defaults for all of them, so set your own before running anything public.

## Run one round locally

Each round is a standalone Django project. For Round 2:

```bash
cd "Round 2"
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_challenges
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:7741
```

Round 1 seeds with `import_questions`. Round 3 seeds with `seed_challenges` and `create_admin`.

## Project structure

```
docker-compose.yml   Postgres plus the three apps
init-db.sh           creates the extra databases
shared_auth/         a consolidated CustomUser model (role, approval, points)
Round 1/             quiz app, question CSV
Round 2/             debugchallenge app, buggy notebooks and datasets
Round 3/             ctf app, challenge notebooks, datasets, tampered model
DB Backup/           pg_dump files for the three round databases
```

`Round 1/` and `Round 3/` also have their own Dockerfile.prod and entrypoint scripts. `Round 2/` and the root have Render config for single-service deploys.

## Notes

- `DB Backup/` holds dumps taken after the event, so they contain real registrations. Check them before making the repo public.
- `Round 2/quiz/views.py` is a leftover; `quiz` is not an installed app in Round 2.
- Round 2's views serve `ML_Challenge_Notebooks.zip` from `challenge_materials/`. The setup ZIP and scripts its README mentions are not in the repo.
