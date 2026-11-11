"""Split the card front (targets/card.jpg, 1000×1480) into liftable AR layers + a cover image.

Same idea as poster/split_poster.py: every layer is cut from the printed art, so the AR
matches the card exactly; every pixel belongs to the highest layer that claims it; the
cover is the card with all lifted pixels (and the printed cube stack) painted out.

usage: python card/split_card.py targets/card.jpg card
Boxes are card.jpg px, read from the card PDF's own vector boxes (2026-11-12 print version).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
im = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
H, W, _ = im.shape
PAPER = np.median(np.concatenate([im[5:25, 5:25].reshape(-1, 3), im[-25:-5, 400:600].reshape(-1, 3)]), 0)
COLS = {'orange': np.array([255, 148, 4.]), 'blue': np.array([37, 96, 163.]), 'black': np.array([0, 0, 0.])}
clamp = lambda a: np.clip(a, 0, 1)
lum = lambda p: p @ np.array([.299, .587, .114])

def key_alpha(p):
    return clamp((np.abs(p - PAPER).max(-1) - 28) / 50)

def color_alpha(p, c):   # strict: the light grid lines (≈45 % toward blue) stay out
    v = c - PAPER
    a = ((p - PAPER) @ v) / (v @ v)
    resid = np.linalg.norm(p - (PAPER + a[..., None] * v), axis=-1)
    return clamp((a - 0.5) / 0.4) * (resid < 48)

def dark_alpha(p):       # black ink only: rings / grid lines / colour blocks stay out
    return clamp((115 - lum(p)) / 70) * clamp((45 - np.abs(p - p.mean(-1, keepdims=True)).max(-1)) / 15)   # blue (lum 86, chroma 62) must stay out

def strong_alpha(p):
    return np.maximum.reduce([color_alpha(p, COLS['orange']), color_alpha(p, COLS['blue']), dark_alpha(p)])

G = True
ON_TOP = {'stripes'}   # printed on top of the cube stack
SPEC = [  # name, mode, (x, y, w, h), z, glitch
    ('gridTL', 'rect', (50, 325, 250, 367), .02, 0),
    ('gridBR', 'rect', (653, 782, 297, 283), .025, 0),
    ('gridBL', 'rect', (87, 998, 200, 250), .018, 0),
    ('frame', 'frame', (15, 37, 970, 1300), .012, 0),
    ('footer', 'key', (25, 1345, 950, 120), .03, 0),
    ('blueL', 'color:blue', (50, 548, 107, 317), .07, G),
    ('blueR', 'color:blue', (783, 325, 167, 90), .09, 0),
    ('orangeR', 'color:orange', (867, 415, 83, 250), .06, G),
    ('orangeSq', 'color:orange', (287, 1148, 116, 100), .2, 0),
    ('orangeDot', 'color:orange', (766, 897, 29, 29), .1, 0),
    ('hline', 'color:orange', (0, 748, 1000, 16), .1, G),
    ('blueBar', 'color:blue', (158, 929, 204, 22), .095, G),
    ('stripes', 'key', (550, 670, 250, 46), .11, G),
    ('miniCube', 'strong', (198, 507, 63, 71), .12, 0),
    ('blackSq', 'dark', (188, 636, 62, 62), .11, 0),
    ('dotsH', 'strong', (322, 970, 75, 25), .12, 0),
    ('dotsV', 'key', (788, 262, 26, 76), .12, 0),
    ('cross1', 'dark', (198, 777, 45, 60), .1, 0),
    ('cross2', 'dark', (345, 1060, 40, 60), .13, 0),
    ('crossBox', 'dark', (705, 422, 90, 115), .13, 0),
    ('tagline', 'dark', (318, 372, 510, 32), .1, 0),
    ('projMap', 'dark', (905, 690, 45, 405), .2, 0),
    ('lightCube', 'color:blue', (60, 890, 40, 268), .14, 0),
    ('date', 'key', (680, 60, 260, 205), .15, 0),
    ('t1o', 'color:orange', (50, 80, 600, 290), .15, G),
    ('t1b', 'color:blue', (50, 80, 600, 290), .17, G),
    ('t1k', 'dark', (50, 80, 600, 290), .19, G),
    ('t2o', 'color:orange', (380, 975, 580, 341), .15, G),
    ('t2b', 'color:blue', (380, 975, 580, 341), .17, G),
    ('t2k', 'dark', (380, 975, 580, 341), .19, G),
]

def raw_alpha(mode, box):
    x, y, w, h = box
    p = im[y:y + h, x:x + w]
    if mode == 'rect': return np.ones((h, w), np.float32)
    if mode == 'key': return key_alpha(p)
    if mode == 'dark': return dark_alpha(p)
    if mode == 'strong': return strong_alpha(p)
    if mode.startswith('color:'): return color_alpha(p, COLS[mode[6:]])
    if mode == 'frame':   # frame lines + the 8 handle squares only
        a = key_alpha(p); band = np.zeros((h, w), bool)
        for lx in (31, 969): band[:, max(0, lx - x - 4):lx - x + 5] = True
        for ly in (52, 1321): band[max(0, ly - y - 4):ly - y + 5, :] = True
        for sx, sy in [(30, 52), (500, 52), (970, 52), (30, 687), (970, 663), (30, 1322), (500, 1322), (970, 1322)]:
            band[max(0, sy - y - 13):sy - y + 14, max(0, sx - x - 13):sx - x + 14] = True
        return a * band

# the printed cube stack: union of the cube hexagons from the PDF outlines
HEX = json.load(open(os.path.join(os.path.dirname(__file__), 'stack_hexes.json')))
m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
for x0, y0, x1, y1 in HEX:
    cx, q = (x0 + x1) / 2, (y1 - y0) / 4
    dr.polygon([(cx, y0), (x1, y0 + q), (x1, y1 - q), (cx, y1), (x0, y1 - q), (x0, y0 + q)], fill=255)
stack = ndi.binary_dilation(np.asarray(m) > 0, iterations=4)

order = sorted(range(len(SPEC)), key=lambda i: -SPEC[i][3])
claimed = np.zeros((H, W), np.float32); total = np.zeros((H, W), np.float32)
results = {}; stack_done = False
for i in order:
    name, mode, box, z, glitch = SPEC[i]
    if z < 0.105 and not stack_done:
        claimed = np.maximum(claimed, stack.astype(np.float32)); stack_done = True
    x, y, w, h = box
    ra = raw_alpha(mode, box)
    free = 1 - claimed[y:y + h, x:x + w]
    if name not in ON_TOP: free = free * (1 - stack[y:y + h, x:x + w])   # nothing but the stripe block may take pixels of the printed stack
    p = im[y:y + h, x:x + w].copy()
    if mode == 'rect':   # grid (20-px cells): rebuilt by tiling the cleanest printed cell, so rings / text / stack bits printed over it stay out
        L = lum(p); chroma = np.abs(p - p.mean(-1, keepdims=True)).max(-1)
        junk = ((chroma < 12) & (L < 225)) | (strong_alpha(p) > 0.05)
        best = None
        for ty in range(0, h - 20, 2):
            for tx in range(0, w - 20, 2):
                n = junk[ty:ty + 20, tx:tx + 20].sum()
                if best is None or n < best[0]: best = (n, tx, ty)
                if n == 0: break
            if best[0] == 0: break
        _, tx, ty = best; tile = p[ty:ty + 20, tx:tx + 20]
        yy, xx = np.mgrid[0:h, 0:w]; out = tile[(yy - ty) % 20, (xx - tx) % 20]
        a = np.ones((h, w), np.float32); rgb = out
    else:
        a = ra * free
        if mode.startswith('color:'): rgb = np.broadcast_to(COLS[mode[6:]], p.shape).copy()
        elif mode == 'dark': rgb = np.zeros_like(p)
        else:
            aa = np.maximum(ra, 1e-3)[..., None]
            rgb = np.clip(PAPER + (p - PAPER) / aa, 0, 255)
    claimed[y:y + h, x:x + w] = np.maximum(claimed[y:y + h, x:x + w], ra * (mode != 'frame') if mode != 'rect' else 1)
    total[y:y + h, x:x + w] = np.maximum(total[y:y + h, x:x + w], ndi.binary_dilation(a > 0.02, iterations=2) if mode != 'rect' else 1)
    Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), 'RGBA').save(f'{OUT}/{name}.png', optimize=True)
    results[i] = dict(name=name, x=x, y=y, w=w, h=h, z=z, glitch=bool(glitch), shadow=mode not in ('frame',))
manifest = [results[i] for i in range(len(SPEC))]

A = np.maximum(total, stack.astype(np.float32))
cover = im * (1 - A[..., None]) + PAPER * A[..., None]
Image.fromarray(cover.astype(np.uint8)).save(f'{OUT}/cover.jpg', quality=88)
ys, xs = np.nonzero(np.asarray(m) > 0)
info = dict(W=W, H=H, paper='#%02X%02X%02X' % tuple(int(v) for v in PAPER),
            stack=dict(x=int(xs.min()), y=int(ys.min()), w=int(xs.max() - xs.min()), h=int(ys.max() - ys.min())), layers=manifest)
json.dump(info, open(f'{OUT}/layers.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(info['stack']), info['paper'], len(manifest), 'layers')
