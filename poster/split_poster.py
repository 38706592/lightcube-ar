"""Split the A1 poster into liftable AR layers + a cover image.

Each layer is cut from the poster itself (so it matches the print exactly),
keyed against the paper colour, and every pixel belongs to the highest layer
that claims it. The cover is the poster with all lifted pixels (and the
printed cube stack) painted out, so nothing doubles up when layers rise.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
im = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
H, W, _ = im.shape
PAPER = np.median(np.concatenate([im[:20, :20].reshape(-1, 3), im[-20:, -20:].reshape(-1, 3)]), 0)
COLS = {'orange': np.array([255, 149, 5.]), 'blue': np.array([37, 96, 164.]), 'black': np.array([12, 12, 12.])}
clamp = lambda a: np.clip(a, 0, 1)

def key_alpha(p):
    d = np.abs(p - PAPER).max(-1)
    return clamp((d - 28) / 50)

def color_alpha(p, c):
    v = c - PAPER
    a = ((p - PAPER) @ v) / (v @ v)
    resid = np.linalg.norm(p - (PAPER + a[..., None] * v), axis=-1)
    a = clamp(a) * (resid < 48)
    return clamp((a - 0.3) / 0.55)

G = True
SPEC = [  # name, mode, (x, y, w, h), z, glitch
    ('gridTL', 'rect', (80, 362, 282, 410), .02, 0),
    ('gridBR', 'rect', (755, 875, 333, 317), .025, 0),
    ('gridBL', 'rect', (122, 1117, 225, 280), .018, 0),
    ('frame', 'frame', (40, 42, 1090, 1458), .012, 0),
    ('footer', 'key', (55, 1488, 1060, 125), .03, 0),
    ('blueL', 'key', (80, 615, 120, 353), .07, G),
    ('blueR', 'key', (900, 364, 188, 102), .09, 0),
    ('orangeR', 'key', (993, 466, 95, 280), .06, G),
    ('orangeSq', 'key', (345, 1285, 131, 112), .08, 0),
    ('hline', 'color:orange', (0, 834, 1169, 22), .1, G),
    ('stripes', 'stripes', (645, 748, 277, 56), .11, G),
    ('miniCube', 'key', (248, 568, 68, 74), .12, 0),
    ('blackSq', 'key', (240, 716, 64, 62), .1, 0),
    ('dots', 'key', (908, 298, 26, 80), .12, 0),
    ('cross1', 'key', (228, 873, 62, 62), .13, 0),
    ('cross2', 'key', (388, 1188, 62, 62), .13, 0),
    ('crossBox', 'key', (818, 466, 92, 124), .13, 0),
    ('tagline', 'key', (383, 392, 552, 30), .1, 0),
    ('projMap', 'key', (1043, 778, 32, 370), .14, 0),
    ('lightCube', 'key', (100, 1008, 32, 290), .14, 0),
    ('date', 'key', (772, 78, 312, 225), .15, 0),
    ('t1o', 'color:orange', (95, 100, 625, 295), .15, G),
    ('t1b', 'color:blue', (95, 100, 625, 295), .17, G),
    ('t1k', 'color:black', (95, 100, 625, 295), .19, G),
    ('t2o', 'color:orange', (480, 1158, 605, 310), .15, G),
    ('t2b', 'color:blue', (480, 1158, 605, 310), .17, G),
    ('t2k', 'color:black', (480, 1158, 605, 310), .19, G),
]

def raw_alpha(mode, box):
    x, y, w, h = box
    p = im[y:y + h, x:x + w]
    if mode == 'rect':
        return np.ones((h, w), np.float32)
    if mode == 'key':
        return key_alpha(p)
    if mode == 'color:black':  # black takes every inked pixel that isn't clearly orange or blue
        return clamp(key_alpha(p) - np.maximum(color_alpha(p, COLS['orange']), color_alpha(p, COLS['blue'])) * 1.2)
    if mode.startswith('color:'):
        return color_alpha(p, COLS[mode[6:]])
    if mode == 'stripes':  # rows read where the stripes cross plain paper, extended across
        prof = color_alpha(im[y:y + h, 880:915], COLS['orange']).mean(1)
        return np.repeat(clamp(prof * 1.1)[:, None], w, 1)
    if mode == 'frame':
        a = key_alpha(p)
        band = np.zeros((h, w), bool)
        for lx in (59 - x, 1110 - x):
            band[:, max(0, lx - 4):lx + 5] = True
        for ly in (60 - y, 1478 - y):
            band[max(0, ly - 4):ly + 5, :] = True
        for sx in (59, 585, 1110):
            for sy in (60, 769, 1478):
                band[max(0, sy - y - 14):sy - y + 15, max(0, sx - x - 14):sx - x + 15] = True
        return a * band

# the printed cube stack: isometric silhouette (hex width 175, edge 101 px)
from PIL import ImageDraw
POLY = [(585,541),(672,591),(672,692),(760,742),(760,843),(847,893),(847,995),(760,1045),(672,995),
        (585,1045),(497,995),(410,1045),(322,995),(322,893),(410,843),(410,742),(497,692),(497,591)]
m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(POLY, fill=255)
stack = ndi.binary_dilation(np.asarray(m) > 0, iterations=5)

order = sorted(range(len(SPEC)), key=lambda i: -SPEC[i][3])
claimed = np.zeros((H, W), np.float32)
total = np.zeros((H, W), np.float32)
manifest = []
results = {}
stack_done = False
for i in order:
    name, mode, box, z, glitch = SPEC[i]
    if z < 0.105 and not stack_done:
        claimed = np.maximum(claimed, stack.astype(np.float32))
        stack_done = True
    x, y, w, h = box
    ra = raw_alpha(mode, box)
    free = 1 - claimed[y:y + h, x:x + w]
    p = im[y:y + h, x:x + w].copy()
    if mode == 'rect':
        hole = free < 0.5
        out = p.copy()
        for yy, xx in zip(*np.nonzero(hole)):  # repeat the grid pattern into covered spots
            for dx in (89, -89, 178, -178, 267, -267):
                sx = xx + dx
                if 0 <= sx < w and not hole[yy, sx]:
                    out[yy, xx] = p[yy, sx]; break
            else:
                out[yy, xx] = np.median(p[~hole], 0)
        a = np.ones((h, w), np.float32)
        rgb = out
    else:
        a = ra * free
        if mode.startswith('color:') or mode == 'stripes':
            rgb = np.broadcast_to(COLS.get(mode[6:], COLS['orange']), p.shape).copy()
        else:
            aa = np.maximum(ra, 1e-3)[..., None]
            rgb = np.clip(PAPER + (p - PAPER) / aa, 0, 255)
    claimed[y:y + h, x:x + w] = np.maximum(claimed[y:y + h, x:x + w], ra * (mode != 'frame') if mode != 'rect' else 1)
    total[y:y + h, x:x + w] = np.maximum(total[y:y + h, x:x + w], ndi.binary_dilation(a > 0.02, iterations=2) if mode != 'rect' else 1)
    rgba = np.dstack([rgb, a * 255]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(f'{OUT}/{name}.png', optimize=True)
    results[i] = dict(name=name, x=x, y=y, w=w, h=h, z=z, glitch=bool(glitch),
                      shadow=mode not in ('frame',))
manifest = [results[i] for i in range(len(SPEC))]

# cover: poster with every lifted pixel and the printed stack painted out
A = np.maximum(total, stack.astype(np.float32))
cover = im * (1 - A[..., None]) + PAPER * A[..., None]
Image.fromarray(cover.astype(np.uint8)).save(f'{OUT}/cover.jpg', quality=88)

# stack silhouette bbox in poster px, for placing the 3D cubes
ys, xs = np.nonzero(np.asarray(m) > 0)
info = dict(W=W, H=H, paper='#%02X%02X%02X' % tuple(int(v) for v in PAPER),
            stack=dict(x=int(xs.min()), y=int(ys.min()), w=int(xs.max() - xs.min()), h=int(ys.max() - ys.min())),
            layers=manifest)
json.dump(info, open(f'{OUT}/layers.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(info['stack']), info['paper'], len(manifest), 'layers')
