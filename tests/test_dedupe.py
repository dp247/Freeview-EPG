import unittest

from src.dedupe import dedupe_programmes


class TestDedupeProgrammes(unittest.TestCase):
    def test_dedupe_preserves_last_occurrence(self):
        programmes = [
            {"channel": "a", "start": 1, "title": "Show", "description": "first"},
            {"channel": "b", "start": 2, "title": "Other", "description": "keep"},
            {"channel": "a", "start": 1, "title": "Show", "description": "last"},
        ]

        deduped = dedupe_programmes(programmes)

        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["description"], "keep")
        self.assertEqual(deduped[1]["description"], "last")
        self.assertEqual(
            [item["channel"] for item in deduped],
            ["b", "a"],
        )


if __name__ == "__main__":
    unittest.main()
