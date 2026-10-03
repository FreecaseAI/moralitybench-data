#!/usr/bin/env python3
"""Moral Psychology LLM Benchmark Runner — Batch 2 (8 models)"""
import json, subprocess, time, urllib.request, urllib.error, sys

result = subprocess.run(['bash', '-c', 'source ~/.hermes/.env && echo $OPENROUTER_API_KEY'],
                        capture_output=True, text=True)
API_KEY = result.stdout.strip()

BENCH = '/home/jim/.hermes/cache/scratch/moral-bench/benchmark.json'
RESULTS = '/home/jim/.hermes/cache/scratch/moral-bench/raw_results_batch2.json'

with open(BENCH) as f:
    bench = json.load(f)

MODELS = {
    "GPT-6.1 Sol": "openai/gpt-6.1-sol",
    "GLM 5.3": "z-ai/glm-5.3",
    "Grok 4.7": "x-ai/grok-4.7",
    "DeepSeek V4.1 Flash": "deepseek/deepseek-v4.1-flash",
    "Kimi K3": "moonshotai/kimi-k3",
    "Muse Spark 1.3": "meta/muse-spark-1.3",
    "MiniMax M3": "minimax/minimax-m3",
    "Gemini 3.8 Flash": "google/gemini-3.8-flash",
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
                print(f"    FAILED: {e}", flush=True)
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
            with open(RESULTS, 'w') as f:
                json.dump(all_results, f, indent=2)

    print(f"\n\nAll done.", flush=True)


if __name__ == '__main__':
    main()