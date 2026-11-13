#!/usr/bin/env python3
"""Join the Center's returned DIT-2 scores to the public run table.

Inputs (checked in):  center-report/center-scores.xlsx, runs.csv
Outputs:              scores-by-run.csv, scores-by-model.csv, summary.json

    python3 build_summary.py           # rewrite the outputs
    python3 build_summary.py --check   # fail if the outputs or source files differ

The Center for the Study of Ethical Development computed every score. This
script only reads its workbook, attaches model names, and averages the two runs.
Standard library only.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import statistics
import sys
import zipfile
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
WORKBOOK = HERE / 'center-report/center-scores.xlsx'
REPORT = HERE / 'center-report/center-scorer-report.pdf'
RUNS = HERE / 'runs.csv'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

# SHA-256 of the files exactly as the Center returned them; only the names were shortened.
SOURCES = {
    WORKBOOK: 'a0fcfa326ee4e1124437c451f4fa69188f1bc587c39acb91ccd793d2c44642e7',
    REPORT: '7715b5bfdf8d811a26fd0a44dcb7bd7eeb2061d9e351dc0c1167649193c57e82',
}

# Center column -> public column. Order is the public column order.
SCORES = [
    ('N2SCORE', 'n2'),
    ('PSCORE', 'p'),
    ('MAINTAININGNORMS', 'maintaining_norms'),
    ('PERSONALINTEREST', 'personal_interest'),
    ('TYPENEW', 'type'),
    ('CONSTRAN', 'consolidation'),
    ('U', 'utilizer'),
    ('HumLib', 'humanitarian_liberalism'),
    ('Cancer10', 'religious_orthodoxy'),
    ('NumCD', 'cant_decide'),
    ('ASCORE', 'antisocial'),
    ('MSCORE', 'meaningless'),
    ('Purged', 'purged'),
]
U_MISSING = 9.99  # the Center's missing-value code for the Utilizer score
DEMOGRAPHICS = ['age', 'sex', 'edu', 'conlib', 'citizen', 'lang']
STAT_COLUMNS = ['n2', 'p', 'maintaining_norms', 'personal_interest', 'humanitarian_liberalism',
                'religious_orthodoxy', 'cant_decide', 'antisocial', 'meaningless']

# "Stats" page of the Center's PDF report: (mean, standard deviation), N = 32.
CENTER_STATS = {
    'n2': (73.08, 5.77), 'p': (76.12, 9.14), 'maintaining_norms': (17.88, 9.5),
    'personal_interest': (5.5, 2.96), 'humanitarian_liberalism': (3.25, 0.95),
    'religious_orthodoxy': (2.28, 1.14), 'cant_decide': (0.81, 1.06),
    'antisocial': (0.25, 0.8), 'meaningless': (0.0, 0.0),
}
CENTER_U_WITH_MISSING_CODE = (0.38, 1.75)

# Gungordu, Nabizadehchianeh, O'Connor, Ma & Walker (2024), Ethics & Behavior 34(4),
# 246-263, Tables 3 and 4: US citizens with English as a primary language, tested
# 2011-2020 (N = 73,740). Each row: education level, n for the schema scores,
# (mean, SD) for Personal Interest, Maintaining Norms and P score, n for N2, (mean, SD) for N2.
NORMS_2023_ROWS = [
    ('Grade 1-6', 781, (24.6, 11.8), (34.5, 13.9), (35.6, 15.7), 781, (35.45, 14.74)),
    ('Grade 7-9', 1614, (27.3, 13.4), (33.3, 14.4), (32.5, 16.7), 1613, (31.50, 16.64)),
    ('Grade 10-12', 5317, (27.5, 13.0), (33.5, 13.9), (32.8, 16.4), 5314, (31.82, 16.27)),
    ('Voc/Tech', 903, (27.1, 13.0), (36.8, 13.8), (29.2, 14.8), 903, (28.05, 14.90)),
    ('Junior college', 2776, (28.5, 12.7), (34.6, 13.6), (30.4, 15.5), 2774, (29.08, 15.49)),
    ('College freshman', 18985, (28.1, 12.7), (34.8, 13.5), (31.1, 15.3), 18976, (30.26, 15.19)),
    ('College sophomore', 7116, (26.1, 12.8), (33.7, 13.9), (34.4, 15.7), 7111, (33.67, 15.40)),
    ('College junior', 8751, (25.8, 12.8), (33.9, 14.0), (34.6, 15.8), 8750, (34.03, 15.57)),
    ('College senior', 14894, (24.1, 12.5), (33.3, 14.2), (37.2, 16.0), 14887, (36.96, 15.68)),
    ('Professional degree', 6490, (21.2, 11.6), (31.9, 14.6), (42.3, 16.0), 6486, (42.41, 14.82)),
    ('MS degree', 2441, (22.7, 12.3), (33.8, 14.9), (38.5, 15.6), 2440, (38.38, 15.17)),
    ('Doctoral degree', 3672, (23.4, 11.9), (32.3, 14.2), (38.9, 16.0), 3672, (38.47, 15.10)),
]


def pooled(pairs):
    """Combine (n, mean, sd) groups into one overall mean and SD."""
    total = sum(n for n, _, _ in pairs)
    mean = sum(n * m for n, m, _ in pairs) / total
    variance = sum((n - 1) * sd * sd + n * (m - mean) ** 2 for n, m, sd in pairs) / (total - 1)
    return total, round(mean, 2), round(variance ** 0.5, 2)


def human_norms():
    fields = ['personal_interest', 'maintaining_norms', 'p']
    groups = []
    for name, n, pi, mn, p, n2_n, n2 in NORMS_2023_ROWS:
        groups.append({'group': name, 'n': n, 'n_n2': n2_n, 'personal_interest': list(pi),
                       'maintaining_norms': list(mn), 'p': list(p), 'n2': list(n2)})
    overall = {'group': 'All education levels (pooled by MoralityBench from the rows above)'}
    for index, field in enumerate(fields):
        total, mean, sd = pooled([(row[1], row[2 + index][0], row[2 + index][1]) for row in NORMS_2023_ROWS])
        overall[field] = [mean, sd]
        overall['n'] = total
    total, mean, sd = pooled([(row[5], row[6][0], row[6][1]) for row in NORMS_2023_ROWS])
    overall['n2'] = [mean, sd]
    overall['n_n2'] = total
    return {
        'source': "Gungordu, N., Nabizadehchianeh, G., O'Connor, E., Ma, W., & Walker, D. I. (2024). "
                  'Moral reasoning development: norms for Defining Issue Test-2 (DIT2). '
                  'Ethics & Behavior, 34(4), 246-263. https://doi.org/10.1080/10508422.2023.2206573',
        'sample': 'US citizens with English as a primary language, tested 2011-2020 (N = 73,740); '
                  'published by the Center for the Study of Ethical Development as its updated DIT2 norms',
        'n2_75th_percentile_highest_group': 53.4,
        'groups': groups,
        'pooled': overall,
        'earlier_norms_2003': EARLIER_NORMS,
    }


# Bebeau & Thoma (2003), Guide for DIT-2, Table 1, kept for comparison with the 2023 norms:
# US respondents with English as a primary language, by education. (mean, standard deviation).
EARLIER_NORMS = {
    'source': 'Bebeau, M. J., & Thoma, S. J. (2003). Guide for DIT-2, Table 1.',
    'groups': [
        {'group': 'All education levels', 'n': 10553, 'personal_interest': [25.48, 12.71],
         'maintaining_norms': [32.73, 14.00], 'p': [36.74, 16.05], 'n2': [35.67, 16.23]},
        {'group': 'College seniors', 'n': 2441, 'personal_interest': [24.80, 12.53],
         'maintaining_norms': [32.40, 14.01], 'p': [37.84, 15.44], 'n2': [36.85, 15.53]},
        {'group': 'MS degree', 'n': 853, 'personal_interest': [21.69, 11.82],
         'maintaining_norms': [32.64, 14.35], 'p': [41.06, 15.77], 'n2': [40.56, 15.06]},
        {'group': 'Professional degree', 'n': 1582, 'personal_interest': [19.76, 11.28],
         'maintaining_norms': [31.41, 15.06], 'p': [44.87, 15.86], 'n2': [44.97, 14.87]},
        {'group': 'Ph.D./Ed.D.', 'n': 169, 'personal_interest': [18.71, 11.63],
         'maintaining_norms': [27.24, 14.05], 'p': [50.69, 16.16], 'n2': [48.99, 15.60]},
    ],
}


def number(text):
    value = round(float(text), 2)
    return int(value) if value == int(value) else value


def read_workbook():
    archive = zipfile.ZipFile(WORKBOOK)
    sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    table = []
    for row in sheet.iter(NS + 'row'):
        cells = {}
        for cell in row.findall(NS + 'c'):
            column = re.sub(r'\d+', '', cell.get('r'))
            value = cell.find(NS + 'v')
            if value is not None:
                cells[column] = value.text
            else:
                cells[column] = ''.join(t.text or '' for t in cell.iter(NS + 't'))
        table.append(cells)
    header = table[0]
    expected = ['id'] + [name for name, _ in SCORES]
    assert sorted(header.values()) == sorted(expected), list(header.values())
    scores = {}
    for cells in table[1:]:
        row = {header[column]: text for column, text in cells.items()}
        scores[int(float(row['id']))] = {public: number(row[center]) for center, public in SCORES}
    return scores


def stats(values):
    return {'n': len(values), 'mean': round(statistics.mean(values), 2),
            'sd': round(statistics.stdev(values), 2), 'min': min(values), 'max': max(values)}


def to_csv(fields, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def build():
    for path, digest in SOURCES.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == digest, f'{path.name} differs from the file the Center returned'
    scores = read_workbook()
    runs = list(csv.DictReader(RUNS.open()))
    submitted = {int(r['id']) for r in runs if r['submitted_for_scoring'] == 'yes'}
    assert submitted == set(scores), 'scored ids must equal submitted ids'

    by_run = []
    for run in runs:
        key = int(run['id'])
        if key not in scores:
            continue
        row = {'id': key, 'model': run['model'], 'run': int(run['run']), 'method': run['method']}
        row.update(scores[key])
        if row['utilizer'] == U_MISSING:
            row['utilizer'] = ''
        row.update({name: run[name] for name in DEMOGRAPHICS})
        by_run.append(row)

    by_model = []
    for model in dict.fromkeys(r['model'] for r in by_run):
        pair = [r for r in by_run if r['model'] == model]
        assert [r['run'] for r in pair] == [1, 2], model
        row = {'model': model, 'method': pair[0]['method'], 'runs_scored': len(pair)}
        for name in ['n2', 'p', 'maintaining_norms', 'personal_interest']:
            row[f'{name}_run1'], row[f'{name}_run2'] = pair[0][name], pair[1][name]
            row[f'{name}_mean'] = round(statistics.mean(r[name] for r in pair), 2)
        row['type'] = '; '.join(dict.fromkeys(str(r['type']) for r in pair))
        row['identical_scores_in_both_runs'] = 'yes' if all(
            pair[0][public] == pair[1][public] for _, public in SCORES) else 'no'
        by_model.append(row)
    by_model.sort(key=lambda r: -r['n2_mean'])

    cohort = {name: stats([r[name] for r in by_run]) for name in STAT_COLUMNS}
    for name, (mean, sd) in CENTER_STATS.items():
        assert (cohort[name]['mean'], cohort[name]['sd']) == (mean, sd), (name, cohort[name])
    utilizer_raw = [scores[r['id']]['utilizer'] for r in by_run]
    assert (round(statistics.mean(utilizer_raw), 2), round(statistics.stdev(utilizer_raw), 2)) \
        == CENTER_U_WITH_MISSING_CODE
    cohort['utilizer'] = stats([r['utilizer'] for r in by_run if r['utilizer'] != ''])
    llm = [r for r in by_run if r['method'] == 'llm_chat']

    summary = {
        'instrument': 'Defining Issues Test, version 2 (DIT-2)',
        'scored_by': 'Center for the Study of Ethical Development, University of Alabama',
        'administered_utc': [min(r['started_at_utc'] for r in runs), max(r['finished_at_utc'] for r in runs)],
        'center_file_name_date': '2026-11-04',
        'center_files_generated': '2026-11-06',
        'received': '2026-11-12',
        'source_files': [{'file': str(path.relative_to(HERE)), 'sha256': digest}
                         for path, digest in SOURCES.items()],
        'questionnaires_attempted': len(runs),
        'questionnaires_scored': len(by_run),
        'purged_by_center': sum(r['purged'] for r in by_run),
        'not_submitted': [{'id': int(r['id']), 'model': r['model'], 'run': int(r['run']),
                           'reason': r['exclusion_reason']} for r in runs if int(r['id']) not in scores],
        'all_scored_runs': cohort,
        'llm_runs_only': {name: stats([r[name] for r in llm]) for name in ['n2', 'p', 'maintaining_norms', 'personal_interest']},
        'utilizer_note': 'One run (id 10032) has the missing-value code 9.99 and is left out. '
                         'The Center\'s report averages that code in, giving 0.38 (SD 1.75).',
        'type_counts': {str(t): sum(r['type'] == t for r in by_run) for t in sorted({r['type'] for r in by_run})},
        'human_norms': human_norms(),
        'models': by_model,
        'runs': by_run,
    }
    run_fields = ['id', 'model', 'run', 'method'] + [public for _, public in SCORES] + DEMOGRAPHICS
    return {
        'scores-by-run.csv': to_csv(run_fields, by_run),
        'scores-by-model.csv': to_csv(list(by_model[0]), by_model),
        'summary.json': json.dumps(summary, indent=2) + '\n',
    }


def main():
    outputs = build()
    if '--check' in sys.argv[1:]:
        stale = [name for name, text in outputs.items()
                 if not (HERE / name).exists() or (HERE / name).read_text() != text]
        if stale:
            sys.exit('Out of date: ' + ', '.join(stale))
        print('DIT-2 outputs match the Center workbook and runs.csv.')
        return
    for name, text in outputs.items():
        (HERE / name).write_text(text)
    print('Wrote ' + ', '.join(outputs))


if __name__ == '__main__':
    main()
