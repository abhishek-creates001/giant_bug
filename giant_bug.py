"""
Giant Worm - a procedural creature that chases a fly.

Install:  pip install pygame
Run:      python giant_bug.py
Quit:     ESC or close the window
"""

import math
import sys
import pygame
from pygame.math import Vector2 as V

W, H = 1200, 800
FPS = 60

# ---------- colours ----------
BG = (22, 24, 20)
BODY_DARK = (73, 42, 28)
BODY_MID = (148, 82, 47)
BODY_LIGHT = (205, 132, 77)
BODY_BAND = (103, 54, 35)
EYE = (28, 20, 18)
FLY_BODY = (38, 43, 36)
FLY_WING = (175, 205, 194, 155)
FLY_EYE = (155, 35, 35)

# Body segments run from the head to the tapered tail.
RADII = [25, 30, 33, 34, 34, 32, 29, 25, 20, 14, 8]
SPACING = [0, 24, 25, 25, 25, 24, 23, 22, 20, 18, 15]
MAX_SPEED = 480
SIZE_PER_FLY = 0.25
MAX_SIZE = 3.0


def perp(v):
    return V(-v.y, v.x)


def safe_norm(v, fallback=None):
    if fallback is None:
        fallback = V(1, 0)
    v = V(v)
    if v.length_squared() <= 1e-6:
        return V(fallback)
    return v.normalize()


class Bug:
    def __init__(self):
        self.seg = [V(W / 2 - sum(SPACING[:i + 1]), H / 2) for i in range(len(RADII))]
        self.vel = V(0, 0)
        self.time = 0.0
        self.size = 1.0

    # --- frame vectors for a segment ---
    def axis(self, i):
        if i == 0:
            return safe_norm(self.seg[0] - self.seg[1])
        j = min(i + 1, len(self.seg) - 1)
        return safe_norm(self.seg[i - 1] - self.seg[j])

    def update(self, target, dt):
        self.time += dt
        head = self.seg[0]
        to_t = target - head
        dist = to_t.length()

        # chase the cursor (slows down near it, rests when close)
        if dist > 45:
            speed = min((dist - 45) * 4.0, MAX_SPEED)
            desired = safe_norm(to_t) * speed
        else:
            desired = V(0, 0)
        self.vel = self.vel.lerp(desired, 1 - math.exp(-7 * dt))
        self.seg[0] = head + self.vel * dt

        # body segments trail behind
        for i in range(1, len(self.seg)):
            d = self.seg[i - 1] - self.seg[i]
            self.seg[i] = self.seg[i - 1] - safe_norm(d) * SPACING[i] * self.size

    def grow(self):
        self.size = min(round(self.size + SIZE_PER_FLY, 10), MAX_SIZE)
        return self.size >= MAX_SIZE


    # ---------- drawing ----------
    def draw(self, surf):
        # Draw each body section as a shaded disc over a continuous shadowed body.
        shadow = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(len(self.seg) - 1):
            width = int((RADII[i] + RADII[i + 1]) * 1.8 * self.size)
            pygame.draw.line(shadow, (0, 0, 0, 65), self.seg[i] + V(10, 15),
                             self.seg[i + 1] + V(10, 15), width)
        for i, s in enumerate(self.seg):
            pygame.draw.circle(shadow, (0, 0, 0, 60), s + V(10, 15),
                               int((RADII[i] + 3) * self.size))
        surf.blit(shadow, (0, 0))

        for i in range(len(self.seg) - 1, -1, -1):
            if i > 0:
                width = int((RADII[i] + RADII[i - 1]) * 0.92 * self.size)
                pygame.draw.line(surf, BODY_DARK, self.seg[i], self.seg[i - 1], width)
                pygame.draw.line(surf, BODY_MID, self.seg[i] - V(0, 3),
                                 self.seg[i - 1] - V(0, 3), max(1, width - int(8 * self.size)))
        for i in reversed(range(len(self.seg))):
            pulse = math.sin(self.time * 4 - i * 0.45) * 1.5
            s, r = self.seg[i], (RADII[i] + pulse) * self.size
            pygame.draw.circle(surf, BODY_DARK, s, r)
            pygame.draw.circle(surf, BODY_MID, s - V(0, 3), r * 0.84)
            pygame.draw.ellipse(surf, BODY_LIGHT,
                                (s.x - r * 0.56, s.y - r * 0.58, r * 1.0, r * 0.48))
            if 2 <= i <= 8:
                f = self.axis(i)
                n = perp(f)
                pygame.draw.line(surf, BODY_BAND, s - n * r * 0.72,
                                 s + n * r * 0.72, max(2, int(3 * self.size)))

        # small eyes and a simple mouth give the worm a clear front.
        head, hf = self.seg[0], self.axis(0)
        hn = perp(hf)
        for side in (-1, 1):
            eye = head + hf * 5 * self.size + hn * side * 14 * self.size
            pygame.draw.circle(surf, (235, 190, 145), eye, max(2, int(5 * self.size)))
            pygame.draw.circle(surf, EYE, eye + hf * 1.5 * self.size,
                               max(1, int(2 * self.size)))
        mouth = head + hf * 19 * self.size
        pygame.draw.line(surf, BODY_DARK, mouth - hn * 5 * self.size,
                         mouth + hn * 5 * self.size, max(1, int(2 * self.size)))


def draw_cursor(surf, pos, time):
    heading = V(math.cos(time * 2.2), math.sin(time * 2.2))
    side = perp(heading)
    wingbeat = math.sin(time * 38) * 0.32

    for sign in (-1, 1):
        wing_center = pos - heading * 2 + side * sign * (8 + wingbeat * sign)
        wing = pygame.Surface((34, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(wing, FLY_WING, (2, 2, 30, 16))
        wing_angle = math.degrees(math.atan2(side.y * sign - wingbeat,
                                             side.x * sign + wingbeat))
        rotated = pygame.transform.rotate(wing, -wing_angle)
        surf.blit(rotated, rotated.get_rect(center=wing_center))

    thorax = pos + heading * 1
    abdomen = pos - heading * 9
    pygame.draw.line(surf, FLY_BODY, thorax, abdomen, 5)
    pygame.draw.circle(surf, FLY_BODY, thorax, 5)
    pygame.draw.circle(surf, (55, 60, 48), abdomen, 4)
    head = pos + heading * 8
    pygame.draw.circle(surf, FLY_EYE, head + side * 3, 3)
    pygame.draw.circle(surf, FLY_EYE, head - side * 3, 3)
    pygame.draw.line(surf, FLY_BODY, head + heading * 3,
                     head + heading * 10, 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Giant Worm - chase the fly!")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    bug = Bug()
    t = 0.0
    can_eat = True
    game_over = False
    font = pygame.font.Font(None, 84)
    message_font = pygame.font.Font(None, 34)
    button_font = pygame.font.Font(None, 38)
    restart_button = pygame.Rect(W // 2 - 170, H // 2 + 85, 150, 58)
    exit_button = pygame.Rect(W // 2 + 20, H // 2 + 85, 150, 58)

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        t += dt
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE or (game_over and e.key == pygame.K_q):
                    pygame.quit()
                    sys.exit()
                if game_over and e.key in (pygame.K_r, pygame.K_RETURN):
                    bug = Bug()
                    can_eat = True
                    game_over = False
                    pygame.mouse.set_visible(False)
            if game_over and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if restart_button.collidepoint(e.pos):
                    bug = Bug()
                    can_eat = True
                    game_over = False
                    pygame.mouse.set_visible(False)
                elif exit_button.collidepoint(e.pos):
                    pygame.quit()
                    sys.exit()

        mouse = V(pygame.mouse.get_pos())
        if not game_over:
            bug.update(mouse, dt)
            distance = (mouse - bug.seg[0]).length()
            bite_distance = RADII[0] * bug.size + 10
            if not can_eat and distance > bite_distance + 55:
                can_eat = True
            elif can_eat and distance < bite_distance:
                can_eat = False
                game_over = bug.grow()

        screen.fill(BG)
        bug.draw(screen)
        if not game_over:
            draw_cursor(screen, mouse, t)
        else:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            screen.blit(overlay, (0, 0))
            title = font.render("GAME OVER", True, (245, 218, 184))
            message = message_font.render("The worm reached its maximum size!", True, (220, 195, 160))
            screen.blit(title, title.get_rect(center=(W // 2, H // 2 - 30)))
            screen.blit(message, message.get_rect(center=(W // 2, H // 2 + 32)))
            pygame.mouse.set_visible(True)
            for rect, label in ((restart_button, "Restart"), (exit_button, "Exit")):
                color = (117, 82, 54) if rect.collidepoint(mouse) else (83, 62, 45)
                pygame.draw.rect(screen, color, rect, border_radius=8)
                pygame.draw.rect(screen, (220, 185, 145), rect, 2, border_radius=8)
                text = button_font.render(label, True, (245, 225, 200))
                screen.blit(text, text.get_rect(center=rect.center))
        pygame.display.flip()


if __name__ == "__main__":
    main()
