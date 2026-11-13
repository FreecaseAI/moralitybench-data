"""Offline verification tests for the 2026-11-12 rerun release and combined summary."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class November12RerunTests(unittest.TestCase):
    def test_five_run_and_combined_integrity(self):
        summary = json.loads((ROOT / 'five-run-summary.json').read_text())
        combined = json.loads((ROOT / 'combined-five-run-summary.json').read_text())
        verification = json.loads((ROOT / 'verification.json').read_text())
        manifest = json.loads((ROOT / 'manifest.json').read_text())

        self.assertTrue(verification['verified'])
        self.assertEqual(verification['records'], 560)
        self.assertEqual(verification['recovery_records'], 12)
        self.assertEqual(verification['distinct_response_ids'], 572)
        self.assertEqual(verification['superseded_models'], ['Mistral Large 2512'])

        self.assertEqual(len(summary['models']), 2)
        by_name = {m['name']: m for m in summary['models']}
        muse = by_name['Muse Spark 1.3']
        mistral = by_name['Mistral Large 2512']

        self.assertEqual(muse['numeric'], 280)
        self.assertEqual(muse['missing'], 0)
        self.assertEqual((muse['matched_pairs'], muse['compared_pairs']), (433, 560))
        self.assertAlmostEqual(muse['distance'], 0.49955555555555564, places=12)
        self.assertEqual((muse['idealism'], muse['relativism'], muse['ideology']), (5.58, 4.68, 'Absolutist'))
        self.assertTrue(muse['category_changed'])

        self.assertEqual(mistral['numeric'], 280)
        self.assertEqual(mistral['missing'], 0)
        self.assertEqual((mistral['matched_pairs'], mistral['compared_pairs']), (526, 560))
        self.assertAlmostEqual(mistral['distance'], 0.6366666666666667, places=12)
        self.assertEqual((mistral['idealism'], mistral['relativism'], mistral['ideology']), (7.16, 5.7, 'Situationist'))
        self.assertFalse(mistral['category_changed'])

        self.assertEqual(len(combined['models']), 21)
        self.assertEqual(combined['llm_numeric'], 5726)
        self.assertEqual(combined['llm_scheduled'], 5880)
        self.assertEqual(combined['collection_dates'], ['2026-10-04', '2026-10-14', '2026-10-29', '2026-11-12'])
        self.assertEqual(len(combined['extensions']), 3)
        self.assertEqual([m['rank'] for m in combined['models']], list(range(1, 22)))
        self.assertEqual([m['distance'] for m in combined['models']], sorted(m['distance'] for m in combined['models']))

        c_by_name = {m['name']: m for m in combined['models']}
        self.assertEqual(c_by_name['Llama 4 Maverick']['matched_pairs'], 526)
        self.assertEqual(c_by_name['Mistral Large 2512']['matched_pairs'], 526)
        self.assertEqual(c_by_name['Muse Spark 1.3']['rank'], 16)
        self.assertEqual(c_by_name['Mistral Large 2512']['rank'], 21)

        with (ROOT / 'combined-five-run-summary.csv').open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 22)
        self.assertEqual(rows[-1]['name'], 'Jev (TypeSafe)')
        self.assertEqual(rows[-1]['rank'], '')

        rec = json.loads((ROOT / 'oct4-recovery' / 'summary.json').read_text())
        self.assertEqual(rec['numeric'], 261)
        self.assertAlmostEqual(rec['distance'], 0.6383333333333335, places=12)

        for rel, digest in manifest.items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), digest, rel)


if __name__ == '__main__':
    unittest.main()
