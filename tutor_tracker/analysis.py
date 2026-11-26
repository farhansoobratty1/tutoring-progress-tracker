"""Turning raw scores into something useful: per-topic stats, weak areas and practice sets.

Kept free of Flask and SQLite so it can be tested on plain lists of dicts.
"""
import random
from collections import defaultdict

WEAK_AVERAGE = 60      # recent average below this (percent) -> weak
DROP_POINTS = 15       # latest score this far below the earlier average -> slipping
RECENT = 3             # how many of the latest scores count as "recent"


def topic_stats(scores):
    """Group scores by topic. Returns {topic: {...}} sorted weakest first."""
    by_topic = defaultdict(list)
    for s in scores:                       # scores arrive oldest first
        by_topic[s["topic"]].append(s["percent"])

    stats = {}
    for topic, results in by_topic.items():
        recent = results[-RECENT:]
        earlier = results[:-1]
        stats[topic] = {
            "attempts": len(results),
            "latest": results[-1],
            "recent_average": round(sum(recent) / len(recent), 1),
            "trend": _trend(results),
            "history": results,
            "reasons": _weak_reasons(results, recent, earlier),
        }
        stats[topic]["weak"] = bool(stats[topic]["reasons"])
    return dict(sorted(stats.items(), key=lambda kv: kv[1]["recent_average"]))


def _trend(results):
    if len(results) < 2:
        return "new"
    change = results[-1] - results[0]
    if change >= 10:
        return "improving"
    if change <= -10:
        return "declining"
    return "steady"


def _weak_reasons(results, recent, earlier):
    reasons = []
    avg = sum(recent) / len(recent)
    if avg < WEAK_AVERAGE:
        reasons.append(f"recent average {avg:.0f}% is below {WEAK_AVERAGE}%")
    if earlier and results[-1] <= sum(earlier) / len(earlier) - DROP_POINTS:
        reasons.append(f"latest score dropped {sum(earlier) / len(earlier) - results[-1]:.0f} points")
    return reasons


def weak_areas(stats):
    return [topic for topic, s in stats.items() if s["weak"]]


def difficulty_for(average):
    """Pick question difficulty from how the student is doing on that topic."""
    if average < 50:
        return "foundation"
    if average < 75:
        return "standard"
    return "stretch"


def practice_set(stats, question_bank, size=8, seed=None):
    """Build a practice set that leans towards the student's weak topics.

    Each topic gets a share of the questions proportional to how far it is from 100%,
    every weak topic gets at least one question, and questions are pitched at a
    difficulty that matches the student's recent average on that topic.
    question_bank: {topic: [{"q": str, "difficulty": str}, ...]}
    """
    rng = random.Random(seed)
    topics = [t for t in stats if t in question_bank]
    if not topics:
        return []

    alloc = _allocate(stats, question_bank, topics, size)

    chosen = []
    for topic in topics:
        n = alloc[topic]
        if n == 0:
            continue
        level = LEVELS.index(difficulty_for(stats[topic]["recent_average"]))
        pool = list(question_bank[topic])
        rng.shuffle(pool)
        # the student's own level first, then the nearest levels (easier before harder)
        pool.sort(key=lambda q: (abs(LEVELS.index(q["difficulty"]) - level), LEVELS.index(q["difficulty"])))
        for q in pool[:n]:
            chosen.append({"topic": topic, "difficulty": q["difficulty"], "question": q["q"]})
    return chosen


LEVELS = ["foundation", "standard", "stretch"]


def _allocate(stats, question_bank, topics, size):
    """Share `size` questions between topics in proportion to how far each is from 100%,
    without giving a topic more questions than its bank holds."""
    gaps = {t: max(100 - stats[t]["recent_average"], 5) for t in topics}
    room = {t: len(question_bank[t]) for t in topics}
    size = min(size, sum(room.values()))
    alloc = {t: 0 for t in topics}
    for t in topics:                       # every weak topic gets at least one question
        if stats[t]["weak"] and sum(alloc.values()) < size:
            alloc[t] = 1
    while sum(alloc.values()) < size:
        # give the next question to the topic furthest below its fair share
        open_topics = [t for t in topics if alloc[t] < room[t]]
        total = sum(gaps[t] for t in open_topics)
        t = max(open_topics, key=lambda t: gaps[t] / total * size - alloc[t])
        alloc[t] += 1
    return alloc
