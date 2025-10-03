import pygame, sys

pygame.init()

# Screen setup
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Color Switch Maze")

# Colors
BLACK = (0,0,0)
WHITE = (255,255,255)
RED   = (200,50,50)
GREEN = (50,200,50)
BLUE  = (50,100,255)
YELLOW= (255,255,100)

# Clock
clock = pygame.time.Clock()

# Player
player_size = 20
player_x, player_y = 40, 40
player_speed = 4

# Player state (current color)
color_states = [RED, GREEN, BLUE]
state_index = 0
player_color = color_states[state_index]

# Maze walls: (x, y, w, h, color)
walls = [
    (100, 0, 20, 300, RED),
    (200, 100, 20, 300, GREEN),
    (300, 0, 20, 300, BLUE),
    (400, 100, 20, 300, RED),
    (500, 0, 20, 300, GREEN)
]

# Exit area
exit_rect = pygame.Rect(WIDTH-40, HEIGHT-40, 30, 30)

# Font
font = pygame.font.SysFont(None, 32)

def draw_text(text, x, y, color=WHITE):
    screen.blit(font.render(text, True, color), (x,y))

def reset_player():
    return 40, 40

running = True
while running:
    screen.fill(BLACK)

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Switch color
                state_index = (state_index + 1) % len(color_states)
                player_color = color_states[state_index]

    # Keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  player_x -= player_speed
    if keys[pygame.K_RIGHT]: player_x += player_speed
    if keys[pygame.K_UP]:    player_y -= player_speed
    if keys[pygame.K_DOWN]:  player_y += player_speed

    # Player rect
    player_rect = pygame.Rect(player_x, player_y, player_size, player_size)

    # Draw exit
    pygame.draw.rect(screen, YELLOW, exit_rect)

    # Draw walls
    for wx,wy,ww,wh,c in walls:
        pygame.draw.rect(screen, c, (wx,wy,ww,wh))
        if player_rect.colliderect(pygame.Rect(wx,wy,ww,wh)):
            if player_color != c:  # Wrong color
                player_x, player_y = reset_player()

    # Check exit
    if player_rect.colliderect(exit_rect):
        draw_text("YOU WIN!", WIDTH//2-60, HEIGHT//2, YELLOW)
        pygame.display.flip()
        pygame.time.delay(2000)
        pygame.quit(); sys.exit()

    # Draw player
    pygame.draw.rect(screen, player_color, player_rect)

    draw_text("Press SPACE to switch color", 10, 10)

    pygame.display.flip()
    clock.tick(30)
