"""
Echo World - PyGame prototype (single file)

Controls:
  Arrow keys / WASD - move
  Space - emit sonar ping (reveals nearby tiles briefly)
  R - regenerate maze and restart
  Esc or window close - quit

Requires: pygame
Run: python echo_world.py
"""

import pygame, random, sys, time, math
from collections import deque

# -------- Config --------
CELL = 24             # pixels per maze cell
MAZE_COLS = 25
MAZE_ROWS = 19
SCREEN_W = CELL * MAZE_COLS
SCREEN_H = CELL * MAZE_ROWS + 40  # extra for HUD
FPS = 60

PING_COOLDOWN = 0.6   # seconds between pings
PING_DURATION = 1.0   # how long revealed tiles remain visible
PING_SPEED = 450      # pixels per second for ping circle expansion
PING_MAX_RADIUS = max(SCREEN_W, SCREEN_H) * 1.1

PLAYER_COLOR = (240, 220, 120)
WALL_COLOR = (200, 200, 200)
FLOOR_COLOR = (40, 40, 40)
EXIT_COLOR = (60, 200, 80)

# Visibility tile states
VISIBLE_NONE = 0    # never revealed (dark)
VISIBLE_TEMP = 1    # revealed by ping (counts down)
VISIBLE_SEEN = 2    # permanently seen (optional; we'll keep temporary reveals only)

# -------- Maze generation (recursive backtracker) --------
def generate_maze(cols, rows):
    # grid of walls: True = wall, False = passage
    grid = [[True for _ in range(cols)] for _ in range(rows)]

    # start at random odd cell
    start_r = random.randrange(0, rows, 2)
    start_c = random.randrange(0, cols, 2)

    stack = [(start_r, start_c)]
    grid[start_r][start_c] = False

    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in [(-2,0),(2,0),(0,-2),(0,2)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc]:
                neighbors.append((nr,nc,dr,dc))
        if neighbors:
            nr, nc, dr, dc = random.choice(neighbors)
            # knock down wall between
            wall_r, wall_c = r + dr//2, c + dc//2
            grid[wall_r][wall_c] = False
            grid[nr][nc] = False
            stack.append((nr,nc))
        else:
            stack.pop()
    return grid

# Convert maze to playable grid where even indices are cells
# But above grid already works; we'll treat False as floor, True as wall

# Find random floor tile for player/exit
def random_floor_tile(grid):
    rows, cols = len(grid), len(grid[0])
    while True:
        r = random.randrange(rows)
        c = random.randrange(cols)
        if not grid[r][c]:
            return r, c

# Convert cell coords to pixel center
def cell_center(c, r):
    return (c * CELL + CELL//2, r * CELL + CELL//2)

# Distance util
def dist(a,b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# -------- Main game class --------
class EchoWorld:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Echo World (PyGame prototype)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.start_time = time.time()
        self.reset()

    def reset(self):
        # Maze: ensure odd dimensions for nice corridors, but okay with chosen size
        self.maze = generate_maze(MAZE_COLS, MAZE_ROWS)
        self.rows = len(self.maze)
        self.cols = len(self.maze[0])

        # Player start and exit on floor tiles
        self.player_r, self.player_c = random_floor_tile(self.maze)
        # ensure exit is different and reachable: we'll BFS to ensure path
        # find a far tile
        self.exit_r, self.exit_c = self.farthest_floor_from(self.player_r, self.player_c)

        # visibility grid: store list of (expiry_time) for temporary reveals
        self.visible_until = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]

        # pings (list of dicts with center, start_time)
        self.pings = []

        self.last_ping_time = -9999.0
        self.pings_used = 0

        self.start_time = time.time()
        self.win = False

    def farthest_floor_from(self, sr, sc):
        # BFS to find farthest floor cell
        q = deque()
        q.append((sr,sc,0))
        seen = set([(sr,sc)])
        far = (sr,sc,0)
        while q:
            r,c,d = q.popleft()
            if d > far[2]:
                far = (r,c,d)
            for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0<=nr<self.rows and 0<=nc<self.cols and not self.maze[nr][nc] and (nr,nc) not in seen:
                    seen.add((nr,nc))
                    q.append((nr,nc,d+1))
        return far[0], far[1]

    def emit_ping(self):
        now = time.time()
        if now - self.last_ping_time < PING_COOLDOWN:
            return
        self.last_ping_time = now
        self.pings_used += 1
        # center in pixels
        cx, cy = cell_center(self.player_c, self.player_r)
        ping = {"cx":cx, "cy":cy, "t":now}
        self.pings.append(ping)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        moved = False
        dr = dc = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dr = -1; moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dr = 1; moved = True
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dc = -1; moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dc = 1; moved = True

        # Movement: only one axis at a time for nicer control
        if dr != 0 and dc != 0:
            dc = 0

        if moved and (dr != 0 or dc != 0):
            nr, nc = self.player_r + dr, self.player_c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.maze[nr][nc]:
                self.player_r, self.player_c = nr, nc

    def update(self, dt):
        # remove old pings and update visible_until grid
        now = time.time()
        new_pings = []
        for ping in self.pings:
            age = now - ping["t"]
            if age <= PING_DURATION + (PING_MAX_RADIUS / PING_SPEED):
                new_pings.append(ping)
        self.pings = new_pings

        # For each ping, set visible_until for tiles inside current radius
        for ping in self.pings:
            age = now - ping["t"]
            radius = age * PING_SPEED
            if radius < 0:
                continue
            # clip radius
            if radius > PING_MAX_RADIUS:
                radius = PING_MAX_RADIUS
            # iterate over tiles overlapping bounding box
            min_c = max(0, int((ping["cx"] - radius) // CELL))
            max_c = min(self.cols-1, int((ping["cx"] + radius) // CELL))
            min_r = max(0, int((ping["cy"] - radius) // CELL))
            max_r = min(self.rows-1, int((ping["cy"] + radius) // CELL))
            for r in range(min_r, max_r+1):
                for c in range(min_c, max_c+1):
                    if not self.maze[r][c]:
                        cx, cy = cell_center(c, r)
                        if dist((cx, cy), (ping["cx"], ping["cy"])) <= radius + CELL*0.7:
                            # reveal this tile until slightly after ping duration to show fade
                            self.visible_until[r][c] = max(self.visible_until[r][c], ping["t"] + PING_DURATION)

        # Check win
        if (self.player_r, self.player_c) == (self.exit_r, self.exit_c):
            self.win = True

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if e.key == pygame.K_SPACE:
                    self.emit_ping()
                if e.key == pygame.K_r:
                    self.reset()

    def draw(self):
        self.screen.fill((0,0,0))
        now = time.time()

        # Draw maze tiles as dark floor unless revealed
        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(c*CELL, r*CELL, CELL, CELL)
                if self.maze[r][c]:
                    # wall
                    # check if visible
                    if self.visible_until[r][c] >= now:
                        pygame.draw.rect(self.screen, WALL_COLOR, rect)
                    else:
                        # invisible wall -> black (covered)
                        pygame.draw.rect(self.screen, (0,0,0), rect)
                else:
                    # floor
                    if self.visible_until[r][c] >= now:
                        pygame.draw.rect(self.screen, FLOOR_COLOR, rect)
                    else:
                        pygame.draw.rect(self.screen, (0,0,0), rect)

        # Draw exit (only visible if currently revealed)
        if self.visible_until[self.exit_r][self.exit_c] >= now:
            ex_rect = pygame.Rect(self.exit_c*CELL, self.exit_r*CELL, CELL, CELL)
            pygame.draw.rect(self.screen, EXIT_COLOR, ex_rect)

        # Draw ping circles (ring effect)
        for ping in self.pings:
            age = now - ping["t"]
            r_px = age * PING_SPEED
            alpha = 255
            if age < 0:
                continue
            # fade near end of ping duration
            if now > ping["t"] + PING_DURATION:
                remaining = max(0, (ping["t"] + PING_DURATION + (PING_MAX_RADIUS / PING_SPEED) - now))
                alpha = int(255 * (remaining / (PING_MAX_RADIUS / PING_SPEED)))
            # draw expanding ring (use surface to set alpha)
            if r_px > 0:
                surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                pygame.draw.circle(surf, (200,200,255, int(alpha*0.6)), (int(ping["cx"]), int(ping["cy"])), int(min(r_px, PING_MAX_RADIUS)), width=3)
                # soft inner glow
                pygame.draw.circle(surf, (200,200,255, int(alpha*0.12)), (int(ping["cx"]), int(ping["cy"])), int(min(r_px*0.5, PING_MAX_RADIUS)), width=0)
                self.screen.blit(surf, (0,0))

        # Player (draw even if in dark so player can orient; in a stricter version hide player too)
        px, py = cell_center(self.player_c, self.player_r)
        pygame.draw.circle(self.screen, PLAYER_COLOR, (px, py), CELL//2 - 2)

        # HUD
        hud_rect = pygame.Rect(0, SCREEN_H-40, SCREEN_W, 40)
        pygame.draw.rect(self.screen, (20,20,20), hud_rect)
        t_elapsed = int(now - self.start_time)
        txt = f"Ping (Space): {self.pings_used}   Time: {t_elapsed}s   (R: regenerate) "
        if self.win:
            txt = "YOU REACHED THE EXIT! Press R to play again. " + txt
        text_surf = self.font.render(txt, True, (220,220,220))
        self.screen.blit(text_surf, (8, SCREEN_H-32))

        # Mini-map: small grid showing 'seen' cells (optional)
        mini_w = 160
        mini_h = 120
        mini_x = SCREEN_W - mini_w - 8
        mini_y = SCREEN_H - mini_h - 8
        mini_surf = pygame.Surface((mini_w, mini_h))
        mini_surf.fill((10,10,10))
        cell_w = mini_w / self.cols
        cell_h = mini_h / self.rows
        for r in range(self.rows):
            for c in range(self.cols):
                cxr = int(c * cell_w)
                ryr = int(r * cell_h)
                color = None
                if self.visible_until[r][c] >= now:
                    if self.maze[r][c]:
                        color = (200,200,200)
                    else:
                        color = (60,60,60)
                else:
                    color = (8,8,8)
                mini_surf.fill(color, (cxr, ryr, math.ceil(cell_w), math.ceil(cell_h)))
        # player dot and exit dot
        prx = int(self.player_c * cell_w + cell_w/2)
        pry = int(self.player_r * cell_h + cell_h/2)
        erx = int(self.exit_c * cell_w + cell_w/2)
        ery = int(self.exit_r * cell_h + cell_h/2)
        pygame.draw.circle(mini_surf, (240,220,120), (prx, pry), 3)
        pygame.draw.circle(mini_surf, EXIT_COLOR, (erx, ery), 3)
        self.screen.blit(mini_surf, (mini_x, mini_y))

        pygame.display.flip()

    def run(self):
        last_time = time.time()
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.handle_input()
            self.update(dt)
            self.draw()

# -------- Entry point --------
if __name__ == "__main__":
    try:
        EchoWorld().run()
    except Exception as e:
        print("Error:", e)
        pygame.quit()
        sys.exit()
