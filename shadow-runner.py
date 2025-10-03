import pygame, sys, random
from collections import deque

pygame.init()

# Screen setup
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shadow Runner")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
BLUE = (50, 100, 255)

# Clock
clock = pygame.time.Clock()

# Player
player_size = 20
player_x, player_y = WIDTH // 2, HEIGHT // 2
player_speed = 5

# Shadow (follows history of player moves)
shadow_delay = 30  # frames delay
history = deque(maxlen=200)

# Font
font = pygame.font.SysFont(None, 36)

def draw_text(text, x, y, color=WHITE):
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

score = 0
running = True
while running:
    screen.fill(BLACK)

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: player_x -= player_speed
    if keys[pygame.K_RIGHT]: player_x += player_speed
    if keys[pygame.K_UP]: player_y -= player_speed
    if keys[pygame.K_DOWN]: player_y += player_speed

    # Keep inside screen
    player_x = max(0, min(WIDTH - player_size, player_x))
    player_y = max(0, min(HEIGHT - player_size, player_y))

    # Save position to history
    history.append((player_x, player_y))

    # Shadow follows delayed path
    shadow_x, shadow_y = history[0] if len(history) >= shadow_delay else (-100, -100)

    # Draw player and shadow
    pygame.draw.rect(screen, BLUE, (player_x, player_y, player_size, player_size))
    pygame.draw.rect(screen, RED, (shadow_x, shadow_y, player_size, player_size))

    # Check collision
    if abs(player_x - shadow_x) < player_size and abs(player_y - shadow_y) < player_size:
        draw_text("GAME OVER!", WIDTH // 2 - 100, HEIGHT // 2, RED)
        pygame.display.flip()
        pygame.time.delay(2000)
        pygame.quit()
        sys.exit()

    # Score increases over time
    score += 1
    draw_text(f"Score: {score}", 10, 10)

    pygame.display.flip()
    clock.tick(30)
