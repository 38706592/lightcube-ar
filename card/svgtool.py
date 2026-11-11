"""Render chosen groups of the layered card SVG (光影立方_酷卡正面_分圖層.svg) to transparent RGBA at card.jpg size (1000×1480)."""
import xml.etree.ElementTree as ET, copy, numpy as np, pymupdf
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', 'http://www.w3.org/2000/svg'); ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
W, H = 1000, 1480
class Card:
    def __init__(self, path, shifts=None):
        self.root = ET.parse(path).getroot()
        self.shifts = shifts or {}   # group id → (dx, dy) in design px (600×888); SVG units are 0.75 design px
    def render(self, keep):
        return self._raster(self.svg(keep))
    def svg(self, keep):
        """keep: {top-group id: None (whole group) | set of sub-group ids | ('children', slice)}"""
        r = copy.deepcopy(self.root)
        for g in list(r):
            if g.tag != NS + 'g': continue
            gid = g.get('id')
            if gid not in keep: r.remove(g); continue
            sel = keep[gid]
            if isinstance(sel, set):
                for c in list(g):
                    if c.tag == NS + 'g' and c.get('id') and c.get('id') not in sel: g.remove(c)
            elif isinstance(sel, tuple):   # ('children', sub id, slice) – keep only some children of a sub-group
                _, sid, slc = sel
                for c in list(g):
                    if c.tag == NS + 'g' and c.get('id') and c.get('id') != sid: g.remove(c)
                sub = [c for c in g if c.get('id') == sid][0]
                kids = list(sub); keepk = set(map(id, kids[slc])) | {id(k) for k in kids if k.tag == NS + 'defs'}   # glyph symbols live in defs
                for c in kids:
                    if id(c) not in keepk: sub.remove(c)
            for c in g.iter():
                if c.get('id') in self.shifts:
                    dx, dy = self.shifts[c.get('id')]
                    c.set('transform', f'translate({dx * .75} {dy * .75}) ' + (c.get('transform') or ''))
        r.set('width', str(W)); r.set('height', str(H))
        return ET.tostring(r)
    def _raster(self, data):   # MuPDF fallback (no patterns / some clips) – the real layers are drawn in Chrome, see tools/render_layers.html
        doc = pymupdf.open(stream=data, filetype='svg'); p = doc[0]
        pm = p.get_pixmap(alpha=True, matrix=pymupdf.Matrix(W / p.rect.width, H / p.rect.height))
        return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 4).copy()
    def child_count(self, gid, sid):
        g = [x for x in self.root if x.get('id') == gid][0]; s = [x for x in g if x.get('id') == sid][0]
        return len(list(s))
def bbox(a, thr=4):
    ys, xs = np.nonzero(a[..., 3] > thr)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None
