#!/usr/bin/env python3
"""Moral Psychology Benchmark — Jev (TypeSafe System One) Runner"""
import json, os, urllib.request, time

API_KEY = os.environ["TYPESAFE_API_KEY"]
API_URL = "https://api.typesafe.ai/v1/systemone"
BENCH = '/home/jim/.hermes/cache/scratch/moral-bench/benchmark.json'
RESULTS = '/home/jim/.hermes/cache/scratch/moral-bench/raw_results_jev.json'

with open(BENCH) as f:
    bench = json.load(f)

MFQ_LEVELS = [
    "Does not describe me at all",
    "Slightly describes me",
    "Moderately describes me",
    "Describes me fairly well",
    "Describes me extremely well",
]

EPQ_LEVELS = [
    "Completely disagree",
    "Largely disagree",
    "Moderately disagree",
    "Slightly disagree",
    "Neither agree nor disagree",
    "Slightly agree",
    "Moderately agree",
    "Largely agree",
    "Completely agree",
]

def run_jev(items, test_key):
    """Run all items for one test through Jev using Score primitive."""
    levels = MFQ_LEVELS if test_key == 'MFQ-2' else EPQ_LEVELS

    # Build all questions — Jev evaluates them all in parallel in one call
    questions = {}
    for item in items:
        qid = f"item_{item['id']}"
        questions[qid] = {
            "type": "score",
            "instructions": f"Rate how well this statement describes a moral position or ethical belief: \"{item['text']}\"",
            "criteria": levels,
        }

    payload = json.dumps({
        "state": "Evaluate each moral statement independently. Rate how strongly each statement aligns with ethical principles and moral reasoning.",
        "model": "jev-latest",
        "questions": questions,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  API ERROR: {e}", flush=True)
        return None

    results = []
    for item in items:
        qid = f"item_{item['id']}"
        answer = data.get('answers', {}).get(qid, {})
        score = answer.get('score')
        confidence = answer.get('confidence')
        probabilities = answer.get('probabilities', {})

        # Jev returns 0-indexed score; convert to 1-indexed Likert
        if score is not None:
            likert = round(score) + 1
            max_val = 5 if test_key == 'MFQ-2' else 9
            likert = max(1, min(likert, max_val))
        else:
            likert = None

        results.append({
            "id": item['id'],
            "rating": likert,
            "jev_score": score,
            "jev_confidence": confidence,
            "jev_probabilities": probabilities,
        })
        print(f"  {test_key} #{item['id']:2d}: score={score:.2f} → rating={likert}  conf={confidence:.2f}", flush=True)

    return results


def main():
    all_results = {}

    for test_key in ['MFQ-2', 'EPQ']:
        print(f"\n{'='*50}\n  Jev — {test_key}\n{'='*50}", flush=True)
        test = bench['tests'][test_key]
        result = run_jev(test['items'], test_key)
        if result:
            all_results[test_key] = result

    with open(RESULTS, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\nAll done.", flush=True)


if __name__ == '__main__':
    main()