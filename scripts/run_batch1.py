#!/usr/bin/env python3
"""Moral Psychology LLM Benchmark Runner — OpenRouter"""
import json, subprocess, time, urllib.request, urllib.error, sys

result = subprocess.run(['bash', '-c', 'source ~/.hermes/.env && echo $OPENROUTER_API_KEY'],
                        capture_output=True, text=True)
API_KEY = result.stdout.strip()

BENCH = '/home/jim/.hermes/cache/scratch/moral-bench/benchmark.json'
RESULTS = '/home/jim/.hermes/cache/scratch/moral-bench/raw_results.json'
LOG = '/home/jim/.hermes/cache/scratch/moral-bench/benchmark_log.txt'

with open(BENCH) as f:
    bench = json.load(f)

MODELS = {
    "Qwen3.8 27B": "qwen/qwen3.8-27b",
    "MiMo v2.6 Pro": "xiaomi/mimo-v2.6-pro",
    "Claude Opus 5.5": "anthropic/claude-opus-5.5",
}

PROMPT_TEMPLATE = bench['benchmark_protocol']['prompt_template']
MFQ_SCALE = "1 = Does not describe me at all, 2 = Slightly describes me, 3 = Moderately describes me, 4 = Describes me fairly well, 5 = Describes me extremely well"
EPQ_SCALE = "1 = Completely disagree, 2 = Largely disagree, 3 = Moderately disagree, 4 = Slightly disagree, 5 = Neither agree nor disagree, 6 = Slightly agree, 7 = Moderately agree, 8 = Largely agree, 9 = Completely agree"


def get_rating(model_id, prompt, retries=3):
    payload = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 4096,
        "reasoning": {"exclude": True},
    }).encode()

    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=payload,
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    )

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            content = (data['choices'][0]['message'].get('content') or '').strip()
            for char in content:
                if char.isdigit():
                    return int(char)
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                return None


def run_test(model_id, test_key):
    test = bench['tests'][test_key]
    items = test['items']
    scale = MFQ_SCALE if test_key == 'MFQ-2' else EPQ_SCALE

    results = []
    for item in items:
        prompt = PROMPT_TEMPLATE.format(scale_description=scale, item_text=item['text'])
        rating = get_rating(model_id, prompt)
        results.append({"id": item['id'], "rating": rating})
        print(f"  {test_key} #{item['id']:2d}: {rating}", flush=True)
        time.sleep(0.3)
    return results


def main():
    all_results = {}

    for model_name, model_id in MODELS.items():
        print(f"\n{'='*50}\n  {model_name}  ({model_id})\n{'='*50}", flush=True)
        all_results[model_name] = {}

        for test_key in ['MFQ-2', 'EPQ']:
            print(f"\n--- {test_key} ---", flush=True)
            all_results[model_name][test_key] = run_test(model_id, test_key)
            # Save partial results after each test
            with open(RESULTS, 'w') as f:
                json.dump(all_results, f, indent=2)

    print(f"\n\nAll done.", flush=True)


if __name__ == '__main__':
    main()