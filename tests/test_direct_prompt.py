import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_spec_card_ab as pipeline
import run_direct


class DirectPromptTests(unittest.TestCase):
    def test_baseline_matches_existing_prompt(self):
        from argparse import Namespace
        self.assertEqual(pipeline.direct_prompt(Namespace(direct_prompt='baseline')), pipeline.DIRECT_SYSTEM)

    def test_entry_defaults_and_override(self):
        for extra, expected in [([], 'g3'), (['--direct-prompt', 'baseline'], 'baseline')]:
            captured = []
            with patch.object(sys, 'argv', ['run_direct.py', *extra]), patch.object(
                    pipeline, 'main', side_effect=lambda: captured.append(pipeline.parse_args())):
                run_direct.main()
                self.assertEqual(sys.argv, ['run_direct.py', *extra])
            self.assertEqual(captured[0].direct_prompt, expected)
            self.assertEqual(captured[0].arm, 'direct')
            self.assertEqual(captured[0].max_repairs, 0)

if __name__ == '__main__':
    unittest.main()
