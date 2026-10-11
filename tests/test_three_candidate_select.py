import unittest
from types import SimpleNamespace

from run_three_candidate_select import aggregate, blinded_order


def candidate(candidate_id: int, passed: bool) -> dict:
    return {
        "candidate_id": candidate_id,
        "strategy": "test",
        "first_syntax_pass": True,
        "final_syntax_pass": True,
        "attempts": 1,
        "api_calls": 1,
        "total_tokens": 10,
        "official": {"pass": passed},
    }


class ThreeCandidateMetricsTest(unittest.TestCase):
    def test_pass1_pass3_and_select3_are_distinct(self) -> None:
        rows = [
            {
                "case_id": "Prob001_x",
                "candidates": [candidate(1, False), candidate(2, True), candidate(3, False)],
                "selection": {"selected_id": 2, "api_calls": 1, "total_tokens": 5},
                "selected_official": {"pass": True},
            },
            {
                "case_id": "Prob002_x",
                "candidates": [candidate(1, True), candidate(2, False), candidate(3, False)],
                "selection": {"selected_id": 3, "api_calls": 1, "total_tokens": 5},
                "selected_official": {"pass": False},
            },
        ]
        args = SimpleNamespace(model="m", reasoning_effort="none", temperature=0.0)
        summary = aggregate(rows, args, ["Prob001_x", "Prob002_x"])
        self.assertEqual(summary["metrics"]["pass_at_1_count"], 1)
        self.assertEqual(summary["metrics"]["oracle_pass_at_3_count"], 2)
        self.assertEqual(summary["metrics"]["blind_select_at_3_count"], 1)

    def test_blinded_order_is_stable_and_complete(self) -> None:
        candidates = [candidate(1, False), candidate(2, False), candidate(3, False)]
        first = blinded_order("Prob001_x", candidates)
        second = blinded_order("Prob001_x", candidates)
        self.assertEqual([x["candidate_id"] for x in first], [x["candidate_id"] for x in second])
        self.assertEqual({x["candidate_id"] for x in first}, {1, 2, 3})


if __name__ == "__main__":
    unittest.main()
