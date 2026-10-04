"""Optional publication figure; requires matplotlib. Analysis itself uses stdlib only."""
import json
import os
from pathlib import Path
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'moralitybench-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parent
summary = json.loads((ROOT/'five-run-summary.json').read_text())
models = summary['models'] + [summary['jev']]
fig, (left, right) = plt.subplots(1, 2, figsize=(12.8, 8), gridspec_kw={'width_ratios': [1.25, 1]})
for i, m in enumerate(models):
 color = '#0d9488' if i < 13 else '#b45309'
 left.barh(i, m['agreement'], color=color, height=.56)
 left.text(m['agreement'] + 1, i, f"{m['agreement']:.1f}%", va='center', fontsize=9)
 right.plot([m['distance_min'],m['distance_max']], [i,i], color='#d6d3d1', lw=3, zorder=1)
 for run in m['runs']:
  right.scatter(run['distance'], i, marker='o', s=23, color='#78716c' if run['run'] == 1 else '#0d9488', zorder=2)
 right.scatter(m['distance'], i, marker='D', s=32, color='#1c1917', zorder=3)
left.set_yticks(range(len(models)), [m['name'] for m in models]);right.set_yticks(range(len(models)), ['']*len(models))
for ax in [left,right]:
 ax.invert_yaxis();ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
 ax.axhline(12.5,color='#a8a29e',ls='--',lw=.8);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
left.set_xlim(0,110);left.set_xticks([0,25,50,75,100]);left.set_xlabel('Exact agreement across all ten pairs of five runs (%)')
left.set_title('Answer agreement',loc='left',fontweight='bold')
right.set_xlim(0,.76);right.set_xlabel('Distance from US foundation means (lower = closer)')
right.set_title('Distance in each run',loc='left',fontweight='bold')
fig.suptitle('MoralityBench: five repeated administrations',fontsize=16,fontweight='bold',x=.02,ha='left')
fig.text(.02,.025,'Missing answers are excluded from agreement; completion counts appear in the data table.\nDots: individual runs (gray: original). Black diamonds: five-run means. Jev is a separate protocol.',fontsize=10,color='#44403c')
fig.tight_layout(rect=[0,.075,1,.95])
for ext in ['png','pdf','svg']:fig.savefig(ROOT/f'five-run-overview.{ext}',dpi=180,bbox_inches='tight')
svg = ROOT/'five-run-overview.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
print('Saved figure in PNG, PDF, and SVG.')
