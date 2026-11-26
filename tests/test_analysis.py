import unittest

from tutor_tracker import analysis


def scores(topic, *percents):
    return [{"topic": topic, "percent": p} for p in percents]


class TopicStats(unittest.TestCase):
    def test_low_recent_average_is_weak(self):
        stats = analysis.topic_stats(scores("Quadratics", 40, 50, 55))
        self.assertTrue(stats["Quadratics"]["weak"])
        self.assertIn("below", stats["Quadratics"]["reasons"][0])

    def test_sudden_drop_is_flagged_even_with_good_average(self):
        stats = analysis.topic_stats(scores("Trig", 85, 90, 65))
        self.assertTrue(stats["Trig"]["weak"])
        self.assertTrue(any("dropped" in r for r in stats["Trig"]["reasons"]))

    def test_strong_topic_is_not_weak(self):
        stats = analysis.topic_stats(scores("Fractions", 80, 85, 88))
        self.assertFalse(stats["Fractions"]["weak"])
        self.assertEqual(stats["Fractions"]["trend"], "steady")

    def test_only_recent_scores_count(self):
        # early struggles shouldn't keep a topic flagged once the student has improved
        stats = analysis.topic_stats(scores("Equations", 20, 30, 75, 80, 85))
        self.assertFalse(stats["Equations"]["weak"])
        self.assertEqual(stats["Equations"]["trend"], "improving")

    def test_sorted_weakest_first(self):
        stats = analysis.topic_stats(scores("A", 90) + scores("B", 40) + scores("C", 70))
        self.assertEqual(list(stats), ["B", "C", "A"])


class PracticeSets(unittest.TestCase):
    BANK = {
        topic: [{"q": f"{topic} {lvl} {i}", "difficulty": lvl}
                for lvl in ("foundation", "standard", "stretch") for i in range(4)]
        for topic in ("Weak", "Okay", "Strong")
    }

    def setUp(self):
        self.stats = analysis.topic_stats(
            scores("Weak", 35, 40) + scores("Okay", 65, 70) + scores("Strong", 90, 95))

    def test_size_is_respected(self):
        for size in (1, 5, 8, 12):
            self.assertEqual(len(analysis.practice_set(self.stats, self.BANK, size=size, seed=1)), size)

    def test_weak_topics_get_most_questions(self):
        qs = analysis.practice_set(self.stats, self.BANK, size=10, seed=1)
        counts = {t: sum(q["topic"] == t for q in qs) for t in self.BANK}
        self.assertGreater(counts["Weak"], counts["Okay"])
        self.assertGreaterEqual(counts["Okay"], counts["Strong"])

    def test_difficulty_matches_level(self):
        qs = analysis.practice_set(self.stats, self.BANK, size=10, seed=1)
        weak = [q["difficulty"] for q in qs if q["topic"] == "Weak"]
        # the 4 foundation questions come first, then the nearest level, never stretch
        self.assertEqual(weak[:4], ["foundation"] * 4)
        self.assertNotIn("stretch", weak)
        strong = [q["difficulty"] for q in qs if q["topic"] == "Strong"]
        self.assertTrue(all(d == "stretch" for d in strong))

    def test_never_more_questions_than_the_bank_has(self):
        small_bank = {"Weak": self.BANK["Weak"][:2], "Okay": self.BANK["Okay"][:2], "Strong": self.BANK["Strong"][:2]}
        qs = analysis.practice_set(self.stats, small_bank, size=10, seed=1)
        self.assertEqual(len(qs), 6)
        self.assertEqual(len({q["question"] for q in qs}), 6)

    def test_same_seed_same_set(self):
        a = analysis.practice_set(self.stats, self.BANK, size=8, seed=7)
        b = analysis.practice_set(self.stats, self.BANK, size=8, seed=7)
        self.assertEqual(a, b)

    def test_no_scores_no_questions(self):
        self.assertEqual(analysis.practice_set({}, self.BANK), [])


if __name__ == "__main__":
    unittest.main()
