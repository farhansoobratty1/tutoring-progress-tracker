"""Tutoring progress tracker: records topic scores, flags weak areas and builds practice sets."""
import json
import os
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from . import analysis, db

HERE = Path(__file__).resolve().parent


def load_question_bank(path=HERE / "questions.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("TRACKER_SECRET_KEY", "dev-only-change-me"),
        DATABASE=str(Path(app.instance_path) / "tracker.sqlite"),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    bank = load_question_bank()
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()

    @app.route("/")
    def index():
        students = []
        for s in db.list_students():
            stats = analysis.topic_stats(db.scores_for(s["id"]))
            students.append({"row": s, "weak": analysis.weak_areas(stats), "topics": len(stats)})
        return render_template("index.html", students=students, subjects=sorted(bank))

    @app.post("/students")
    def create_student():
        name = request.form.get("name", "").strip()
        subject = request.form.get("subject", "")
        if not name or subject not in bank:
            flash("Please give a name and pick a subject.")
            return redirect(url_for("index"))
        sid = db.add_student(name, request.form.get("year_group", ""), subject,
                             request.form.get("target", 70) or 70)
        return redirect(url_for("student", student_id=sid))

    @app.route("/students/<int:student_id>")
    def student(student_id):
        s = db.get_student(student_id) or abort(404)
        scores = db.scores_for(student_id)
        stats = analysis.topic_stats(scores)
        return render_template(
            "student.html", s=s, stats=stats, weak=analysis.weak_areas(stats),
            recent=list(reversed(scores))[:10], topics=sorted(bank.get(s["subject"], {})),
        )

    @app.post("/students/<int:student_id>/scores")
    def record_score(student_id):
        s = db.get_student(student_id) or abort(404)
        try:
            marks = float(request.form["marks"])
            out_of = float(request.form["out_of"])
            topic = request.form["topic"]
            if topic not in bank.get(s["subject"], {}):
                raise ValueError("unknown topic")
            db.add_score(student_id, topic, marks, out_of,
                         request.form.get("taken_on") or None, request.form.get("note", ""))
            flash(f"Saved {marks:g}/{out_of:g} for {topic}.")
        except (KeyError, ValueError) as e:
            flash(f"Couldn't save that score: {e}")
        return redirect(url_for("student", student_id=student_id))

    @app.route("/students/<int:student_id>/practice")
    def practice(student_id):
        s = db.get_student(student_id) or abort(404)
        stats = analysis.topic_stats(db.scores_for(student_id))
        size = max(1, min(int(request.args.get("size", 8)), 20))
        questions = analysis.practice_set(stats, bank.get(s["subject"], {}), size=size,
                                          seed=request.args.get("seed"))
        return render_template("practice.html", s=s, questions=questions,
                               weak=analysis.weak_areas(stats), size=size)

    return app
