import tempfile
import unittest
from pathlib import Path

from tutor_tracker import create_app


class AppFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.tmp.name) / "test.sqlite")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def add_student(self):
        r = self.client.post("/students", data={"name": "Test Student", "year_group": "Year 11",
                                                "subject": "GCSE Maths", "target": "70"})
        self.assertEqual(r.status_code, 302)
        return r.headers["Location"]

    def test_full_flow(self):
        url = self.add_student()
        for marks in (8, 9, 7):
            self.client.post(url + "/scores", data={"topic": "Algebra: quadratics", "marks": marks, "out_of": 20})
        self.client.post(url + "/scores", data={"topic": "Statistics and probability", "marks": 18, "out_of": 20})

        page = self.client.get(url).get_data(as_text=True)
        self.assertIn("Focus areas", page)
        self.assertIn("Algebra: quadratics", page)

        practice = self.client.get(url + "/practice?size=6&seed=1").get_data(as_text=True)
        self.assertEqual(practice.count("<li>"), 6)

        home = self.client.get("/").get_data(as_text=True)
        self.assertIn("Test Student", home)

    def test_rejects_bad_scores(self):
        url = self.add_student()
        r = self.client.post(url + "/scores", data={"topic": "Algebra: quadratics", "marks": 25, "out_of": 20},
                             follow_redirects=True)
        self.assertIn("Couldn&#39;t save", r.get_data(as_text=True))
        r = self.client.post(url + "/scores", data={"topic": "Made-up topic", "marks": 5, "out_of": 20},
                             follow_redirects=True)
        self.assertIn("unknown topic", r.get_data(as_text=True))

    def test_unknown_student_is_404(self):
        self.assertEqual(self.client.get("/students/999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
