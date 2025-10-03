"""
Reality Glitch Escape - PyGame prototype

Controls:
  Arrow keys / WASD - move
  R - restart
  Esc - quit

Goal:
  Reach the green exit tile while surviving random glitches.
"""

import pygame, sys, random, time

# --- Config ---
CELL = 32
COLS, ROWS = 18, 14
SCREEN_W, SCREEN_H = COLS * CELL, ROWS * CELL + 40
FPS = 30

# Colors
WALL = (40,40,40)
FLOOR = (20,20,25)
PLAYER_COLOR = (100,200,255)
EXIT_COLOR = (120,255,120)

GLITCH_INTERVAL = 4  # seconds between glitches
GLITCH_DURATION = 3  # how long glitch lasts

class GlitchEscape:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Reality Glitch Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.reset()

    def reset(self):
        self.grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        for r in range(ROWS):
            for c in range(COLS):
                if r in (0,ROWS-1) or c in (0,COLS-1):
                    self.grid[r][c] = 1
                elif random.random() < 0.18:
                    self.grid[r][c] = 1

        self.player = [1,1]
        self.exit = [COLS-2,ROWS-2]
        self.win = False

        self.glitch = None
        self.glitch_start = 0
        self.last_glitch = time.time()

    def trigger_glitch(self):
        glitches = ["invert_colors","no_walls","reverse_controls","fast_player","slow_player","flip_world"]
        self.glitch = random.choice(glitches)
        self.glitch_start = time.time()

    def clear_glitch(self):
        self.glitch = None

    def move_player(self, dx,dy):
        # apply reverse control glitch
        if self.glitch == "reverse_controls":
            dx, dy = -dx, -dy

        nr, nc = self.player[1]+dy, self.player[0]+dx
        if 0<=nr<ROWS and 0<=nc<COLS:
            if self.glitch=="no_walls" or self.grid[nr][nc]==0:
                self.player=[nc,nr]

        if self.player==self.exit:
            self.win=True

    def handle_events(self):
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()
                if e.key==pygame.K_r: self.reset()
                if not self.win:
                    if e.key in (pygame.K_LEFT,pygame.K_a): self.move_player(-1,0)
                    if e.key in (pygame.K_RIGHT,pygame.K_d): self.move_player(1,0)
                    if e.key in (pygame.K_UP,pygame.K_w): self.move_player(0,-1)
                    if e.key in (pygame.K_DOWN,pygame.K_s): self.move_player(0,1)

    def update(self):
        now = time.time()
        # trigger glitches
        if self.glitch and now-self.glitch_start > GLITCH_DURATION:
            self.clear_glitch()
        elif not self.glitch and now-self.last_glitch > GLITCH_INTERVAL:
            self.trigger_glitch()
            self.last_glitch = now

    def draw(self):
        self.screen.fill((0,0,0))
        # world flip glitch
        flip = self.glitch=="flip_world"

        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c*CELL, r*CELL, CELL, CELL)
                val = self.grid[r][c]
                if val==1:
                    color = WALL
                else:
                    color = FLOOR
                if flip:  # invert vertically
                    rect = pygame.Rect(c*CELL, (ROWS-1-r)*CELL, CELL, CELL)
                if self.glitch=="invert_colors":
                    color = tuple(255-x for x in color)
                pygame.draw.rect(self.screen, color, rect)

        # exit
        rect = pygame.Rect(self.exit[0]*CELL, self.exit[1]*CELL, CELL, CELL)
        if flip:
            rect = pygame.Rect(self.exit[0]*CELL, (ROWS-1-self.exit[1])*CELL, CELL, CELL)
        pygame.draw.rect(self.screen, EXIT_COLOR, rect)

        # player
        px, py = self.player
        if flip:
            py = ROWS-1-py
        pygame.draw.circle(self.screen, PLAYER_COLOR, (px*CELL+CELL//2, py*CELL+CELL//2), CELL//2-4)

        # HUD
        hud = f"Glitch: {self.glitch if self.glitch else 'None'}"
        if self.win: hud = "YOU ESCAPED! 🎉 Press R to restart"
        text = self.font.render(hud,True,(220,220,220))
        self.screen.blit(text,(10,SCREEN_H-30))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__=="__main__":
    GlitchEscape().run()
