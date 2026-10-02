# Cavansite Coil

Full-colour Python 3 neon disc-launcher arcade for ElbowOS.

Aim a copper coil and arc cyan, gold, and rose discs into matching crystal sockets that drift in a vertical shaft. Walls bounce. A floor miss breaks the combo. Original rules and art — not a ROM and not an emulator.

## Play

```bash
pip install -r requirements.txt
python3 cavansite_coil.py --play
```

A / D or arrow keys aim. Hold Space to charge, release to launch. R restarts.

## Record a 9:16 reel

```bash
python3 cavansite_coil.py --record
```

Headless autoplay writes a 15 second 1080x1920 H.264 MP4 (libx264, yuv420p, CRF 20, +faststart).

* Featured account: https://x.com/ElbowOS
* Drive reel: https://drive.google.com/file/d/1n5gu5BkGz1ngaHJ4mFhqyFdP2J5kRtq-/view
