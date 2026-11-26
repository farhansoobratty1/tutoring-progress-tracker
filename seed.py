"""Fill the database with made-up demo students and scores (no real student data)."""
from datetime import date, timedelta

from tutor_tracker import create_app, db

DEMO = [
    ("Alex (demo)", "Year 11", "GCSE Maths", 70, {
        "Algebra: solving equations": [55, 62, 71, 78],
        "Algebra: quadratics": [48, 52, 45],
        "Geometry: Pythagoras and trigonometry": [70, 74, 58],
        "Number: fractions and percentages": [80, 85, 88],
        "Statistics and probability": [66, 72],
    }),
    ("Priya (demo)", "Year 11", "GCSE Physics", 75, {
        "Forces and motion": [62, 70, 81],
        "Energy": [75, 79],
        "Electricity": [41, 50, 55],
        "Waves": [68],
    }),
    ("Sam (demo)", "Year 4", "11+ Maths", 80, {
        "Arithmetic": [70, 80, 90],
        "Fractions": [40, 55, 50],
        "Shape and area": [85, 80],
        "Word problems": [60, 58, 52],
    }),
]


def seed():
    app = create_app()
    with app.app_context():
        conn = db.get_db()
        conn.execute("DELETE FROM scores")
        conn.execute("DELETE FROM students")
        conn.commit()
        start = date.today() - timedelta(weeks=10)
        for name, year, subject, target, topics in DEMO:
            sid = db.add_student(name, year, subject, target)
            for t_i, (topic, percents) in enumerate(topics.items()):
                for i, p in enumerate(percents):
                    taken = start + timedelta(weeks=2 * i, days=t_i)
                    db.add_score(sid, topic, p / 5, 20, taken.isoformat())
        print(f"Seeded {len(DEMO)} demo students into {app.config['DATABASE']}")


if __name__ == "__main__":
    seed()
