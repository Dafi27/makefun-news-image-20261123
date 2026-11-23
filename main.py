#!/usr/bin/env python3
"""news-image-20261123: sums up Monday 23 November 2026 world news in one
1024x1024 PNG. Pure standard library: renders the picture with a 5x7 pixel
font and shape drawing, then encodes the PNG itself with zlib.
Writes to $MAKEFUN_OUTPUT_DIR/entry.png (default ./out/entry.png).
Deterministic: two runs produce byte-identical output."""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '#' = on.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = x1 - x0, y1 - y0
        n = max(abs(dx), abs(dy), 1)
        for i in range(n + 1):
            x = x0 + dx * i // n
            y = y0 + dy * i // n
            for a in range(-(t // 2), t // 2 + 1):
                for b in range(-(t // 2), t // 2 + 1):
                    self.set(x + a, y + b, c)

    def tri(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        def area(ax, ay, bx, by, cx, cy):
            return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        d = area(x0, y0, x1, y1, x2, y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = area(xx, yy, x1, y1, x2, y2)
                b = area(x0, y0, xx, yy, x2, y2)
                cc = area(x0, y0, x1, y1, xx, yy)
                if (d > 0 and a >= 0 and b >= 0 and cc >= 0) or \
                   (d < 0 and a <= 0 and b <= 0 and cc <= 0):
                    self.set(xx, yy, c)

    def text(self, x, y, s, scale, c):
        """Draw uppercase text; returns width in px."""
        cx = x
        for ch in s.upper():
            g = FONT.get(ch, FONT[' '])
            for r, row in enumerate(g):
                for col, bit in enumerate(row):
                    if bit == '1':
                        self.rect(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx - x

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def wrap(self, x, y, s, scale, c, max_w, lh=None):
        """Word-wrap text into lines of at most max_w px. Returns end y."""
        if lh is None:
            lh = 8 * scale
        words = s.upper().split(' ')
        lines, cur = [], ''
        for wd in words:
            trial = (cur + ' ' + wd).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        for ln in lines:
            self.text(x, y, ln, scale, c)
            y += lh
        return y

    def center(self, y, s, scale, c, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)

# ---------------------------------------------------------------- palette
NAVY   = bytes((13, 27, 62))
NAVY2  = bytes((24, 48, 96))
PAPER  = bytes((247, 243, 232))
INK    = bytes((18, 24, 38))
MUTED  = bytes((90, 96, 112))
WHITE  = bytes((255, 255, 255))
RED    = bytes((196, 42, 42))
ORANGE = bytes((232, 122, 26))
GOLD   = bytes((212, 160, 23))
GREEN  = bytes((34, 139, 84))
TEAL   = bytes((14, 130, 140))
BLUE   = bytes((38, 110, 190))
SKY    = bytes((120, 190, 225))
SAND   = bytes((222, 205, 164))
GREY   = bytes((150, 156, 170))
DARK   = bytes((60, 66, 80))

# ---------------------------------------------------------------- pictograms
def pic_globe(cv, cx, cy, r):
    """Earth with a red slash: climate talks fail."""
    cv.disc(cx, cy, r, BLUE)
    cv.disc(cx - r // 3, cy - r // 4, r // 3, GREEN)
    cv.disc(cx + r // 3, cy + r // 3, r // 4, GREEN)
    cv.disc(cx + r // 4, cy - r // 2, r // 5, GREEN)
    cv.line(cx - r, cy + r, cx + r, cy - r, RED, 7)
    # ring outline
    for a in range(0, 360, 3):
        import math
        x = int(cx + r * math.cos(math.radians(a)))
        y = int(cy + r * math.sin(math.radians(a)))
        cv.set(x, y, NAVY)

def pic_tanker(cv, x, y, w, h):
    """Oil tanker on waves with a flame."""
    hull_y = y + h // 2
    cv.rect(x, hull_y, w, h // 4, DARK)
    cv.rect(x + w // 6, hull_y - h // 4, w // 5, h // 4, RED)
    cv.rect(x + w // 2, hull_y - h // 5, w // 8, h // 5, DARK)
    # flame above the deck, wide and short
    fx = x + int(w * 0.72)
    cv.tri([(fx, hull_y - h // 3), (fx - 22, hull_y - 4), (fx + 22, hull_y - 4)], ORANGE)
    cv.tri([(fx, hull_y - h // 3 - 6), (fx - 10, hull_y - 18), (fx + 10, hull_y - 18)], GOLD)
    # waves
    for i, wy in enumerate((hull_y + h // 4 + 8, hull_y + h // 4 + 20)):
        for xx in range(x, x + w, 26):
            cv.line(xx, wy, xx + 13, wy - 5, BLUE, 3)

def pic_ship_sink(cv, x, y, w, h):
    """Warship listing and sinking, smoke above."""
    # smoke puffs
    cv.disc(x + w // 3, y + 14, 12, GREY)
    cv.disc(x + w // 3 + 18, y + 6, 9, GREY)
    cv.disc(x + w // 3 - 16, y + 8, 8, GREY)
    # tilted hull: two stacked rects at an angle via lines
    cv.line(x + 6, y + h // 2 + 30, x + w - 6, y + h // 2 + 6, DARK, 16)
    cv.line(x + 14, y + h // 2 + 18, x + w - 20, y + h // 2 - 4, RED, 8)
    cv.line(x + w // 2, y + h // 2 - 6, x + w // 2 + 8, y + h // 2 - 44, DARK, 8)
    # water line, just under the hull
    cv.rect(x, y + h - 44, w, 6, BLUE)
    cv.rect(x, y + h - 32, w, 4, SKY)

def pic_rescue(cv, x, y, w, h):
    """Broken apartment block, rubble, a small figure carried out."""
    bx, by = x + 8, y + 6
    cv.rect(bx, by, 52, h - 30, SAND)
    cv.rect(bx + 26, by, 26, 34, DARK)          # broken corner
    for wy in range(by + 12, by + h - 42, 22):
        cv.rect(bx + 8, wy, 12, 12, NAVY2)
        cv.rect(bx + 32, wy, 12, 12, NAVY2)
    # rubble
    cv.tri([(bx + 60, y + h - 22), (bx + 78, y + h - 44), (bx + 96, y + h - 22)], GREY)
    cv.tri([(bx + 88, y + h - 22), (bx + 104, y + h - 38), (bx + 118, y + h - 22)], DARK)
    # rescuer + child: two figures
    cv.disc(x + w - 34, y + h - 62, 8, INK)
    cv.rect(x + w - 40, y + h - 54, 12, 26, RED)
    cv.disc(x + w - 52, y + h - 56, 6, INK)
    cv.rect(x + w - 57, y + h - 50, 10, 16, GOLD)

def pic_exports(cv, x, y, w, h):
    """Rising bars and arrow: exports hit $1 trillion."""
    base = y + h - 18
    bars = [26, 42, 58, 80]
    bw = 22
    for i, bh in enumerate(bars):
        bx = x + 10 + i * 34
        cv.rect(bx, base - bh, bw, bh, (GREEN, TEAL, BLUE, GOLD)[i])
    cv.line(x + 8, base - 88, x + w - 8, base - 108, RED, 4)
    cv.tri([(x + w - 8, base - 108), (x + w - 26, base - 108), (x + w - 12, base - 122)], RED)
    cv.text(x + 8, y + 2, "$1T", 2, INK)

def pic_maths(cv, x, y, w, h):
    """Chalkboard with the zeta equation and a big tick."""
    cv.rect(x + 6, y + 6, w - 12, h - 34, NAVY2)
    cv.rect(x + 6, y + 6, w - 12, 6, GOLD)
    cv.text(x + 18, y + 26, "Z(S) = 0", 3, WHITE)
    cv.text(x + 18, y + 62, "PROOF?", 3, GOLD)
    # green tick
    cv.line(x + w - 52, y + h - 34, x + w - 34, y + h - 14, GREEN, 6)
    cv.line(x + w - 34, y + h - 14, x + w - 6, y + h - 52, GREEN, 6)

# ---------------------------------------------------------------- layout
STORIES = [
    ("CLIMATE", RED, "CLIMATE TALKS FAIL",
     "COP31 ends with no deal on fossil fuels in Antalya",
     pic_globe),
    ("MIDDLE EAST", ORANGE, "TANKERS HIT IN HORMUZ",
     "Trump threatens to sink Iranian vessels after strikes",
     pic_tanker),
    ("WAR AT SEA", NAVY2, "RUSSIAN WARSHIP SINKS",
     "Frigate Merkury capsizes at Benghazi after suspected drone strike",
     pic_ship_sink),
    ("UKRAINE", TEAL, "BOY, 7, PULLED ALIVE",
     "Rescued from rubble after a Russian strike near Kyiv",
     pic_rescue),
    ("ECONOMY", GREEN, "KOREA EXPORTS TOP $1 TRILLION",
     "A first, driven by global demand for AI chips",
     pic_exports),
    ("SCIENCE", BLUE, "MATHS PROOF CLAIMED",
     "Anthropic team says Claude helped prove the Riemann Hypothesis",
     pic_maths),
]

def draw_panel(cv, x, y, w, h, tag, accent, headline, sub, pic):
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, 4, accent)
    cv.rect(x, y, w, 34, accent)
    cv.text(x + 12, y + 9, tag, 2, WHITE)
    # pictogram on the left
    ix, iy, iw, ih = x + 12, y + 46, 150, h - 58
    if pic is pic_globe:
        pic(cv, ix + iw // 2, iy + ih // 2, 52)
    else:
        pic(cv, ix, iy, iw, ih)
    # text on the right
    tx = x + 176
    tw = w - 176 - 14
    ny = cv.wrap(tx, y + 50, headline, 3, INK, tw, lh=26)
    cv.wrap(tx, ny + 6, sub, 2, MUTED, tw, lh=18)

def render():
    cv = Canvas(W, H, PAPER)
    # header
    cv.rect(0, 0, W, 148, NAVY)
    cv.rect(0, 148, W, 6, GOLD)
    cv.center(18, "THE WORLD IN ONE DAY", 2, GOLD)
    cv.center(48, "23 NOVEMBER 2026", 6, WHITE)
    cv.center(112, "MONDAY  -  SIX STORIES THAT MATTERED", 2, SKY)
    # grid 2 x 3
    gx, gy = 16, 168
    pw, ph, gap = 490, 258, 12
    for i, (tag, accent, head, sub, pic) in enumerate(STORIES):
        px = gx + (i % 2) * (pw + gap)
        py = gy + (i // 2) * (ph + gap)
        draw_panel(cv, px, py, pw, ph, tag, accent, head, sub, pic)
    # footer
    fy = 168 + 3 * ph + 2 * gap + 8
    cv.center(fy, "REPORTED 23 NOVEMBER 2026  -  BBC, REUTERS, AP", 2, MUTED)
    return cv

# ---------------------------------------------------------------- PNG encode
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[yy * stride:(yy + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "./out")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(render())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes, {W}x{H})")

if __name__ == "__main__":
    main()
