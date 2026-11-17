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
    font: 500 15px "Heebo", Arial, sans-serif; color: #1D1A3A; text-decoration: none; cursor: pointer;
    background: #fff; border: 1.5px solid #1D1A3A; border-radius: 4px; padding: 6px 18px;
    transition: background .15s ease, color .15s ease;
  }
  .actions a:hover, .actions button:hover { background: #1D1A3A; color: #fff; }

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
  .note { cursor: pointer; }
  .note .head { transition: fill .25s ease, transform .25s ease; transform-box: fill-box; transform-origin: center; }
  .note.lit .head { fill: var(--acc-edge); transform: scale(1.25); transition: none; }

  /* Printing: one page, always. The page prints the exported image (same chart, light theme),
     sized to fit the paper, instead of the live layout that would spill onto a second page. */
  .print-only { display: none; }
  @page { margin: 10mm; }
  @media print {
    .hero, .paper { display: none; }
    body { background: #fff; padding: 0; }
    .print-only { display: block; width: auto; height: auto; max-width: 100%; max-height: 100vh; margin: 0 auto; }
  }
"""

SITE_JS = """
(() => {
  const STEPS = [0, 2, 4, 5, 7, 9, 11], BLACK_AFTER = %(black_after)s, OCTAVES = %(octaves)d;
  // Real grand piano recordings (Salamander Grand Piano, CC-BY 3.0), one every 3 semitones;
  // the notes in between are the nearest recording, re-pitched.
  const SAMPLES = { 33: 'A1', 36: 'C2', 39: 'Ds2', 42: 'Fs2', 45: 'A2', 48: 'C3', 51: 'Ds3', 54: 'Fs3',
                    57: 'A3', 60: 'C4', 63: 'Ds4', 66: 'Fs4', 69: 'A4', 72: 'C5', 75: 'Ds5', 78: 'Fs5', 81: 'A5', 84: 'C6' };
  const raw = {}, buffers = {};
  for (const [m, name] of Object.entries(SAMPLES))
    raw[m] = fetch(`samples/${name}.mp3`).then(r => r.arrayBuffer());
  let ctx;
  function buffer(m) {
    return buffers[m] = buffers[m] || raw[m].then(b => ctx.decodeAudioData(b.slice(0)));
  }
  async function play(midi) {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === 'suspended') ctx.resume();
    const near = Object.keys(SAMPLES).map(Number).reduce((a, b) => Math.abs(b - midi) < Math.abs(a - midi) ? b : a);
    const src = ctx.createBufferSource(), gain = ctx.createGain();
    src.buffer = await buffer(near);
    src.playbackRate.value = 2 ** ((midi - near) / 12);
    gain.gain.value = 0.8;
    src.connect(gain).connect(ctx.destination);
    const t = ctx.currentTime;
    src.start(t);
    let released = false;
    // Like lifting a finger off the key: the sound dies away when you let go (it rings a moment first).
    return () => {
      if (released) return; released = true;
      const at = Math.max(ctx.currentTime, t + 0.9);
      gain.gain.setValueAtTime(0.8, at);
      gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.5);
      src.stop(at + 0.55);
    };
  }
  function press(el, midi, extra) {
    el.addEventListener('pointerdown', e => {
      const stop = play(midi);
      flash(el); if (extra) flash(extra);
      const up = () => { stop.then(f => f()); el.removeEventListener('pointerup', up); el.removeEventListener('pointerleave', up); };
      el.addEventListener('pointerup', up); el.addEventListener('pointerleave', up);
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
      press(key, midi, notes[i]);
      press(notes[i], midi, key);
    });
    frame.querySelectorAll('.blacks rect').forEach((key, j) => {
      const o = Math.floor(j / BLACK_AFTER.length), w = BLACK_AFTER[j %% BLACK_AFTER.length];
      const midi = base + 12 * o + STEPS[w] + 1;
      press(key, midi);
    });
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
        '  <p lang="he" dir="rtl">לחצו על קליד או תו כדי לשמוע אותו</p>',
        '  <div class="actions"><button id="print" type="button">הדפסה</button>'
        '<a href="painting_pianos.png" download>הורדת תמונה</a></div>',
        '</header>',
        '<div class="paper">', '<p class="hint" lang="he" dir="rtl">החליקו הצידה כדי לראות את כל המקלדת</p>',
        '<div class="scroll"><div class="inner">', frames, '', chart.signature(), '</div></div></div>',
        '<img class="print-only" src="painting_pianos.png" alt="">',
        f"<script>{js}</script>", ""])


if __name__ == "__main__":
    out = Path(__file__).with_name("index.html")
    out.write_text(site(), encoding="utf-8")
    print(f"wrote {out}")
