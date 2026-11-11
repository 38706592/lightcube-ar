"""Card AR layers rendered straight from the layered source SVG (光影立方_酷卡正面_分圖層.svg), one transparent PNG per element.

The source SVG is the pre-2026-11-12 layout; the print moved two things, applied here so the AR matches the printed card:
  tagline 'CUBE × LIGHT × PARTICLE × SPACE' (labels-03) down 15 design px; footer strip (footer) down 12.5 design px.
Coordinates: card.jpg px (1000×1480 = 600×888 design px × 5/3).
usage: 1) python card/build_card_layers.py svgs <layered svg> <svg dir>   → one isolated SVG per layer (+ bg, STACK)
       2) draw them in Chrome: tools/render_layers.html (MuPDF cannot draw the hatch patterns / clips) → PNGs 1000×1480
       3) python card/build_card_layers.py pack <layered svg> <png dir> card   → cropped layers + cover.jpg + layers.json
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from svgtool import Card, bbox

MODE, SVG = sys.argv[1], sys.argv[2]
card = Card(SVG, shifts={'labels-03': (0, 15), 'footer-01': (0, 12.5)})
G = True
# name, keep, z, glitch, shadow
SPEC = [
    ('gridTL', {'grid-blocks': {'grid-blocks-01'}}, .02, 0, 1),
    ('gridBR', {'grid-blocks': {'grid-blocks-02'}}, .025, 0, 1),
    ('gridBL', {'grid-blocks': {'grid-blocks-03'}}, .018, 0, 1),
    ('blueL', {'grid-blocks': {'grid-blocks-04'}}, .07, G, 1),
    ('blueR', {'grid-blocks': {'grid-blocks-05'}}, .09, 0, 1),
    ('orangeR', {'grid-blocks': {'grid-blocks-06'}}, .06, G, 1),
    ('orangeSq', {'grid-blocks': {'grid-blocks-07'}}, .08, 0, 1),
    ('rings', {'ring': None}, .045, 0, 0),
    ('hline', {'glitch-bars': {'glitch-bars-01'}}, .1, G, 1),
    ('stripes', {'glitch-bars': {'glitch-bars-02'}}, .11, G, 1),
    ('blueBar', {'glitch-bars': {'glitch-bars-03'}}, .095, G, 1),
    ('blackBar', {'glitch-bars': {'glitch-bars-04'}}, .1, 0, 1),
    ('miniWire', {'cube-stack': ('children', 'cube-stack-01', slice(95, 97))}, .12, 0, 1),
    ('miniCube', {'cube-stack': ('children', 'cube-stack-01', slice(97, 101))}, .12, 0, 1),
    ('blackSq', {'cube-stack': ('children', 'cube-stack-01', slice(101, 103))}, .1, 0, 1),
    ('orangeDot', {'cube-stack': ('children', 'cube-stack-01', slice(103, 104))}, .1, 0, 1),
    ('check', {'pixel-dots': {'pixel-dots-01'}}, .2, 0, 1),   # drawn after the title in the source, sits on top of its glitch slice
    ('dotsH', {'pixel-dots': {'pixel-dots-02'}}, .12, 0, 1),
    ('dotsV', {'pixel-dots': {'pixel-dots-03'}}, .12, 0, 1),
    ('cross0', {'pixel-dots': {'pixel-dots-04'}}, .13, 0, 0),
    ('cross1', {'pixel-dots': {'pixel-dots-05'}}, .13, 0, 0),
    ('cross2', {'pixel-dots': {'pixel-dots-06'}}, .13, 0, 0),
    ('tagline', {'labels': {'labels-03'}}, .1, 0, 1),
    ('projMap', {'labels': {'labels-01'}}, .14, 0, 1),
    ('lightCube', {'labels': {'labels-02'}}, .14, 0, 1),
    ('date', {'date': None}, .15, 0, 1),
    ('t1o', {'title-1': {'title-1-k0'}}, .15, G, 0),
    ('t1b', {'title-1': {'title-1-k1'}}, .17, G, 0),
    ('t1k', {'title-1': {'title-1-k2', 'title-1-k3'}}, .19, G, 1),
    ('t1sq', {'title-1': {'title-1-k4'}}, .21, 0, 1),
    ('t2o', {'title-2': {'title-2-k0'}}, .15, G, 0),
    ('t2b', {'title-2': {'title-2-k1'}}, .17, G, 0),
    ('t2k', {'title-2': {'title-2-k2', 'title-2-k3'}}, .19, G, 1),
    ('frame', {'frame': None}, .012, 0, 0),
    ('footer', {'footer': None}, .03, 0, 1),
]
EXTRA = [('bg', {'bg': None}), ('STACK', {'cube-stack': ('children', 'cube-stack-01', slice(0, 95))})]
if MODE == 'svgs':
    D = sys.argv[3]; os.makedirs(D, exist_ok=True)
    for name, keep, *_ in SPEC + EXTRA: open(f'{D}/{name}.svg', 'wb').write(card.svg(keep))
    print(len(SPEC) + len(EXTRA), 'svgs →', D); sys.exit()

PNG, OUT = sys.argv[3], sys.argv[4]
DX, DY = 0, -2   # the printed PDF sits 2 px (card.jpg) higher than the source SVG; measured by best-fit against targets/card.jpg
os.makedirs(OUT, exist_ok=True)
manifest = []
for name, keep, z, glitch, shadow in SPEC:
    a = np.asarray(Image.open(f'{PNG}/{name}.png').convert('RGBA')); b = bbox(a)
    if b is None: print('EMPTY', name); continue
    x0, y0, x1, y1 = b; x0, y0 = max(0, x0 - 2), max(0, y0 - 2); x1, y1 = min(a.shape[1], x1 + 2), min(a.shape[0], y1 + 2)
    Image.fromarray(a[y0:y1, x0:x1], 'RGBA').save(f'{OUT}/{name}.png', optimize=True)
    manifest.append(dict(name=name, x=x0 + DX, y=y0 + DY, w=x1 - x0, h=y1 - y0, z=z, glitch=bool(glitch), shadow=bool(shadow)))
# cover: plain card paper — every printed element is its own layer, and the printed cube stack is replaced by the 3D stack
Image.open(f'{PNG}/bg.png').convert('RGB').save(f'{OUT}/cover.jpg', quality=92)
st = (190, 469, 840, 1041)   # printed cube outlines, from the card PDF
import time
info = dict(v=time.strftime('%Y%m%d%H%M%S'), W=1000, H=1480, paper='#F6F4EF', stack=dict(x=st[0], y=st[1], w=st[2] - st[0], h=st[3] - st[1]), layers=manifest)
json.dump(info, open(f'{OUT}/layers.json', 'w'), ensure_ascii=False, indent=1)
print(len(manifest), 'layers')
