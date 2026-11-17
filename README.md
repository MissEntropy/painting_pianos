# Painting Pianos 🎹

A printable piano chart: the treble clef for the right hand (green) and the bass clef for the left hand (blue), each showing the notes, the Hebrew note names, the keys and the finger numbers.

**Live app:** https://missentropy.github.io/painting_pianos/ (tap any key or note to hear it)

![chart](painting_pianos.png)

## Build

```bash
python3 build.py            # writes painting_pianos.html
python3 build.py --png      # also exports painting_pianos.png (needs Chrome + Pillow)
python3 build.py --artifact # artifact version (no doctype/meta)
python3 app.py              # writes index.html, the web app GitHub Pages serves
```

All settings (fingering, note names, colours, geometry) live at the top of `build.py`.

## Credits

Piano sound: [Salamander Grand Piano](https://archive.org/details/SalamanderGrandPianoV3) by Alexander Holm, CC-BY 3.0 (the mp3 set in `samples/`, as published by Tone.js).
