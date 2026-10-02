#!/usr/bin/env python3
"""Cavansite Coil — neon disc-launcher arcade for ElbowOS. Python 3 + pygame.

Aim a copper coil, charge, and arc colored discs into matching crystal sockets.
Not a ROM, not an emulator, original rules and art.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/CAVANSITE_COIL_ElbowOS.mp4")
NAVY, TEAL, INK = (7, 22, 32), (14, 56, 66), (4, 10, 16)
CYAN, GOLD, ROSE = (62, 224, 255), (255, 209, 90), (255, 79, 180)
COPPER, LIME, WHITE = (255, 138, 61), (182, 255, 74), (236, 248, 255)
COLS = [CYAN, GOLD, ROSE]


class Game:
    def __init__(self, seed=7):
        random.seed(seed)
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not RECORD else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption("Cavansite Coil")
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.tiny = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.reset()

    def reset(self):
        self.t = 0.0
        self.score = 0
        self.combo = 0
        self.angle = 0.0
        self.charge = 0.0
        self.charging = False
        self.discs = []
        self.parts = []
        self.sockets = []
        for i in range(4):
            self.sockets.append(self._sock(i % 3, 220 + i * 190))
        self.veins = [(random.randint(40, 160), random.random()) for _ in range(8)]
        self.veins += [(random.randint(W - 160, W - 40), random.random()) for _ in range(8)]
        self.flash = 0.0

    def _sock(self, ci, x):
        return {
            "x": float(x), "y": float(random.randint(340, 860)),
            "ci": ci, "vx": random.choice([-1, 1]) * random.uniform(70, 140),
            "ph": random.random() * 6.2, "r": 58,
        }

    def launch(self, power):
        if len(self.discs) >= 3:
            return
        sp = 980 + power * 1280
        ang = -math.pi / 2 + self.angle
        ci = random.randrange(3)
        self.discs.append({
            "x": W / 2 + math.cos(ang) * 70, "y": H - 250 + math.sin(ang) * 40,
            "vx": math.cos(ang) * sp, "vy": math.sin(ang) * sp, "ci": ci, "r": 26,
        })
        self.charge = 0.0
        self.charging = False

    def step(self, dt, aim, fire):
        self.t += dt
        self.angle = max(-1.05, min(1.05, self.angle + aim * 2.4 * dt))
        if fire:
            self.charging = True
            self.charge = min(1.0, self.charge + dt * 1.7)
        elif self.charging:
            self.launch(self.charge)
        self.flash = max(0.0, self.flash - dt)
        for s in self.sockets:
            s["x"] += s["vx"] * dt
            s["y"] += math.sin(self.t * 1.4 + s["ph"]) * 18 * dt
            if s["x"] < 150 or s["x"] > W - 150:
                s["vx"] *= -1
            s["x"] = max(140, min(W - 140, s["x"]))
            s["y"] = max(300, min(980, s["y"]))
        alive = []
        for d in self.discs:
            d["vy"] += 920 * dt
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            if d["x"] < 70 or d["x"] > W - 70:
                d["vx"] *= -0.86
                d["x"] = max(70, min(W - 70, d["x"]))
            hit = False
            for s in self.sockets:
                if s["ci"] != d["ci"]:
                    continue
                if (d["x"] - s["x"]) ** 2 + (d["y"] - s["y"]) ** 2 < (s["r"] + d["r"] - 8) ** 2:
                    self.combo += 1
                    self.score += 100 + self.combo * 35
                    self.flash = 0.18
                    self._burst(s["x"], s["y"], COLS[s["ci"]])
                    s["x"] = random.randint(180, W - 180)
                    s["y"] = random.randint(340, 900)
                    s["vx"] = random.choice([-1, 1]) * random.uniform(80, 150)
                    hit = True
                    break
            if hit or d["y"] > H - 140:
                if not hit:
                    self.combo = 0
                continue
            alive.append(d)
        self.discs = alive
        self.parts = [p for p in self.parts if p["life"] > 0]
        for p in self.parts:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt

    def _burst(self, x, y, col):
        for _ in range(16):
            a = random.random() * math.tau
            sp = random.uniform(80, 420)
            self.parts.append({
                "x": x, "y": y, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                "life": random.uniform(0.25, 0.7), "col": col, "r": random.randint(4, 10),
            })

    def auto(self):
        aim, fire = 0.0, False
        if not self.sockets:
            return 0.0, False
        target = min(self.sockets, key=lambda s: abs(s["x"] - W / 2) + s["y"] * 0.15)
        want = math.atan2(target["x"] - W / 2, (H - 260) - target["y"])
        want = max(-1.0, min(1.0, want * 0.92))
        aim = max(-1.0, min(1.0, (want - self.angle) * 4.5))
        ready = abs(want - self.angle) < 0.12 and len(self.discs) < 2
        fire = ready or (self.charging and self.charge < 0.82)
        if self.t < 0.35:
            fire = False
        return aim, fire

    def draw(self):
        surf = self.screen
        surf.fill(NAVY)
        for i in range(18):
            y = int((i * 110 + self.t * 40) % (H + 80)) - 40
            pygame.draw.rect(surf, (10, 32, 44), (0, y, W, 36))
        for vx, ph in self.veins:
            pts = []
            for k in range(14):
                yy = 120 + k * 120
                xx = vx + math.sin(self.t * 1.2 + ph + k) * 18
                pts.append((xx, yy))
            pygame.draw.lines(surf, (28, 110, 130), False, pts, 4)
        for s in self.sockets:
            col = COLS[s["ci"]]
            pulse = 6 * math.sin(self.t * 3 + s["ph"])
            self._hex(surf, int(s["x"]), int(s["y"]), int(s["r"] + pulse), col, 6)
            pygame.draw.circle(surf, col, (int(s["x"]), int(s["y"])), 14)
        for d in self.discs:
            col = COLS[d["ci"]]
            pygame.draw.circle(surf, col, (int(d["x"]), int(d["y"])), d["r"])
            pygame.draw.circle(surf, WHITE, (int(d["x"]) - 6, int(d["y"]) - 6), 7)
        for p in self.parts:
            pygame.draw.circle(surf, p["col"], (int(p["x"]), int(p["y"])), max(1, p["r"]))
        self._coil(surf)
        bar = pygame.Surface((W, 150), pygame.SRCALPHA)
        bar.fill((4, 12, 18, 170))
        surf.blit(bar, (0, 0))
        title = self.font.render("CAVANSITE COIL", True, CYAN)
        surf.blit(title, title.get_rect(center=(W // 2, 62)))
        sc = self.small.render(f"SCORE {self.score}   COMBO x{self.combo}", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W // 2, 122)))
        foot = pygame.Surface((W, 90), pygame.SRCALPHA)
        foot.fill((4, 12, 18, 180))
        surf.blit(foot, (0, H - 90))
        tag = self.small.render("x.com/ElbowOS", True, LIME)
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 46)))
        return surf

    def _hex(self, surf, x, y, r, col, w):
        pts = [(x + math.cos(math.pi / 6 + i * math.pi / 3) * r,
                y + math.sin(math.pi / 6 + i * math.pi / 3) * r) for i in range(6)]
        pygame.draw.polygon(surf, col, pts, w)

    def _coil(self, surf):
        cx, cy = W // 2, H - 210
        ang = -math.pi / 2 + self.angle
        pygame.draw.rect(surf, (40, 28, 22), (cx - 120, cy + 40, 240, 36), border_radius=8)
        for i in range(7):
            rr = 28 + i * 9
            pygame.draw.circle(surf, COPPER, (cx, cy + 20), rr, 5)
        tip = (cx + math.cos(ang) * 150, cy + math.sin(ang) * 150)
        pygame.draw.line(surf, COPPER, (cx, cy), tip, 16)
        pygame.draw.circle(surf, GOLD if self.charge > 0.7 else CYAN, (int(tip[0]), int(tip[1])), 22)
        pygame.draw.rect(surf, (20, 16, 14), (cx - 90, cy + 78, 180, 18), border_radius=6)
        pygame.draw.rect(surf, LIME, (cx - 88, cy + 80, int(176 * self.charge), 14), border_radius=5)

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        dt = 1.0 / FPS
        try:
            for _ in range(frames):
                aim, fire = self.auto()
                self.step(dt, aim, fire)
                self.draw()
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)

    def play(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(FPS) / 1000.0
            aim = fire = 0
            hold = False
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                aim -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                aim += 1
            hold = keys[pygame.K_SPACE] or keys[pygame.K_UP]
            self.step(min(dt, 0.05), aim, hold)
            self.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play()
    else:
        g.record()
        pygame.quit()


if __name__ == "__main__":
    main()
