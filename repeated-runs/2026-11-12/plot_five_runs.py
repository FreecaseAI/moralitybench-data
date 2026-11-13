#!/usr/bin/env python3
"""Generate publication overview figures (SVG, PDF, PNG) for the 2026-11-12 rerun cohort."""
import html
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _svg_fallback(models: list[dict]) -> str:
    w, h = 920, 290
    row_y = [108 + i * 52 for i in range(len(models))]
    # Left panel: Answer agreement (x: 190..500 -> 0..100%)
    lx0, lx1 = 190, 500
    # Right panel: Distance (x: 560..880 -> 0..0.75)
    rx0, rx1 = 560, 880

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
        '<text x="20" y="34" font-size="19" font-weight="700" fill="#1c1917">MoralityBench: November 12 OpenRouter reruns (280/280 complete)</text>',
        '<text x="190" y="68" font-size="13" font-weight="700" fill="#1c1917">Answer agreement (%)</text>',
        '<text x="560" y="68" font-size="13" font-weight="700" fill="#1c1917">Distance from US foundation means</text>',
    ]
    for pct in (0, 25, 50, 75, 100):
        x = lx0 + (lx1 - lx0) * (pct / 100.0)
        parts.append(f'<line x1="{x:.1f}" y1="82" x2="{x:.1f}" y2="{row_y[-1] + 28}" stroke="#e7e5e4" stroke-width="1"/>')
        parts.append(f'<text x="{x:.1f}" y="{row_y[-1] + 46}" font-size="10" fill="#57534e" text-anchor="middle">{pct}%</text>')
    for dval in (0.0, 0.25, 0.50, 0.75):
        x = rx0 + (rx1 - rx0) * (dval / 0.75)
        parts.append(f'<line x1="{x:.1f}" y1="82" x2="{x:.1f}" y2="{row_y[-1] + 28}" stroke="#e7e5e4" stroke-width="1"/>')
        parts.append(f'<text x="{x:.1f}" y="{row_y[-1] + 46}" font-size="10" fill="#57534e" text-anchor="middle">{dval:.2f}</text>')

    for idx, m in enumerate(models):
        cy = row_y[idx]
        bar_w = (lx1 - lx0) * (m['agreement'] / 100.0)
        parts.append(f'<text x="178" y="{cy + 4}" font-size="12" font-weight="600" fill="#1c1917" text-anchor="end">{html.escape(m["name"])}</text>')
        parts.append(f'<rect x="{lx0}" y="{cy - 12}" width="{bar_w:.1f}" height="24" rx="4" fill="{m["color"]}"/>')
        parts.append(f'<text x="{lx0 + bar_w + 6:.1f}" y="{cy + 4}" font-size="11" font-weight="600" fill="#1c1917">{m["agreement"]:.1f}%</text>')
        x_min = rx0 + (rx1 - rx0) * (m['distance_min'] / 0.75)
        x_max = rx0 + (rx1 - rx0) * (m['distance_max'] / 0.75)
        x_mean = rx0 + (rx1 - rx0) * (m['distance'] / 0.75)
        parts.append(f'<line x1="{x_min:.1f}" y1="{cy}" x2="{x_max:.1f}" y2="{cy}" stroke="#d6d3d1" stroke-width="4" stroke-linecap="round"/>')
        for r in m['runs']:
            rx = rx0 + (rx1 - rx0) * (r['distance'] / 0.75)
            parts.append(f'<circle cx="{rx:.1f}" cy="{cy}" r="4" fill="{m["color"]}" opacity="0.85"/>')
        parts.append(f'<polygon points="{x_mean:.1f},{cy - 6} {x_mean + 6:.1f},{cy} {x_mean:.1f},{cy + 6} {x_mean - 6:.1f},{cy}" fill="#1c1917"/>')
        parts.append(f'<text x="{x_max + 8:.1f}" y="{cy + 4}" font-size="11" fill="#44403c">{m["distance"]:.3f}</text>')

    parts.append(f'<text x="20" y="{h - 22}" font-size="10.5" fill="#57534e">Strict whole-answer integers across 5 fresh concurrent runs (280/280 items each). Dots mark runs; diamonds mark means.</text>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def main() -> None:
    summary = json.loads((ROOT / 'five-run-summary.json').read_text())
    models = summary['models']

    if importlib.util.find_spec('matplotlib') is not None:
        import os
        import tempfile
        os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'moralitybench-matplotlib'))
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, (left, right) = plt.subplots(1, 2, figsize=(12.8, 3.6), gridspec_kw={'width_ratios': [1.25, 1]})
        for i, m in enumerate(models):
            left.barh(i, m['agreement'], color=m['color'], height=.56)
            left.text(m['agreement'] + 1, i, f"{m['agreement']:.1f}%", va='center', fontsize=9)
            right.plot([m['distance_min'], m['distance_max']], [i, i], color='#d6d3d1', lw=3, zorder=1)
            for run in m['runs']:
                right.scatter(run['distance'], i, marker='o', s=23, color=m['color'], zorder=2)
            right.scatter(m['distance'], i, marker='D', s=32, color='#1c1917', zorder=3)
        left.set_yticks(range(len(models)), [m['name'] for m in models])
        right.set_yticks(range(len(models)), [''] * len(models))
        for ax in (left, right):
            ax.invert_yaxis()
            ax.spines[['top', 'right', 'left']].set_visible(False)
            ax.tick_params(axis='y', length=0)
            ax.grid(axis='x', alpha=.15)
            ax.set_axisbelow(True)
        left.set_xlim(0, 110)
        left.set_xticks([0, 25, 50, 75, 100])
        left.set_xlabel('Exact agreement across all ten pairs of five runs (%)')
        left.set_title('Answer agreement', loc='left', fontweight='bold')
        right.set_xlim(0, .75)
        right.set_xlabel('Distance from US foundation means (lower = closer)')
        right.set_title('Distance in each run', loc='left', fontweight='bold')
        fig.suptitle('MoralityBench: November 12 OpenRouter reruns', fontsize=15, fontweight='bold', x=.02, ha='left')
        fig.tight_layout(rect=[0, .06, 1, .93])
        for ext in ('png', 'pdf', 'svg'):
            fig.savefig(ROOT / f'five-run-overview.{ext}', dpi=180, bbox_inches='tight')
        svg = ROOT / 'five-run-overview.svg'
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
        print('Saved figure via matplotlib in PNG, PDF, and SVG.')
        return

    svg_path = ROOT / 'five-run-overview.svg'
    svg_path.write_text(_svg_fallback(models))
    if importlib.util.find_spec('weasyprint') is not None:
        import subprocess
        import weasyprint
        html_doc = f'<!doctype html><html><head><style>@page {{ size: 920px 290px; margin: 0; }} html, body {{ margin: 0; padding: 0; }}</style></head><body>{svg_path.read_text()}</body></html>'
        weasyprint.HTML(string=html_doc).write_pdf(str(ROOT / 'five-run-overview.pdf'))
        res = subprocess.run(['pdftoppm', '-png', '-r', '180', '-singlefile', str(ROOT / 'five-run-overview.pdf'), str(ROOT / 'five-run-overview')], capture_output=True, text=True)
        if res.returncode == 0:
            print('Saved figure via pure SVG + weasyprint/pdftoppm in SVG, PDF, and PNG.')
            return
    print('Saved SVG overview figure (matplotlib unavailable).')


if __name__ == '__main__':
    main()
