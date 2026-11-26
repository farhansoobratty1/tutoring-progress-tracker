# Tutoring Progress Tracker

A small web app I'm building for my GCSE and 11+ tutoring students. After each session I record how a student did on each topic. The app then shows where they're improving and **flags the topics that need work**. It can also **generate a practice set** that focuses on those weak areas, at a difficulty that matches how the student is doing.

> **Status: early version, in progress (November 2026).** The core loop works: record scores, spot weak areas, print a practice set. There's no login yet, so it's meant for me to use locally rather than for students or parents to log into. See [What's next](#whats-next).

## Why

With three students in different year groups and subjects, it was getting hard to keep track of what each one had covered and where they were slipping. Parents also ask, fairly, how their child is getting on. I wanted something that would:

- keep every student's scores in one place, topic by topic
- show trends instead of single results, so one bad week doesn't hide steady progress (and vice versa)
- save me time by building targeted homework instead of me picking questions by hand

## Features

- **Students:** name, year group, subject (GCSE Maths, GCSE Physics or 11+ Maths) and a target percentage.
- **Recording scores:** marks out of a total for a topic, with an optional date and note. Invalid entries are rejected, such as marks higher than the total or a topic from the wrong subject.
- **Topic overview:** attempts, latest score, recent average against the student's target, a trend (improving, steady or declining) and the full score history for each topic.
- **Weak-area flags:** a topic is flagged if its average over the last 3 attempts is below 60%, or if the latest score dropped 15 or more points below the earlier average. The table shows why each topic was flagged.
- **Practice sets:**
  - Questions are shared out in proportion to how far each topic is from 100%, and every flagged topic gets at least one.
  - Difficulty follows the student's recent average on each topic: below 50% gets foundation questions, 50–75% gets standard and above 75% gets stretch.
  - Sets are printable. "Shuffle" makes a new set.

## Running it

You need Python 3.10 or newer.

```
python -m venv .venv
.venv\Scripts\activate          (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python seed.py                  # optional: adds three made-up demo students
flask --app tutor_tracker run
```

Then open http://127.0.0.1:5000.

**Tests:** `python -m unittest discover tests -v`

## How it's built

| Path | What it is |
|---|---|
| `tutor_tracker/__init__.py` | The Flask app: routes for students, scores and practice sets. |
| `tutor_tracker/db.py` | SQLite schema and queries. Uses parameterised SQL, foreign keys and `CHECK` constraints on marks. |
| `tutor_tracker/analysis.py` | The logic: topic statistics, weak-area rules and practice-set allocation. It doesn't depend on Flask or the database, so it's easy to test. |
| `tutor_tracker/questions.json` | The question bank, organised by subject, topic and difficulty. |
| `tutor_tracker/templates/`, `static/` | Jinja templates and CSS. The practice set has a print stylesheet. |
| `seed.py` | Demo data. All the students and scores are made up. |
| `tests/` | Unit tests for the analysis and end-to-end tests through Flask's test client. |

The database is created at `instance/tracker.sqlite`, which is ignored by git. Real student data never goes into the repository.

## What's next

- [ ] Login for me, plus read-only parent links showing just their own child's progress
- [ ] Charts of each topic over time
- [ ] A bigger question bank, and letting me add questions through the app
- [ ] Marking practice sets in the app, so results go straight into the tracker
- [ ] Deployment, so I can use it on my phone during sessions

---

Built with help from Claude Code (AI-assisted development). I designed the features and the weak-area rules around how I actually tutor.
