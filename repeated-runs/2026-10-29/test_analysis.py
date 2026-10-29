"""Scientific invariants for the October 29 MFQ-2/EPQ extension; no API calls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('october29_analysis', ROOT / 'analyze_five_runs.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class ExtensionAnalysisTests(unittest.TestCase):
    def test_primary_parser_rejects_prose_decimals_and_out_of_range(self):
        self.assertEqual(analysis.collector.parse('3', 5), (3, 3))
        for response in ['I choose 3', '3.0', '6']:
            self.assertIsNone(analysis.collector.parse(response, 5)[1])

    def test_runs_have_equal_weight_before_absolute_distance_is_averaged(self):
        runs = {
            run: {**{('MFQ-2', item): value for item in range(1, 37)},
                  **{('EPQ', item): 5 for item in range(1, 21)}}
            for run, value in enumerate([1, 5, 1, 5, 3], 1)
        }
        for item in range(7, 37):
            runs[1][('MFQ-2', item)] = None
        result = analysis.summarize_runs('GPT-6.1 Terra', runs)
        self.assertEqual(result['numeric'], 250)
        self.assertEqual(result['foundations'], [3] * 6)
        expected = (2 * (12.64 / 6) + 2 * (11.36 / 6) + 2.74 / 6) / 5
        self.assertAlmostEqual(result['distance'], expected)

    def test_missing_answer_is_omitted_from_all_four_affected_pairs(self):
        runs = {
            run: {**{('MFQ-2', item): 3 for item in range(1, 37)},
                  **{('EPQ', item): 5 for item in range(1, 21)}}
            for run in range(1, 6)
        }
        runs[1][('MFQ-2', 1)] = None
        result = analysis.summarize_runs('GPT-6.1 Terra', runs)
        self.assertEqual(result['numeric'], 279)
        self.assertEqual(result['missing'], 1)
        self.assertEqual(result['matched_pairs'], 556)
        self.assertEqual(result['compared_pairs'], 556)
        self.assertEqual(result['all_five_observed_items'], 55)
        self.assertEqual(result['all_five_identical_items'], 55)
        self.assertEqual(result['foundations'], [3] * 6)
        self.assertAlmostEqual(result['distance'], 2.74 / 6)
        self.assertEqual(result['ideology'], 'Situationist')

    def test_missing_foundation_is_unscored(self):
        runs = {
            run: {**{('MFQ-2', item): 3 for item in range(1, 37)},
                  **{('EPQ', item): 5 for item in range(1, 21)}}
            for run in range(1, 6)
        }
        for item in [1, 7, 13, 19, 25, 31]:
            runs[1][('MFQ-2', item)] = None
        self.assertIsNone(analysis.summarize_runs('GPT-6.1 Terra', runs))

    def test_combination_preserves_every_historical_value_and_jev(self):
        previous = json.loads((ROOT.parent / '2026-10-14/combined-five-run-summary.json').read_text())
        before = copy.deepcopy(previous)
        addition = copy.deepcopy(previous['models'][0])
        addition.update(name='GPT-6.1 Terra', numeric=280, missing=0,
                        collection_date='2026-10-29', release_path='repeated-runs/2026-10-29')
        release = {'models': [addition], 'legacy_models': [addition],
                   'details': {'GPT-6.1 Terra': {'strict_numeric': 280}},
                   'unscored_models': [], 'scheduled': 280,
                   'primary_parser': 'strict whole-answer integer'}
        combined = analysis.combine(previous, release)
        self.assertEqual(previous, before)
        self.assertEqual(combined['jev'], before['jev'])
        actual = {m['name']: {k: v for k, v in m.items() if k != 'rank'} for m in combined['models']}
        for old in before['models']:
            self.assertEqual(actual[old['name']], {k: v for k, v in old.items() if k != 'rank'})
        self.assertEqual(len(combined['models']), 17)
        self.assertEqual(combined['llm_numeric'], 4295 + 280)
        self.assertEqual(combined['llm_scheduled'], 4480 + 280)
        self.assertEqual(combined['extensions'][0], before['latest_extension'])
        self.assertEqual(combined['latest_extension']['collection_date'], '2026-10-29')
        self.assertEqual(combined['collection_dates'], ['2026-10-04', '2026-10-14', '2026-10-29'])
        self.assertIn('Jev uses Python round(score) + 1, clipped to instrument range.',
                      combined['primary_parser'])


if __name__ == '__main__':
    unittest.main()
