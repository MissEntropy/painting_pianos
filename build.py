#!/usr/bin/env python3
"""Painting Pianos: builds painting_pianos.html (treble + bass piano charts).

    python3 build.py              -> painting_pianos.html, a standalone page you can open in a browser
    python3 build.py --artifact   -> same page without <!doctype>/<meta charset> (the artifact host adds those)

No dependencies. Fonts (Heebo, Noto Music) load from Google Fonts, so open it online.

Each frame is: title box / staff with a whole note above each white key / Hebrew note names /
two-octave keyboard / finger numbers, all sitting in alternating grey columns, one per white key.
"""
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------- what's on the page
FRAMES = [
    dict(
        css_class="",             # green accents
        title="מפתח סול (יד ימין)",
        clef="treble",
        octave=4,                 # keys run C4..B5
        fingers=[1, 2, 3, 1, 2, 3, 4] * 2,           # RH C major scale, thumb under on C and F
        fingers_note="Right-hand fingering for the C major scale: thumb (1) on C and F",
    ),
    dict(
        css_class="bass",         # blue accents
        title="מפתח פה (יד שמאל)",
        clef="bass",
        octave=2,                 # keys run C2..B3
        fingers=[5, 4, 3, 2, 1, 3, 2, 1, 4, 3, 2, 1, 3, 2],  # LH C major scale, thumb on G and C
        fingers_note="Left-hand fingering for the C major scale: thumb (1) on G and C",
    ),
]
FINGER_LABEL = "מספר אצבע"
HEBREW_NAMES = ["דו", "רה", "מי", "פה", "סול", "לה", "סי"]
LETTERS = "CDEFGAB"
OCTAVES = 2
N_WHITE = 7 * OCTAVES

# ---------------------------------------------------------------- keyboard geometry (piano SVG units)
KEY_W, WHITE_H = 40, 154
BLACK_W, BLACK_H = 24, 96          # black keys are ~5/8 the white key's length, like a real piano
BLACK_AFTER = [0, 1, 3, 4, 5]      # a black key follows C, D, F, G, A in each octave

# ---------------------------------------------------------------- staff geometry (staff SVG units)
SPACE = 12 * 2                     # distance between staff lines
LINES_Y = [22 + SPACE * i for i in range(5)]   # top line .. bottom line
BOTTOM = LINES_Y[-1]
SCALE = 904 * 0.86667 / 604        # staff units per piano unit (keeps the size we tuned by eye)
KEY0 = 60.86                       # staff x where the first key starts
STAFF_LEFT = -40                   # staff lines start here; clef lives between here and KEY0
KEY_STAFF_W = KEY_W * SCALE
KEYS_CENTRE = KEY0 + N_WHITE * KEY_STAFF_W / 2
STAFF_RIGHT = round(2 * KEYS_CENTRE - STAFF_LEFT)   # same overhang both sides -> piano centred

CLEFS = {
    # bottom_step: diatonic step of the bottom line (letter index + 7*octave): E4 = 30, G2 = 18
    # Noto Music glyphs: 250 font units per staff space, so 96px gives 24-unit spaces.
    "treble": dict(glyph="\U0001D11E", bottom_step=30, size=96, x=-33, y=118, cls="clef",
                   viewbox_y=(-44, 210), name="Treble"),
    # The bass clef is drawn a bit small in this font: 100px, baseline raised so the dots
    # straddle the F line and the top just meets the top line (checked against a screenshot).
    "bass": dict(glyph="\U0001D122", bottom_step=18, size=100, x=-35, y=110.7, cls="clef bass-clef",
                 viewbox_y=(-14, 200), name="Bass"),
}

# ---------------------------------------------------------------- layout percentages (shared by both frames)
VB_X0 = STAFF_LEFT - 2
VB_W = (STAFF_RIGHT + 2) - VB_X0
pct = lambda u: f"{u / VB_W * 100:.3f}%"
PIANO_W = pct(564 * SCALE)                       # piano viewBox is 564 wide (-2 .. 562)
PIANO_LEFT = pct(KEY0 - 2 * SCALE - VB_X0)
BANDS_LEFT = pct(KEY0 - VB_X0)
BANDS_W = pct(N_WHITE * KEY_STAFF_W)
COL = f"{100 / N_WHITE:.6f}%"
COL2 = f"{200 / N_WHITE:.6f}%"

f = lambda v: f"{round(v, 2):g}"


def whole_note(x, y):
    """Whole note = outer oval minus a tilted inner oval (evenodd), so staff lines show through."""
    a = math.radians(-50)
    dx, dy = round(7 * math.cos(a), 2), round(7 * math.sin(a), 2)
    return (f"M{f(x-12)} {f(y)}A12 9.5 0 1 0 {f(x+12)} {f(y)}A12 9.5 0 1 0 {f(x-12)} {f(y)}Z"
            f"M{f(x-dx)} {f(y-dy)}A7 4 -50 1 0 {f(x+dx)} {f(y+dy)}A7 4 -50 1 0 {f(x-dx)} {f(y-dy)}Z")


def staff_svg(frame):
    c = CLEFS[frame["clef"]]
    lo, hi = frame["octave"], frame["octave"] + OCTAVES - 1
    y_of = lambda step: BOTTOM - (step - c["bottom_step"]) * SPACE / 2
    out = [f'  <!-- {c["name"]} staff: one whole note above each white key, C{lo} to B{hi} -->',
           f'  <svg class="staff" viewBox="{VB_X0} {c["viewbox_y"][0]} {VB_W} {c["viewbox_y"][1]}" role="img" '
           f'aria-label="{c["name"]} staff with a whole note for every white key, C{lo} to B{hi}">']
    for y in LINES_Y:
        out.append(f'    <line x1="{STAFF_LEFT}" y1="{y}" x2="{STAFF_RIGHT}" y2="{y}"/>')
    for x in (STAFF_LEFT, STAFF_RIGHT):
        out.append(f'    <line x1="{x}" y1="{LINES_Y[0]}" x2="{x}" y2="{BOTTOM}"/>')
    out.append(f'  <text class="{c["cls"]}" x="{c["x"]}" y="{c["y"]}">{c["glyph"]}</text>')
    out.append('  <g class="notes">')
    for i in range(N_WHITE):
        letter, octv = i % 7, frame["octave"] + i // 7
        step = letter + 7 * octv
        x = round(KEY0 + (i + 0.5) * KEY_STAFF_W, 1)
        y = y_of(step)
        ledgers = [s for s in range(c["bottom_step"] - 2, step - 1, -2)]            # below the staff
        ledgers += [s for s in range(c["bottom_step"] + 10, step + 1, 2)]          # above the staff
        out.append(f'    <g class="note" data-note="{LETTERS[letter]}{octv}">')
        for s in ledgers:
            ly = y_of(s)
            out.append(f'      <line class="ledger" x1="{f(x-17)}" y1="{f(ly)}" x2="{f(x+17)}" y2="{f(ly)}"/>')
        out.append(f'      <path class="head" d="{whole_note(x, y)}"/>')
        out.append('    </g>')
    out += ['  </g>', '  </svg>']
    return "\n".join(out)


def names_list():
    items = "\n".join(f'    <li lang="he" dir="rtl">{HEBREW_NAMES[i % 7]}</li>' for i in range(N_WHITE))
    return ('  <!-- Note names in Hebrew: Do Re Mi Fa Sol La Si -->\n'
            f'  <ol class="names" aria-label="Note names in Hebrew">\n{items}\n  </ol>')


def piano_svg(frame):
    lo, hi = frame["octave"], frame["octave"] + OCTAVES - 1
    whites = "\n".join(
        f'      <rect class="white{" alt" if i % 2 else ""}" x="{i * KEY_W}" y="0" width="{KEY_W}" '
        f'height="{WHITE_H}" rx="3"/>' for i in range(N_WHITE))
    blacks = "\n".join(
        f'      <rect class="black" x="{(o * 7 + w + 1) * KEY_W - BLACK_W // 2}" y="0" width="{BLACK_W}" '
        f'height="{BLACK_H}" rx="2"/>' for o in range(OCTAVES) for w in BLACK_AFTER)
    return (f'  <!-- Two octaves, C{lo} to B{hi}: {N_WHITE} white keys, {5 * OCTAVES} black keys -->\n'
            f'  <svg class="piano" viewBox="-2 -2 {N_WHITE * KEY_W + 4} {WHITE_H + 6}" role="img" '
            f'aria-label="Piano keyboard from C{lo} to B{hi}">\n'
            f'    <g class="whites">\n{whites}\n    </g>\n    <g class="blacks">\n{blacks}\n    </g>\n  </svg>')


def fingers_list(frame):
    assert len(frame["fingers"]) == N_WHITE, "one finger number per white key"
    items = "\n".join(f"    <li>{n}</li>" for n in frame["fingers"])
    return (f'  <!-- {frame["fingers_note"]} -->\n'
            f'  <ol class="fingers" lang="he" data-label="{FINGER_LABEL}" aria-label="{FINGER_LABEL}">\n'
            f'{items}\n  </ol>')


def frame_html(frame):
    cls = f'frame {frame["css_class"]}'.strip()
    return "\n".join([
        f'<div class="{cls}">',
        f'<h1 class="title" lang="he" dir="rtl">{frame["title"]}</h1>',
        '<main class="canvas">',
        '  <div class="bands" aria-hidden="true"></div>',
        staff_svg(frame), '', names_list(), '', piano_svg(frame), '', fingers_list(frame),
        '</main>', '</div>'])


CSS = f"""
  :root {{ --bg: #FFFFFF; --fg: #1D1A3A; --key-white: #FFFFFF; --key-black: #1D1A3A; --key-edge: #1D1A3A; --title-bg: #DCF2D4; --title-edge: #7CBF6E; --title-fg: #1F4A24; --blue-bg: #D8E7FA; --blue-edge: #6F9FDA; --blue-fg: #1B3A63; --band-a: #F5F6F9; --band-b: #E8E9F0; --key-white-alt: #EDEEF3; --sign: #D97757; --muted: #6B6889; }}
  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #12111F; --fg: #EEECFA; --key-white: #F4F3FA; --key-black: #0A0914; --key-edge: #0A0914; --title-bg: #22392A; --title-edge: #5E9F5A; --title-fg: #D4F1CC; --blue-bg: #1D2C44; --blue-edge: #5A8BD0; --blue-fg: #D3E3FA; --band-a: #1C1B2D; --band-b: #28273D; --key-white-alt: #CFCDDF; --sign: #E08A6D; --muted: #9C99BC; color-scheme: dark }} }}
  :root[data-theme="dark"] {{ --bg: #12111F; --fg: #EEECFA; --key-white: #F4F3FA; --key-black: #0A0914; --key-edge: #0A0914; --title-bg: #22392A; --title-edge: #5E9F5A; --title-fg: #D4F1CC; --blue-bg: #1D2C44; --blue-edge: #5A8BD0; --blue-fg: #D3E3FA; --band-a: #1C1B2D; --band-b: #28273D; --key-white-alt: #CFCDDF; --sign: #E08A6D; --muted: #9C99BC; color-scheme: dark }}
  html, body {{ height: 100%; }}
  body {{
    margin: 0; background: var(--bg); color: var(--fg);
    padding-left: max(16px, env(safe-area-inset-left, 0px));
    padding-right: max(16px, env(safe-area-inset-right, 0px));
  }}
  /* Frame around each chart; side padding lives here so the % layout inside stays exact */
  .frame {{
    max-width: 1080px; margin: 32px auto;
    border: 1.5px solid var(--acc-edge); border-radius: 6px;
    padding-inline: clamp(12px, 3vw, 32px);
    --acc-bg: var(--title-bg); --acc-edge: var(--title-edge); --acc-fg: var(--title-fg);
  }}
  .frame.bass {{ --acc-bg: var(--blue-bg); --acc-edge: var(--blue-edge); --acc-fg: var(--blue-fg); }}
  .title {{
    width: fit-content; max-width: 100%; box-sizing: border-box;
    margin: 28px auto 0; padding: 8px 24px; text-align: center; text-wrap: balance;
    background: var(--acc-bg); border: 2px solid var(--acc-edge); border-radius: 12px;
    font-family: "Heebo", "Arial Hebrew", "Noto Sans Hebrew", Arial, sans-serif; font-weight: 700;
    font-size: clamp(17px, 2.2vw, 24px); line-height: 1.2; color: var(--acc-fg);
  }}
  .canvas {{ padding-block: 48px; display: flex; flex-direction: column; align-items: center; gap: 20px; max-width: 1080px; margin-inline: auto; position: relative; }}
  /* One grey column per white key, from the top of the staff down to the finger numbers */
  .bands {{
    position: absolute; top: 48px; bottom: 48px; left: {BANDS_LEFT}; width: {BANDS_W};
    background: repeating-linear-gradient(90deg, var(--band-a) 0 {COL}, var(--band-b) {COL} {COL2});
  }}
  .staff, .piano, .names, .fingers {{ position: relative; }}
  .names, .fingers {{
    align-self: flex-start; width: {BANDS_W}; margin: 0 0 0 {BANDS_LEFT}; padding: 0; list-style: none;
    display: grid; grid-template-columns: repeat({N_WHITE}, 1fr);
    font-family: "Heebo", "Arial Hebrew", "Noto Sans Hebrew", Arial, sans-serif;
    font-size: clamp(13px, 2vw, 22px); line-height: 1.6; text-align: center; color: var(--fg);
  }}
  .names {{ font-weight: 500; }}
  .fingers {{ font-weight: 700; font-variant-numeric: tabular-nums; }}
  /* Label box in the left margin, beside the finger numbers */
  .fingers::before {{
    content: attr(data-label);
    position: absolute; right: 100%; top: 50%; transform: translateY(-50%);
    margin-right: 8px; padding: 2px 10px; white-space: nowrap; direction: rtl;
    background: var(--acc-bg); border: 2px solid var(--acc-edge); border-radius: 8px;
    font-weight: 700; font-size: clamp(11px, 1.6vw, 17px); line-height: 1.4; color: var(--acc-fg);
  }}
  .piano, .staff {{ height: auto; display: block; }}
  .staff {{ width: 100%; }}
  .piano {{ width: {PIANO_W}; align-self: flex-start; margin-left: {PIANO_LEFT}; }}
  .staff line {{ stroke: var(--fg); stroke-width: 2; stroke-linecap: round; }}
  .staff .head {{ fill: var(--fg); fill-rule: evenodd; }}
  .staff .clef {{ fill: var(--fg); font-size: {CLEFS["treble"]["size"]}px; font-family: "Noto Music", serif; }}
  .staff .bass-clef {{ font-size: {CLEFS["bass"]["size"]}px; }}
  .white {{ fill: var(--key-white); stroke: var(--key-edge); stroke-width: 2; }}
  .white.alt {{ fill: var(--key-white-alt); }}
  .black {{ fill: var(--key-black); stroke: var(--key-edge); stroke-width: 2; }}
  /* Signature, bottom right: handwritten name + hand-drawn spark */
  .signature {{
    max-width: 1080px; margin: -12px auto 0; padding: 0 12px 32px 0; box-sizing: border-box;
    display: flex; justify-content: flex-end; align-items: center; gap: 6px;
    font-family: "Homemade Apple", "Segoe Script", "Brush Script MT", cursive; font-size: 22px; line-height: 1.6;
    color: var(--muted);
  }}
  /* A real signature is never perfectly level */
  .signature span {{ display: inline-block; transform: rotate(-3deg); }}
  .signature svg {{ width: 34px; height: 34px; transform: translateY(-8px) rotate(-8deg); }}
  .signature path {{ fill: none; stroke: var(--sign); stroke-linecap: round; }}
"""

HEAD = """<title>Painting Pianos</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Homemade+Apple&family=Heebo:wght@500;700&family=Noto+Music&display=swap">
"""


def signature(seed=9, n_rays=11):
    """Artist signature: the name in handwriting + a hand-drawn spark.

    The spark is n_rays strokes around one centre, each with a random wobble in angle, length,
    start point, bend and thickness, so it looks drawn rather than a symmetric snowflake.
    A fixed seed keeps every build identical; change it to get a different (still hand-made) spark.
    """
    import random
    rnd = random.Random(seed)
    base = rnd.uniform(0, 360)
    strokes = []
    for i in range(n_rays):
        a = math.radians(base + i * 360 / n_rays + rnd.uniform(-13, 13))
        length, start = rnd.uniform(6.5, 13.5), rnd.uniform(0.3, 2.6)
        ux, uy = math.cos(a), math.sin(a)
        cx, cy = 15 + rnd.uniform(-.8, .8), 15 + rnd.uniform(-.8, .8)   # rays don't all meet at one point
        x1, y1 = cx + start * ux, cy + start * uy
        x2, y2 = cx + length * ux, cy + length * uy
        bend = rnd.uniform(-1.3, 1.3)
        mx, my = (x1 + x2) / 2 - bend * uy, (y1 + y2) / 2 + bend * ux
        width = rnd.uniform(1.6, 2.6) * 0.75
        strokes.append(f'<path d="M{x1:.1f} {y1:.1f}Q{mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}" stroke-width="{width:.2f}"/>')
    return (f'<footer class="signature"><span>with love, Claude</span>'
            f'<svg viewBox="0 0 30 30" aria-hidden="true">{"".join(strokes)}</svg></footer>')


def build(artifact=False):
    page = HEAD + "<style>" + CSS + "</style>\n\n" + "\n\n".join(frame_html(fr) for fr in FRAMES) + "\n\n" + signature() + "\n"
    if not artifact:
        page = '<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + page
    return page


def export_png(html_path, png_path, width=1200, scale=2):
    """Screenshot the page with headless Chrome (light theme, 2x for sharp print), then trim to the frames."""
    import shutil, subprocess, tempfile
    from PIL import Image, ImageChops  # Pillow
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
    if not chrome:
        sys.exit("--png needs Google Chrome or Chromium installed")
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.png"
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--blink-settings=preferredColorScheme=1",  # light theme
                        f"--force-device-scale-factor={scale}", f"--window-size={width},2400",
                        "--virtual-time-budget=8000",               # let the web fonts load
                        f"--screenshot={raw}", html_path.resolve().as_uri()],
                       check=True, capture_output=True)
        im = Image.open(raw).convert("RGB")
    bg = Image.new("RGB", im.size, im.getpixel((2, 2)))
    l, t, r, b = ImageChops.difference(im, bg).getbbox()
    pad = 24 * scale
    im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height))).save(png_path)
    print(f"wrote {png_path}")


if __name__ == "__main__":
    out = Path(__file__).with_name("painting_pianos.html")
    out.write_text(build(artifact="--artifact" in sys.argv), encoding="utf-8")
    print(f"wrote {out}")
    if "--png" in sys.argv:
        if "--artifact" in sys.argv:
            sys.exit("--png works on the standalone page; run it without --artifact")
        export_png(out, out.with_suffix(".png"))
