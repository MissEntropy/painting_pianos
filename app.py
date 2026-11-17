"""Build the web app (index.html): the chart on a vivid page, with keys you can tap to hear.

    python3 app.py       # writes index.html next to this file (served by GitHub Pages)

The chart itself comes from build.py, so any change there shows up here too.
"""
from pathlib import Path

import build as chart

SITE_CSS = """
  /* The chart stays paper-white; the colour lives around it */
  body {
    min-height: 100%; box-sizing: border-box; padding-block: 0 48px;
    background: #fff; overflow-x: hidden;
    font-family: "Heebo", Arial, sans-serif;
  }

  .hero { max-width: 1080px; margin: 0 auto; padding: 48px 0 24px; text-align: center; }
  .hero h1 {
    margin: 0; font-family: "Homemade Apple", cursive; font-weight: 400;
    font-size: clamp(34px, 7vw, 68px); line-height: 1.5;
    background: linear-gradient(90deg, #E2603F, #C04FB0 40%, #3F7FD9 70%, #3E9B52);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero p { margin: 4px 0 0; font-size: clamp(15px, 2vw, 19px); color: #4A4668; }
  .hero p[lang="he"] { font-weight: 700; }
  .actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin-top: 20px; }
  .actions a, .actions button {
    font: 700 15px "Heebo", Arial, sans-serif; color: #fff; text-decoration: none; cursor: pointer;
    border: 0; border-radius: 999px; padding: 10px 22px;
    background: linear-gradient(135deg, #E2603F, #C04FB0); box-shadow: 0 6px 18px rgb(192 79 176 / .3);
    transition: transform .15s ease, box-shadow .15s ease;
  }
  .actions a:nth-child(2) { background: linear-gradient(135deg, #3F7FD9, #3E9B52); box-shadow: 0 6px 18px rgb(63 127 217 / .3); }
  .actions a:hover, .actions button:hover { transform: translateY(-2px); }

  .paper {
    max-width: 1140px; margin: 16px auto 0; padding: 8px clamp(4px, 2vw, 28px) 0;
    background: #fff;
  }
  .paper .frame { margin-block: 24px; }
  /* On phones the chart keeps its proportions and scrolls sideways instead of squashing */
  .scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .scroll > .inner { min-width: 760px; padding: 0 4px; }
  .hint { display: none; text-align: center; font-size: 13px; color: #6B6889; margin: 12px 0 0; }
  @media (max-width: 780px) { .hint { display: block; } }

  /* Tap to play */
  .piano rect { cursor: pointer; transition: fill .25s ease; }
  .piano rect.lit { fill: var(--acc-edge); transition: none; }
  .note .head { transition: fill .25s ease, transform .25s ease; transform-box: fill-box; transform-origin: center; }
  .note.lit .head { fill: var(--acc-edge); transform: scale(1.25); transition: none; }

  @media print {
    .hero { display: none; }
    body { background: #fff; padding: 0; }
    .paper { box-shadow: none; border-radius: 0; padding: 0; max-width: none; }
  }
"""

SITE_JS = """
(() => {
  const STEPS = [0, 2, 4, 5, 7, 9, 11], BLACK_AFTER = %(black_after)s, OCTAVES = %(octaves)d;
  let ctx;
  function play(midi) {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    const t = ctx.currentTime, freq = 440 * 2 ** ((midi - 69) / 12);
    const out = ctx.createGain();
    out.gain.setValueAtTime(0.0001, t);
    out.gain.exponentialRampToValueAtTime(0.35, t + 0.01);
    out.gain.exponentialRampToValueAtTime(0.0001, t + 1.8);
    out.connect(ctx.destination);
    [[1, 'triangle', 1], [2, 'sine', 0.35], [3, 'sine', 0.12]].forEach(([mult, type, level]) => {
      const osc = ctx.createOscillator(), g = ctx.createGain();
      osc.type = type; osc.frequency.value = freq * mult; g.gain.value = level;
      osc.connect(g).connect(out); osc.start(t); osc.stop(t + 1.9);
    });
  }
  function flash(el) {
    if (!el) return;
    el.classList.add('lit');
    clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove('lit'), 350);
  }
  document.querySelectorAll('.frame').forEach((frame, f) => {
    const base = 12 * ((f === 0 ? %(treble_oct)d : %(bass_oct)d) + 1);
    const notes = frame.querySelectorAll('.note');
    frame.querySelectorAll('.whites rect').forEach((key, i) => {
      const midi = base + 12 * Math.floor(i / 7) + STEPS[i %% 7];
      key.addEventListener('pointerdown', () => { play(midi); flash(key); flash(notes[i]); });
    });
    frame.querySelectorAll('.blacks rect').forEach((key, j) => {
      const o = Math.floor(j / BLACK_AFTER.length), w = BLACK_AFTER[j %% BLACK_AFTER.length];
      const midi = base + 12 * o + STEPS[w] + 1;
      key.addEventListener('pointerdown', () => { play(midi); flash(key); });
    });
    notes.forEach((note, i) => note.addEventListener('pointerdown', () =>
      frame.querySelectorAll('.whites rect')[i].dispatchEvent(new Event('pointerdown'))));
  });
  document.getElementById('print').addEventListener('click', () => window.print());
})();
"""


def site():
    js = SITE_JS % dict(black_after=chart.BLACK_AFTER, octaves=chart.OCTAVES,
                        treble_oct=chart.FRAMES[0]["octave"], bass_oct=chart.FRAMES[1]["octave"])
    frames = "\n\n".join(chart.frame_html(fr) for fr in chart.FRAMES)
    return "\n".join([
        '<!doctype html>', '<html lang="en" data-theme="light">', '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="description" content="A printable piano chart: treble and bass clefs, Hebrew note names and finger numbers.">',
        chart.HEAD,
        "<style>" + chart.CSS + SITE_CSS + "</style>",
        '<header class="hero">',
        '  <h1>Painting Pianos</h1>',
        '  <p>Tap any key or note to hear it</p>',
        '  <p lang="he" dir="rtl">לחצו על קליד או תו כדי לשמוע אותו</p>',
        '  <div class="actions"><button id="print" type="button">Print</button>'
        '<a href="painting_pianos.png" download>Download image</a></div>',
        '</header>',
        '<div class="paper">', '<p class="hint">← swipe to see the whole keyboard →</p>',
        '<div class="scroll"><div class="inner">', frames, '', chart.signature(), '</div></div></div>',
        f"<script>{js}</script>", ""])


if __name__ == "__main__":
    out = Path(__file__).with_name("index.html")
    out.write_text(site(), encoding="utf-8")
    print(f"wrote {out}")
