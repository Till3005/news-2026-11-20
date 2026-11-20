#!/usr/bin/env python3
"""
THE WORLD DAILY -- front page of Friday, 20 November 2026.

A make.fun bounty entry ("Sum up 20 November's world news in one image").

Pure Python 3 standard library. No fonts, no images, no network: every
glyph, rule and pictogram is plotted pixel by pixel into an RGB
framebuffer and encoded as a PNG with our own chunk writer.

Output: /output/entry.png  (override location with env var OUT).
Deterministic: same input, same bytes, every run.
"""

import math
import os
import struct
import zlib

W = H = 1024

# Fixed palette
PAPER = (244, 238, 218)   # cream newsprint
INK = (28, 26, 22)        # near-black ink
CRIMSON = (179, 43, 43)   # accent red
BLUE = (47, 74, 107)      # muted editorial blue

_buf = bytearray(W * H * 3)


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        _buf[i] = c[0]
        _buf[i + 1] = c[1]
        _buf[i + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, W)
    y1 = min(y + h, H)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        for _ in range(x0, x1):
            _buf[i] = c[0]
            _buf[i + 1] = c[1]
            _buf[i + 2] = c[2]
            i += 3


def outline_rect(x, y, w, h, c, t=1):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    """Bresenham line with square-stamp thickness."""
    o = (t - 1) // 2
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        rect(x0 - o, y0 - o, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    r2 = r * r
    for dy in range(-r, r + 1):
        hw = int(math.sqrt(r2 - dy * dy))
        rect(cx - hw, cy + dy, 2 * hw + 1, 1, c)


def half_disc_down(cx, cy, r, c):
    r2 = r * r
    for dy in range(0, r + 1):
        hw = int(math.sqrt(r2 - dy * dy))
        rect(cx - hw, cy + dy, 2 * hw + 1, 1, c)


def ring(cx, cy, r, c, t=1):
    n = max(48, int(6.3 * r))
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        rect(x - (t - 1) // 2, y - (t - 1) // 2, t, t, c)


def arc(cx, cy, r, a0, a1, c, t=1):
    n = max(24, int(abs(a1 - a0) * r * 1.5))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        rect(x - (t - 1) // 2, y - (t - 1) // 2, t, t, c)


def ellipse_ring(cx, cy, rx, ry, rot, c, t=1):
    n = 240
    cr = math.cos(rot)
    sr = math.sin(rot)
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        ex = rx * math.cos(a)
        ey = ry * math.sin(a)
        x = int(round(cx + ex * cr - ey * sr))
        y = int(round(cy + ex * sr + ey * cr))
        rect(x, y, t, t, c)


# --------------------------------------------------------------------------
# Embedded 5x7 pixel font (hand-drawn glyph table)
# --------------------------------------------------------------------------

FONT = {
    " ": ["00000"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00110", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "'": ["01100", "01100", "00100", "00000", "00000", "00000", "00000"],
    '"': ["11011", "11011", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "&": ["01100", "10010", "10010", "01100", "10101", "10010", "01101"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "00110", "00110", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "*": ["00000", "00100", "10101", "01110", "10101", "00100", "00000"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
}


def draw_text(x, y, s, scale, c):
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for ry in range(7):
            row = g[ry]
            for rx in range(5):
                if row[rx] == "1":
                    rect(x + rx * scale, y + ry * scale, scale, scale, c)
        x += 6 * scale


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def center_text(y, s, scale, c):
    draw_text((W - text_w(s, scale)) // 2, y, s, scale, c)


def right_text(x_right, y, s, scale, c):
    draw_text(x_right - text_w(s, scale), y, s, scale, c)


# --------------------------------------------------------------------------
# Pictograms (drawn from primitives)
# --------------------------------------------------------------------------

def pico_barrel(x, y):
    """Oil barrel with a falling arrow (summit-pact oil plunge)."""
    bx = x + 38
    rect(bx, y + 18, 52, 66, INK)                        # barrel body
    ellipse_ring(bx + 26, y + 18, 26, 7, 0.0, INK, 2)    # top rim
    ellipse_ring(bx + 26, y + 84, 26, 7, 0.0, INK, 2)    # bottom rim
    ellipse_ring(bx + 26, y + 38, 26, 5, 0.0, PAPER, 2)  # hoop
    ellipse_ring(bx + 26, y + 62, 26, 5, 0.0, PAPER, 2)  # hoop
    ax = x + 108
    line(ax, y + 16, ax, y + 86, CRIMSON, 4)             # arrow shaft
    line(ax, y + 86, ax - 12, y + 70, CRIMSON, 3)        # arrow head
    line(ax, y + 86, ax + 12, y + 70, CRIMSON, 3)


def pico_folder(x, y):
    """A case folder with a crimson seal (Epstein files subpoenas)."""
    outline_rect(x + 5, y + 11, 34, 26, INK, 2)          # folder body
    rect(x + 5, y + 7, 14, 4, INK)                       # tab
    rect(x + 10, y + 20, 24, 2, INK)                     # document line
    rect(x + 10, y + 26, 18, 2, INK)                     # document line
    disc(x + 32, y + 17, 3, CRIMSON)                     # seal


def pico_euro(x, y):
    """Euro sign with loose coins (German aid pledge)."""
    cx, cy = x + 24, y + 22
    arc(cx, cy, 13, 0.9, 5.38, INK, 2)                   # C sweep, opens right
    line(cx - 15, cy - 4, cx + 3, cy - 4, INK, 2)        # upper bar
    line(cx - 15, cy + 4, cx + 3, cy + 4, INK, 2)        # lower bar
    disc(x + 36, y + 30, 3, CRIMSON)                     # coin
    disc(x + 41, y + 37, 3, CRIMSON)                     # coin


def pico_jet(x, y):
    """Fighter jet in top view (Saudi strikes on Houthi sites)."""
    cx = x + 22
    rect(cx - 2, y + 4, 5, 36, INK)                      # fuselage
    line(cx, y + 16, cx - 18, y + 30, INK, 3)            # left wing
    line(cx, y + 16, cx + 18, y + 30, INK, 3)            # right wing
    line(cx, y + 38, cx - 9, y + 42, INK, 2)             # left tail
    line(cx, y + 38, cx + 9, y + 42, INK, 2)             # right tail
    disc(cx - 17, y + 34, 2, CRIMSON)                    # dropped ordnance
    disc(cx + 17, y + 34, 2, CRIMSON)


def pico_truck(x, y):
    """Aid truck with a crimson cross (Gaza convoy)."""
    outline_rect(x + 4, y + 12, 24, 16, INK, 2)          # cargo box
    line(x + 16, y + 16, x + 16, y + 24, CRIMSON, 2)     # cross upright
    line(x + 12, y + 20, x + 20, y + 20, CRIMSON, 2)     # cross arm
    rect(x + 30, y + 20, 10, 8, INK)                     # cab
    disc(x + 11, y + 32, 3, INK)                         # wheels
    disc(x + 22, y + 32, 3, INK)
    disc(x + 36, y + 32, 3, INK)
    rect(x + 2, y + 38, 40, 2, INK)                      # road


def pico_torii(x, y):
    """Torii gate (Japan tightens Russia sanctions)."""
    rect(x + 4, y + 5, 36, 4, CRIMSON)                   # kasagi
    rect(x + 9, y + 12, 26, 2, CRIMSON)                  # upper tie
    rect(x + 11, y + 9, 4, 30, CRIMSON)                  # left pillar
    rect(x + 29, y + 9, 4, 30, CRIMSON)                  # right pillar
    rect(x + 13, y + 20, 18, 3, CRIMSON)                 # nuki beam
    rect(x + 9, y + 39, 8, 2, CRIMSON)                   # base stones
    rect(x + 27, y + 39, 8, 2, CRIMSON)


def pico_globe(x, y):
    """Globe with a crimson equator (COP31 talks)."""
    cx, cy = x + 22, y + 23
    ring(cx, cy, 15, INK, 2)
    ellipse_ring(cx, cy, 6, 15, 0.0, INK, 1)             # meridian
    line(cx - 13, cy - 7, cx + 13, cy - 7, INK, 1)       # north latitude
    line(cx - 13, cy + 7, cx + 13, cy + 7, INK, 1)       # south latitude
    line(cx - 15, cy, cx + 15, cy, CRIMSON, 2)           # warming line


def pico_tennis(x, y):
    """Tennis ball (ATP Finals, Turin)."""
    cx, cy = x + 22, y + 22
    ring(cx, cy, 14, INK, 2)
    arc(cx - 14, cy, 21, -0.5, 0.5, INK, 2)              # left seam
    arc(cx + 14, cy, 21, math.pi - 0.5, math.pi + 0.5, INK, 2)  # right seam


def pico_flare(x, y):
    """Flaring sun (X6 solar eruption)."""
    cx, cy = x + 22, y + 24
    disc(cx, cy, 9, CRIMSON)
    for k in range(8):
        a = k * math.pi / 4
        x0 = cx + int(round(11 * math.cos(a)))
        y0 = cy + int(round(11 * math.sin(a)))
        x1 = cx + int(round(19 * math.cos(a)))
        y1 = cy + int(round(19 * math.sin(a)))
        line(x0, y0, x1, y1, INK, 2)


def pico_chat(x, y):
    """Speech bubble (OpenAI delays GPT-6)."""
    outline_rect(x + 4, y + 8, 36, 22, INK, 2)
    line(x + 12, y + 30, x + 12, y + 38, INK, 2)         # tail
    line(x + 12, y + 38, x + 20, y + 30, INK, 2)
    disc(x + 12, y + 19, 2, CRIMSON)
    disc(x + 21, y + 19, 2, CRIMSON)
    disc(x + 30, y + 19, 2, CRIMSON)


def pico_quill(x, y):
    """Quill pen with an ink drop (opinion essay)."""
    line(x + 12, y + 34, x + 30, y + 8, INK, 2)          # spine
    line(x + 30, y + 8, x + 12, y + 14, INK, 1)          # upper edge
    line(x + 12, y + 14, x + 12, y + 34, INK, 1)         # lower edge
    line(x + 19, y + 25, x + 15, y + 17, INK, 1)         # barb
    line(x + 25, y + 17, x + 19, y + 14, INK, 1)         # barb
    line(x + 12, y + 34, x + 7, y + 39, INK, 2)          # nib
    disc(x + 6, y + 40, 2, CRIMSON)                      # ink drop


# --------------------------------------------------------------------------
# By-the-numbers strip (mini charts for the stat boxes)
# --------------------------------------------------------------------------

def sparkline(x, y, w, h, vals, c):
    """Polyline of `vals` across an (x, y, w, h) zone, dot on the last point."""
    n = len(vals)
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    prev = None
    last = None
    for i, v in enumerate(vals):
        sx = x + int(round(i * w / (n - 1)))
        sy = y + (h - 2) - int(round((v - lo) * (h - 4) / rng))
        if prev:
            line(prev[0], prev[1], sx, sy, c, 2)
        prev = (sx, sy)
        last = (sx, sy)
    disc(last[0], last[1], 2, c)


def minibars(x, y, w, h, vals, c, last_c=None):
    """Tiny bar chart; optionally crimson-highlight the final bar."""
    n = len(vals)
    step = w / n
    bw = max(3, int(step) - 3)
    peak = max(vals) or 1
    for i, v in enumerate(vals):
        bh = max(2, int(round(v * h / peak)))
        col = last_c if (last_c and i == n - 1) else c
        rect(x + int(round(i * step)), y + h - bh, bw, bh, col)


def viz_down(zx, zy, zw, zh):
    """Brent crude sliding through the week."""
    sparkline(zx, zy, zw - 8, zh, [64.8, 64.1, 64.6, 63.0, 61.9, 58.1], CRIMSON)


def viz_up(zx, zy, zw, zh):
    """Nikkei firming on the pact."""
    sparkline(zx, zy, zw - 8, zh, [50388, 50512, 50440, 50776, 50901, 51204], CRIMSON)


def viz_bars(zx, zy, zw, zh):
    """Daily Gaza aid trucks building to 120."""
    minibars(zx, zy, zw, zh, [40, 64, 88, 104, 120], INK, CRIMSON)


def viz_temp(zx, zy, zw, zh):
    """Record heat: thermometer pegged high beside a blazing sun."""
    tx = zx + 6
    rect(tx, zy, 5, 14, INK)                     # tube
    rect(tx + 1, zy + 3, 3, 14, CRIMSON)         # mercury
    disc(tx + 2, zy + 18, 6, INK)                # bulb shell
    disc(tx + 2, zy + 18, 4, CRIMSON)            # bulb fill
    for k in range(3):
        rect(tx + 7, zy + 2 + k * 5, 5, 1, INK)  # scale ticks
    sx, sy = zx + 40, zy + 8
    disc(sx, sy, 6, CRIMSON)                     # sun
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        line(sx + int(round(8 * math.cos(a))), sy + int(round(8 * math.sin(a))),
             sx + int(round(12 * math.cos(a))), sy + int(round(12 * math.sin(a))),
             INK, 1)


def viz_donut(zx, zy, zw, zh):
    """Storage gauge: ink donut with a crimson fill sweep from 12 o'clock."""
    cx, cy = zx + 15, zy + 10
    ring(cx, cy, 10, INK, 2)
    arc(cx, cy, 10, -math.pi / 2, -math.pi / 2 + 0.88 * 2 * math.pi, CRIMSON, 4)


def pico_cloudsun(x, y):
    """Sun peeking behind a puffy ink cloud (weather micro-panel)."""
    disc(x + 30, y + 6, 4, CRIMSON)                      # sun behind
    line(x + 35, y + 6, x + 38, y + 6, CRIMSON, 1)       # ray
    line(x + 30, y + 0, x + 30, y + 2, CRIMSON, 1)       # ray
    disc(x + 12, y + 10, 5, INK)                         # cloud puffs
    disc(x + 19, y + 7, 6, INK)
    disc(x + 26, y + 10, 5, INK)
    rect(x + 12, y + 10, 20, 5, INK)                     # cloud base


def stat_box(x, y, label, number, sub, viz):
    """One boxed figure: crimson label, 3x number, mini chart, blue source line."""
    outline_rect(x, y, 118, 110, INK, 1)
    draw_text(x + 6, y + 8, label, 1, CRIMSON)
    draw_text(x + 6, y + 26, number, 3, INK)
    viz(x + 6, y + 56, 106, 20)
    draw_text(x + 6, y + 92, sub, 1, BLUE)


def pico_hippo(x, y, c, bg):
    """Fiona the hippo, in silhouette, for the ticker strip."""
    rect(x + 2, y + 8, 26, 14, c)
    disc(x + 9, y + 15, 7, c)
    disc(x + 21, y + 15, 7, c)
    for lx in (x + 4, x + 11, x + 18, x + 24):
        rect(lx, y + 18, 5, 9, c)
    disc(x + 31, y + 12, 7, c)
    rect(x + 33, y + 8, 12, 10, c)
    disc(x + 44, y + 13, 5, c)
    rect(x + 27, y + 2, 4, 5, c)
    rect(x + 40, y + 10, 2, 2, bg)
    rect(x + 45, y + 10, 2, 2, bg)
    rect(x + 31, y + 6, 2, 2, bg)


def pico_fleuron(x, y):
    """Newspaper fleuron: crimson diamond between ink curls and dots."""
    cx, cy = x + 27, y + 7
    for i, wd in enumerate((2, 6, 10, 14, 10, 6, 2)):
        rect(cx - wd // 2, y + i * 2, wd, 2, CRIMSON)
    line(cx - 25, cy, cx - 10, cy, INK, 1)
    line(cx + 10, cy, cx + 25, cy, INK, 1)
    disc(cx - 27, cy, 1, INK)
    disc(cx + 27, cy, 1, INK)


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------

def card(x, y, kicker, head_lines, dek_lines, pico, page_tag):
    outline_rect(x, y, 320, 140, INK, 1)
    draw_text(x + 12, y + 10, kicker, 1, CRIMSON)
    rect(x + 12, y + 20, text_w(kicker, 1), 2, CRIMSON)
    pico(x + 12, y + 24)
    yy = y + 26
    for ln in head_lines:
        draw_text(x + 66, yy, ln, 2, INK)
        yy += 15
    for rx in range(x + 12, x + 308, 6):          # dotted hairline above dek
        rect(rx, y + 76, 3, 1, INK)
    yy = y + 82
    for ln in dek_lines:
        draw_text(x + 12, yy, ln, 1, BLUE)
        yy += 11
    draw_text(x + 308 - text_w(page_tag, 1), y + 122, page_tag, 1, BLUE)


def build():
    rect(0, 0, W, H, PAPER)

    # ---- Masthead -------------------------------------------------------
    rect(24, 14, 976, 1, INK)
    draw_text(24, 22, "VOL. LXXXII - NO. 324", 1, INK)
    right_text(1000, 22, "( PRICE: ONE IMAGE )", 1, INK)
    center_text(22, "INSIDE: GAZA P.4 * COP31 P.7 * ESSAY P.11", 1, INK)
    center_text(40, "THE WORLD DAILY", 7, INK)
    center_text(100, "FRIDAY, 20 NOVEMBER 2026", 3, CRIMSON)
    pico_fleuron(231, 103)
    pico_fleuron(735, 103)
    rect(24, 132, 976, 2, INK)
    rect(24, 137, 976, 1, INK)

    # ---- Lead story -----------------------------------------------------
    draw_text(24, 148, "LEAD STORY: FALL-OUT FROM THE SHENZHEN SUMMIT", 2, CRIMSON)
    draw_text(24, 170, "OIL PLUNGES AS SHENZHEN PACT DETAILS", 3, INK)
    draw_text(24, 192, "EMERGE; EU CALLS SUNDAY SUMMIT", 3, INK)
    draw_text(24, 224, "BRENT SINKS $4 TO $58.10 ON THE OIL CLAUSE; BRUSSELS SUMMONS", 2, INK)
    draw_text(24, 240, "LEADERS FOR SUNDAY; KYIV CALLS THE PACT 'A MAP FOR RUSSIA'.", 2, INK)
    draw_text(24, 266, "EU SUMMIT SUNDAY * ZELENSKY: 'WE WERE NOT IN THE ROOM' * SAUDI RAIDS LIFT CRUDE OFF THE LOWS", 1, BLUE)
    rect(854, 148, 2, 130, INK)
    pico_barrel(866, 148)
    rect(24, 290, 976, 2, INK)
    rect(24, 295, 976, 1, INK)

    # ---- Story cards (3 x 3) --------------------------------------------
    cards = [
        ("CONGRESS",
         ["HOUSE SUBPOENAS", "JPMORGAN OVER", "EPSTEIN FILES"],
         ["OVERSIGHT PANEL DEMANDS JPMORGAN AND", "DEUTSCHE RECORDS BY A DEC. 15 DEADLINE."],
         pico_folder, "FULL REPORT P.02"),
        ("BERLIN",
         ["GERMANY PLEDGES", "3BN EUROS MORE", "FOR UKRAINE"],
         ["MERZ WINS BUNDESTAG VOTE 368-244; MONEY", "COVERS AIR DEFENSE AND GRID REPAIRS."],
         pico_euro, "FULL REPORT P.03"),
        ("GAZA",
         ["CAIRO TALKS RACE TO", "SAVE GAZA CEASEFIRE"],
         ["MEDIATORS MAP TANK PULLBACK TO THE 'YELLOW", "LINE'; 120 TRUCKS ROLL VIA KEREM SHALOM."],
         pico_truck, "FULL REPORT P.04"),
        ("MIDEAST",
         ["SAUDI JETS HIT", "HOUTHI SITES AFTER", "RIYADH DRONE ATTACK"],
         ["DAWN RAIDS ON SANA'A AND HODEIDAH LAUNCH", "SITES; HOUTHI TV REPORTS 14 DEAD."],
         pico_jet, "FULL REPORT P.05"),
        ("ASIA-PACIFIC",
         ["JAPAN TIGHTENS", "RUSSIA CURBS AFTER", "PUTIN TALKS STALL"],
         ["DAY AFTER KREMLIN TALKS STALL, TOKYO FREEZES", "40 MORE RUSSIAN ENTITIES; KURIL TALKS ON ICE."],
         pico_torii, "FULL REPORT P.06"),
        ("CLIMATE",
         ["COP31 TALKS EXTEND", "OVER $40BN FUND GAP"],
         ["TUVALU LEADS WALKOUT THREAT OVER CASH;", "TURKEY CIRCULATES COMPROMISE TEXT FOR SUNDAY."],
         pico_globe, "FULL REPORT P.07"),
        ("SPORT",
         ["SINNER REACHES", "TURIN SEMIS;", "ALCARAZ WAITS"],
         ["DEFENDING CHAMP WINS 6-4, 7-6 SAVING TWO SET", "POINTS; ALCARAZ QUALIFIED UNDEFEATED THURSDAY."],
         pico_tennis, "FULL REPORT P.08"),
        ("SPACE",
         ["X6 FLARE SPOILS", "AIRLINE RADIO;", "AURORAS OVER ROME"],
         ["NIGHT X6 ERUPTION CUTS HF RADIO FOR 90 MINUTES;", "AURORAS SIGHTED IN ROME, BEIJING AND LEEDS."],
         pico_flare, "FULL REPORT P.09"),
        ("TECH",
         ["OPENAI DELAYS", "GPT-6 LAUNCH BY", "A MONTH"],
         ["SAFETY REVIEW AFTER INTERNAL EVALS; GOOGLE'S", "GEMINI 4 NOW TARGETS A DECEMBER 9 LAUNCH."],
         pico_chat, "FULL REPORT P.10"),
    ]
    xs = (24, 352, 680)
    ys = (306, 454, 602)
    for i, (k, hl, dl, p, pt) in enumerate(cards):
        card(xs[i % 3], ys[i // 3], k, hl, dl, p, pt)

    # ---- Tenth card + BY THE NUMBERS band -------------------------------
    card(24, 750, "OPINION",
         ["A PACT THAT LEAVES", "KYIV OUT IS NOT", "A PEACE DEAL"],
         ["THE SHENZHEN FOUR POINTS PRICE THE OIL,", "NOT THE PEOPLE. EUROPE SHOULD NOT CO-SIGN."],
         pico_quill, "ESSAY P.11")

    outline_rect(352, 750, 648, 166, INK, 1)
    draw_text(364, 762, "BY THE NUMBERS", 2, CRIMSON)
    rect(364, 780, text_w("BY THE NUMBERS", 2), 2, CRIMSON)
    stats = [
        (364, "BRENT CRUDE", "$58.10", "OFF $4 ON PACT", viz_down),
        (490, "NIKKEI 225", "51,204", "UP 1.2% ON PACT", viz_up),
        (616, "GAZA AID", "120", "VIA KEREM SHALOM", viz_bars),
        (742, "PERTH HEAT", "41.2C", "RECORD NOV NIGHT", viz_temp),
        (868, "EU GAS STORES", "88%", "FULL FOR WINTER", viz_donut),
    ]
    for bx, label, number, sub, viz in stats:
        stat_box(bx, 790, label, number, sub, viz)

    # ---- Weather micro-panel --------------------------------------------
    outline_rect(24, 896, 320, 20, INK, 1)
    pico_cloudsun(36, 898)
    draw_text(86, 903, "WEATHER", 1, CRIMSON)
    draw_text(138, 903, "ROME 18C * LONDON 7C * SYDNEY 41C", 1, INK)

    # ---- Footer ticker --------------------------------------------------
    rect(24, 924, 976, 2, INK)
    rect(24, 930, 976, 44, INK)
    pico_hippo(36, 937, PAPER, INK)
    draw_text(96, 948,
              "ANTHROPIC CLOSES $93.05 ON DAY TWO * DHAKA QUIET UNDER CURFEW "
              "* BOOKER WON BY LAGOS-BORN DEBUT * HALL OF FAME REVISITS ROSE BAN",
              1, PAPER)

    # ---- Folio ----------------------------------------------------------
    center_text(984, "PAGE 01 - THE WORLD DAILY - FRIDAY, 20 NOVEMBER 2026", 1, INK)
    rect(24, 998, 976, 2, INK)
    rect(24, 1003, 976, 1, INK)


# --------------------------------------------------------------------------
# PNG encoder (signature + IHDR + IDAT + IEND, CRC-32 per chunk)
# --------------------------------------------------------------------------

def write_png(path, w, h, buf):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    stride = w * 3
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0 (None)
        raw += buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    build()
    out = os.environ.get("OUT") or "/output/entry.png"
    if os.path.isdir(out):                     # OUT may name a directory...
        out = os.path.join(out, "entry.png")   # ...then write entry.png inside
    d = os.path.dirname(out)
    if d:
        os.makedirs(d, exist_ok=True)
    n = write_png(out, W, H, _buf)
    print("wrote %s (%d bytes, %dx%d)" % (out, n, W, H))


if __name__ == "__main__":
    main()
