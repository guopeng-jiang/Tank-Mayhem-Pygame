import pygame
import sys
import math
import random

# --- Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 180, 0)
RED = (180, 0, 0)
BLUE = (0, 0, 200)
YELLOW = (200, 200, 0)
ORANGE = (200, 100, 0)
GREY = (150, 150, 150)
GRASS_GREEN = (40, 150, 40) # <-- ADD THIS LINE

# Player Constants
PLAYER_SIZE = 15
PLAYER_SPEED = 1
PLAYER_MAX_HEALTH = 3 # Can take 3 hits from medium/small, 1 from large
PLAYER_MAX_AMMO = 30

# Enemy Constants (Type variations)
ENEMY_TYPES = {
    'small': {
        'size': 12,
        'health': 1,
        'speed_mod': 0.7, # Small tanks are slightly faster
        'color': GREY,
        'damage': 1,
        'score': 10,
    },
    'medium': {
        'size': 15,
        'health': 2,
        'speed_mod': 0.6, # Medium are slightly slower
        'color': ORANGE,
        'damage': 1,
        'score': 25,
    },
    'large': {
        'size': 18,
        'health': 3,
        'speed_mod': 0.55, # Large are slowest
        'color': RED, # Use the base RED color for large
        'damage': 3,  # Deals enough damage to kill player in one hit
        'score': 50,
    }
}
ENEMY_COUNT = 10 # Increased count slightly
ENEMY_MAX_AMMO = 30
ENEMY_AIM_TOLERANCE = 10 # Degrees within player direction to fire

# Bullet Constants
BULLET_SPEED = 3
BULLET_SIZE = 6
SHOOT_DELAY = 300 # Player shoot cooldown
ENEMY_SHOOT_DELAY = 900 # Enemy base shoot cooldown (modified by aim check)
BULLET_SPAWN_OFFSET_FACTOR = 0.7 # Factor of tank size

# Barrier Constants
BARRIER_COUNT = 25
MIN_BARRIER_WIDTH = 10
MAX_BARRIER_WIDTH = 70
MIN_BARRIER_HEIGHT = 10
MAX_BARRIER_HEIGHT = 70
BARRIER_PADDING_FACTOR = 2.0 # Factor of *average* tank size? Use player size for now.
PLAYER_START_CLEARANCE_FACTOR = 4.0
BORDER_THICKNESS = 10

# Power-up Constants
POWERUP_SIZE = 18
POWERUP_RESPAWN_TIME = 30000 # 30 seconds in milliseconds
POWERUP_LIFESPAN = 20000 # Power-ups last 20 seconds if not collected
YELLOW = (255, 255, 0) # Star color
HEALTH_CROSS_COLOR = (255, 50, 50) # Reddish color for health cross

# Enemy Constants
CHASE_DISTANCE = 100 # Pixels within which enemies start chasing
CHASE_STOP_DISTANCE = 300 # Pixels beyond which enemies might stop chasing (hysteresis)

# Explosion Constants
PARTICLE_COUNT = 15        # How many particles per explosion
PARTICLE_SPEED_MIN = 1
PARTICLE_SPEED_MAX = 4
PARTICLE_LIFESPAN = 25     # How many frames particles last (approx 0.4s at 60fps)
PARTICLE_START_SIZE = 5
PARTICLE_END_SIZE = 1
EXPLOSION_COLORS = [(255, 0, 0), (255, 100, 0), (255, 200, 0), (200, 200, 200)] # Red, Orange, Yellow, Grey

# Safe Zone Circle Constants
GAME_DURATION = 2 * 60 * 1000 # 2 minute in milliseconds
CIRCLE_START_RADIUS_FACTOR = 1.1 # Factor of screen half-diagonal
CIRCLE_END_RADIUS = PLAYER_SIZE * 5 # Final radius (quite small)
CIRCLE_COLOR = (150, 150, 255, 100) # Light blue, semi-transparent (RGBA)
CIRCLE_WARNING_COLOR = (255, 100, 0, 120) # Orange when close to edge
CIRCLE_THICKNESS = 3
CIRCLE_DAMAGE_PER_SECOND = 0.5 # HP drain per second outside (adjust as needed)
# Or use instant kill:
# CIRCLE_INSTANT_KILL = True

# --- Helper Functions ---
def angle_diff(a1, a2):
    """ Calculates the shortest difference between two angles (-180 to 180). """
    return (a1 - a2 + 180) % 360 - 180

def draw_text(surface, text, size, x, y, color=WHITE):
    """ Helper to draw text on the screen """
    font = pygame.font.Font(None, size) # Use default font
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

# --- Player Tank Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = PLAYER_SIZE
        self.base_image = pygame.Surface([self.size, self.size], pygame.SRCALPHA)
        pygame.draw.rect(self.base_image, GREEN, [0, 0, self.size, self.size], border_radius=2)
        pygame.draw.line(self.base_image, WHITE,
                         (self.size // 2, self.size // 2),
                         (self.size, self.size // 2),
                         max(1, self.size // 8))
        self.image = self.base_image
        self.start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.rect = self.image.get_rect(center=self.start_pos)
        self.angle = 0
        self.vel_x = 0
        self.vel_y = 0
        self.last_shot_time = 0
        self.health = PLAYER_MAX_HEALTH # Added health
        self.ammo = PLAYER_MAX_AMMO     # Added ammo

    def update(self, walls, enemies_group):
        if self.health <= 0: return # Don't update if dead

        # Aiming
        mouse_x, mouse_y = pygame.mouse.get_pos()
        delta_x = mouse_x - self.rect.centerx
        delta_y = mouse_y - self.rect.centery
        self.angle = math.degrees(math.atan2(delta_y, delta_x))

        # Rotation
        self.image = pygame.transform.rotate(self.base_image, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # --- Movement ---
        old_center = self.rect.center # Store position *before* any movement
        applied_vel_x = self.vel_x
        applied_vel_y = self.vel_y

        # --- Try moving X ---
        self.rect.x += applied_vel_x
        # Check wall collision X
        colliding_walls_x = pygame.sprite.spritecollide(self, walls, False)
        if colliding_walls_x:
            self.rect.x -= applied_vel_x # Revert X move if wall collision
            applied_vel_x = 0 # Don't apply X velocity if blocked by wall

        # Check enemy collision X (only if not blocked by wall)
        if applied_vel_x != 0:
            colliding_enemies_x = pygame.sprite.spritecollide(self, enemies_group, False)
            if colliding_enemies_x:
                self.rect.x -= applied_vel_x # Revert X move if enemy collision
                applied_vel_x = 0 # Mark X as blocked

        # --- Try moving Y ---
        self.rect.y += applied_vel_y
        # Check wall collision Y
        colliding_walls_y = pygame.sprite.spritecollide(self, walls, False)
        if colliding_walls_y:
            self.rect.y -= applied_vel_y # Revert Y move if wall collision
            applied_vel_y = 0 # Don't apply Y velocity if blocked by wall

        # Check enemy collision Y (only if not blocked by wall)
        if applied_vel_y != 0:
            colliding_enemies_y = pygame.sprite.spritecollide(self, enemies_group, False)
            if colliding_enemies_y:
                 # Check if we already reverted X due to an enemy
                 # If so, and Y is also blocked by *the same enemy or another one*,
                 # we might be truly stuck. For now, just revert Y.
                self.rect.y -= applied_vel_y # Revert Y move if enemy collision
                applied_vel_y = 0 # Mark Y as blocked


        # --- Final Position & Screen Bounds ---
        # Apply screen bounds clamping AFTER resolving collisions
        self.rect.left = max(BORDER_THICKNESS, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH - BORDER_THICKNESS, self.rect.right)
        self.rect.top = max(BORDER_THICKNESS, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT - BORDER_THICKNESS, self.rect.bottom)

        # Reset external velocity request flags
        self.vel_x = 0
        self.vel_y = 0

    def move_up(self): self.vel_y = -PLAYER_SPEED
    def move_down(self): self.vel_y = PLAYER_SPEED
    def move_left(self): self.vel_x = -PLAYER_SPEED
    def move_right(self): self.vel_x = PLAYER_SPEED

    def shoot(self, all_sprites, bullets):
        if self.ammo <= 0:
            # print("Player out of ammo!") # Optional feedback
            # Add empty click sound here later?
            return

        now = pygame.time.get_ticks()
        if now - self.last_shot_time > SHOOT_DELAY:
            self.last_shot_time = now
            self.ammo -= 1 # Decrement ammo

            rad_angle = math.radians(self.angle)
            spawn_offset = self.size * BULLET_SPAWN_OFFSET_FACTOR
            spawn_x = self.rect.centerx + math.cos(rad_angle) * spawn_offset
            spawn_y = self.rect.centery + math.sin(rad_angle) * spawn_offset
            # Player bullets deal 1 damage by default
            bullet = Bullet(spawn_x, spawn_y, self.angle, color=BLUE, damage=1)
            all_sprites.add(bullet)
            bullets.add(bullet)
            # print(f"Player Ammo: {self.ammo}") # Debug

    def take_damage(self, amount):
        self.health -= amount
        print(f"Player Hit! Health: {self.health}/{PLAYER_MAX_HEALTH}")
        if self.health <= 0:
            self.kill() # Remove sprite from groups

# --- Enemy Tank Class ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, walls):
        super().__init__()
        self.walls = walls # Keep reference to walls

        # --- INSERT THIS BLOCK HERE ---
        # Choose Type and Set Properties
        self.type = random.choice(list(ENEMY_TYPES.keys()))
        type_data = ENEMY_TYPES[self.type]
        self.size = type_data['size']           # <-- Sets self.size
        self.max_health = type_data['health']
        self.health = type_data['health']
        self.speed = PLAYER_SPEED * type_data['speed_mod']
        self.color = type_data['color']
        self.damage = type_data['damage']
        self.score_value = type_data['score']
        # --- END OF BLOCK TO INSERT ---

        # Now self.size exists and can be used:
        self.base_image = pygame.Surface([self.size, self.size], pygame.SRCALPHA)
        pygame.draw.rect(self.base_image, self.color, [0, 0, self.size, self.size], border_radius=2)
        pygame.draw.line(self.base_image, WHITE,
                         (self.size // 2, self.size // 2),
                         (self.size, self.size // 2),
                         max(1, self.size // 8))
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = random.randint(0, 359)

        # ... rest of the __init__ method (timers, ammo, state, etc.) ...
        self.change_dir_timer = pygame.time.get_ticks() + random.randint(500, 1500)
        self.shoot_timer = pygame.time.get_ticks() + random.randint(1000, 2500)
        self.last_shot_time = 0
        self.ammo = ENEMY_MAX_AMMO
        self.lookahead_dist = self.size * 1.3 # Use self.size after it's set
        self.state = 'roaming'

    # Update method now includes chasing logic
    def update(self, all_sprites, bullets, player_rect, players_group, enemies_group):
        if self.health <= 0: return
        now = pygame.time.get_ticks()

        # --- State Handling & Target Acquisition ---
        target_angle = self.angle
        current_state = self.state

        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            distance_to_player = math.hypot(dx, dy)
            if self.state == 'roaming' and distance_to_player < CHASE_DISTANCE:
                self.state = 'chasing'
            # Removed stop chasing hysteresis for simplicity
        else:
             self.state = 'roaming'

        # --- Collision Prediction (Walls) ---
        # Calculate prediction based on current angle BEFORE deciding turns
        rad_predict_angle = math.radians(self.angle)
        lookahead_x = self.rect.centerx + math.cos(rad_predict_angle) * self.lookahead_dist
        lookahead_y = self.rect.centery + math.sin(rad_predict_angle) * self.lookahead_dist
        lookahead_rect = pygame.Rect(0, 0, 4, 4)
        lookahead_rect.center = (lookahead_x, lookahead_y)

        predicted_wall_collision = False
        for wall in self.walls:
            if wall.rect.colliderect(lookahead_rect):
                predicted_wall_collision = True
                break
        if not (BORDER_THICKNESS < lookahead_x < SCREEN_WIDTH - BORDER_THICKNESS and \
                BORDER_THICKNESS < lookahead_y < SCREEN_HEIGHT - BORDER_THICKNESS):
            predicted_wall_collision = True


        # --- AI Decision Making (Angle and Turning) ---
        force_turn = False # Flag if completely stuck after movement attempt

        if self.state == 'roaming':
            # Regular random turning timer OR if predicting wall collision
            if now > self.change_dir_timer or predicted_wall_collision:
                # Turn more sharply if predicting a wall hit
                turn_range = 110 if predicted_wall_collision else 90
                self.angle += random.randint(-turn_range, turn_range)
                self.angle %= 360
                # Reset timer with shorter delay if turning due to prediction
                delay = random.randint(300, 800) if predicted_wall_collision else random.randint(1500, 4000)
                self.change_dir_timer = now + delay
            target_angle = self.angle

        elif self.state == 'chasing' and player_rect:
            target_angle = math.degrees(math.atan2(dy, dx))
            # If chasing AND predicting wall, force a turn away from wall? (More complex)
            # For now, just let the stuck logic handle it if chasing into wall.
            self.angle = target_angle # Snap angle
            self.angle %= 360


        # --- Rotation ---
        # Apply the decided final angle
        self.image = pygame.transform.rotate(self.base_image, -self.angle)
        current_center = self.rect.center
        self.rect = self.image.get_rect(center=current_center)


        # --- Movement Execution ---
        # Always attempt to move based on the current angle
        old_center = self.rect.center
        applied_dx = 0
        applied_dy = 0

        rad_move_angle = math.radians(self.angle) # Use final angle for movement
        potential_dx = math.cos(rad_move_angle) * self.speed
        potential_dy = math.sin(rad_move_angle) * self.speed

        # Create the check group
        tanks_to_check = players_group.sprites() + [e for e in enemies_group if e != self]
        temp_group_for_check = pygame.sprite.Group(tanks_to_check)

        # Try moving X
        self.rect.x += potential_dx
        collided_wall_x = pygame.sprite.spritecollide(self, self.walls, False)
        collided_tank_x = pygame.sprite.spritecollide(self, temp_group_for_check, False)
        if collided_wall_x or collided_tank_x:
            self.rect.x -= potential_dx # Revert X
        else:
            applied_dx = potential_dx # X move successful

        # Try moving Y
        self.rect.y += potential_dy
        collided_wall_y = pygame.sprite.spritecollide(self, self.walls, False)
        collided_tank_y = pygame.sprite.spritecollide(self, temp_group_for_check, False)
        if collided_wall_y or collided_tank_y:
             self.rect.y -= potential_dy # Revert Y
        else:
             applied_dy = potential_dy # Y move successful

        # --- Check if Stuck & Force Turn ---
        # Only force turn if movement was attempted but resulted in zero displacement
        if applied_dx == 0 and applied_dy == 0 and (abs(potential_dx) > 0.01 or abs(potential_dy) > 0.01): # Check potential was non-zero
             self.rect.center = old_center # Ensure full revert if stuck
             self.angle += random.choice([110, -110, 135, -135, 160, -160, 180])
             self.angle %= 360
             self.change_dir_timer = now + random.randint(100, 400) # Re-evaluate soon


        # --- Shooting Logic ---
        if player_rect and self.ammo > 0 and now > self.shoot_timer:
             if now - self.last_shot_time > ENEMY_SHOOT_DELAY:
                 angle_to_player = math.degrees(math.atan2(player_rect.centery - self.rect.centery,
                                                         player_rect.centerx - self.rect.centerx))
                 # Shoot if chasing and aimed, or if roaming and aimed
                 should_shoot = (self.state == 'chasing' or self.state == 'roaming')

                 if should_shoot and abs(angle_diff(self.angle, angle_to_player)) < ENEMY_AIM_TOLERANCE:
                     # ... (fire bullet) ...
                     self.last_shot_time = now
                     self.ammo -= 1
                     bullet_angle = self.angle
                     rad_bullet_angle = math.radians(bullet_angle)
                     spawn_offset = self.size * BULLET_SPAWN_OFFSET_FACTOR
                     spawn_x = self.rect.centerx + math.cos(rad_bullet_angle) * spawn_offset
                     spawn_y = self.rect.centery + math.sin(rad_bullet_angle) * spawn_offset
                     bullet = Bullet(spawn_x, spawn_y, bullet_angle, color=self.color, damage=self.damage)
                     all_sprites.add(bullet)
                     bullets.add(bullet)
                     self.shoot_timer = now + random.randint(500, 1500)
                 else:
                      self.shoot_timer = now + random.randint(200, 500)

    def take_damage(self, amount):
        self.health -= amount
        # print(f"Enemy {self.type} hit! Health: {self.health}/{self.max_health}") # Debug
        if self.health <= 0:
            return True # Indicate death
        return False # Still alive

# --- Bullet Class ---
class Bullet(pygame.sprite.Sprite):
    # Added damage parameter
    def __init__(self, x, y, angle, color=BLUE, damage=1):
        super().__init__()
        self.image = pygame.Surface([BULLET_SIZE, BULLET_SIZE], pygame.SRCALPHA) # Use SRCALPHA
        # Draw circle, use colorkey only if background isn't transparent
        pygame.draw.circle(self.image, color, (BULLET_SIZE//2, BULLET_SIZE//2), BULLET_SIZE//2)
        # self.image.set_colorkey(BLACK) # Not needed with SRCALPHA and clear background
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = BULLET_SPEED
        self.damage = damage # Store damage value
        rad_angle = math.radians(self.angle)
        self.vel_x = math.cos(rad_angle) * self.speed
        self.vel_y = math.sin(rad_angle) * self.speed

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if not (BORDER_THICKNESS < self.rect.centerx < SCREEN_WIDTH - BORDER_THICKNESS and \
                BORDER_THICKNESS < self.rect.centery < SCREEN_HEIGHT - BORDER_THICKNESS):
             self.kill()

# --- Wall Class --- (No changes needed)
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# --- Particle Class for Explosions ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(groups) # Add to groups immediately
        self.x, self.y = x, y
        self.color = random.choice(EXPLOSION_COLORS)
        self.lifespan = PARTICLE_LIFESPAN
        self.size = PARTICLE_START_SIZE

        # Random velocity
        angle = random.uniform(0, 2 * math.pi) # Random direction in radians
        speed = random.uniform(PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX)
        self.vel_x = math.cos(angle) * speed
        self.vel_y = math.sin(angle) * speed

        # Create initial image and rect
        self.image = pygame.Surface([self.size * 2, self.size * 2], pygame.SRCALPHA) # Double size for antialiasing
        pygame.draw.circle(self.image, self.color, (self.size, self.size), self.size)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        # Move
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.center = (int(self.x), int(self.y))

        # Shrink and Fade (by decreasing size)
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill() # Remove sprite when lifespan ends
            return

        # Calculate new size based on lifespan
        t = self.lifespan / PARTICLE_LIFESPAN # Ratio 0 to 1
        current_size = int(PARTICLE_END_SIZE + (PARTICLE_START_SIZE - PARTICLE_END_SIZE) * t)
        current_size = max(1, current_size) # Ensure size is at least 1

        # Re-create image if size changed significantly (or every frame if simpler)
        if current_size != self.size:
             self.size = current_size
             center = self.rect.center # Store center
             self.image = pygame.Surface([self.size * 2, self.size * 2], pygame.SRCALPHA)
             pygame.draw.circle(self.image, self.color, (self.size, self.size), self.size)
             self.rect = self.image.get_rect(center=center) # Re-center

        # Optional: Add friction/gravity here if desired
        # self.vel_y += 0.1 # Simple gravity

# --- Ammo Refill Power-up Class ---
class AmmoRefill(pygame.sprite.Sprite):
    def __init__(self, x, y, spawn_time): # Added spawn_time
        super().__init__()
        self.type = 'ammo' # Identify the type
        self.size = POWERUP_SIZE
        self.image = pygame.Surface([self.size, self.size], pygame.SRCALPHA)
        self.image.fill((0,0,0,0))

        # --- Draw star --- (same as before)
        center_x, center_y = self.size // 2, self.size // 2
        radius_outer = self.size // 2
        radius_inner = int(radius_outer * 0.5)
        num_points = 5
        star_points = []
        for i in range(num_points * 2):
            angle = math.pi / num_points * i - math.pi / 2
            radius = radius_outer if i % 2 == 0 else radius_inner
            px = center_x + radius * math.cos(angle)
            py = center_y + radius * math.sin(angle)
            star_points.append((px, py))
        pygame.draw.polygon(self.image, YELLOW, star_points)
        # --- End star ---

        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_time = spawn_time # Store when it was spawned

    def update(self, current_time): # Needs current_time to check lifespan
        if current_time - self.spawn_time > POWERUP_LIFESPAN:
            print(f"{self.type} powerup timed out.") # Debug
            self.kill() # Remove if lifespan exceeded

# --- NEW: Health Restore Power-up Class ---
class HealthRestore(pygame.sprite.Sprite):
    def __init__(self, x, y, spawn_time): # Added spawn_time
        super().__init__()
        self.type = 'health' # Identify the type
        self.size = POWERUP_SIZE
        self.image = pygame.Surface([self.size, self.size], pygame.SRCALPHA)
        self.image.fill((0,0,0,0))

        # --- Draw a simple cross ---
        bar_width = self.size // 5
        bar_length = self.size - 2 # Make slightly smaller than surface
        # Horizontal bar
        pygame.draw.rect(self.image, HEALTH_CROSS_COLOR,
                         [1, self.size // 2 - bar_width // 2, bar_length, bar_width], border_radius=1)
        # Vertical bar
        pygame.draw.rect(self.image, HEALTH_CROSS_COLOR,
                         [self.size // 2 - bar_width // 2, 1, bar_width, bar_length], border_radius=1)
        # --- End cross ---

        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_time = spawn_time # Store when it was spawned

    def update(self, current_time): # Needs current_time to check lifespan
        if current_time - self.spawn_time > POWERUP_LIFESPAN:
            print(f"{self.type} powerup timed out.") # Debug
            self.kill() # Remove if lifespan exceeded

# --- Helper function to spawn Powerup --- (Renamed from spawn_star)
def spawn_powerup(current_time, all_sprites_group, powerups_group, walls_group, player_sprite):
    # Randomly choose which powerup to spawn
    PowerupClass = random.choice([AmmoRefill, HealthRestore])

    spawn_attempts = 0
    while spawn_attempts < 100:
        spawn_attempts += 1
        x = random.randint(BORDER_THICKNESS + POWERUP_SIZE, SCREEN_WIDTH - BORDER_THICKNESS - POWERUP_SIZE)
        y = random.randint(BORDER_THICKNESS + POWERUP_SIZE, SCREEN_HEIGHT - BORDER_THICKNESS - POWERUP_SIZE)

        # Create temporary powerup for collision checks
        # We pass current_time now because the constructors need it
        temp_powerup = PowerupClass(x, y, current_time)

        if not pygame.sprite.spritecollide(temp_powerup, walls_group, False):
            # Check collision with player using the passed player_sprite reference
            if not (player_sprite and temp_powerup.rect.colliderect(player_sprite.rect.inflate(PLAYER_SIZE, PLAYER_SIZE))):
                 # Add the real powerup
                 all_sprites_group.add(temp_powerup)
                 powerups_group.add(temp_powerup)
                 print(f"{temp_powerup.type} spawned at ({x},{y})")
                 return True
    print("Warning: Could not find valid spawn location for powerup.")
    return False

# --- Helper function to create explosion particles --- <--- MOVE IT HERE
def create_explosion(center_pos, all_sprites_group, particles_group):
    for _ in range(PARTICLE_COUNT):
        # Pass the groups directly to the Particle constructor
        Particle(center_pos[0], center_pos[1], (all_sprites_group, particles_group))

# --- NEW: Game Setup Function ---
def setup_game():
    print("Setting up new game...") # Debug message
    # --- Sprite Groups ---
    all_sprites = pygame.sprite.Group()
    players = pygame.sprite.GroupSingle()
    enemies = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    particles = pygame.sprite.Group()

    # --- Game Variables ---
    score = 0
    game_over = False
    win = False
    # Timer for the next star spawn
    next_powerup_spawn_time = pygame.time.get_ticks() + 8000 # Spawn first one after 8 seconds

    # --- NEW: Safe Zone & Timer Setup ---
    game_start_time = pygame.time.get_ticks()
    # Calculate a random center, avoiding edges
    padding_x = SCREEN_WIDTH * 0.15
    padding_y = SCREEN_HEIGHT * 0.15
    circle_center_x = random.uniform(padding_x, SCREEN_WIDTH - padding_x)
    circle_center_y = random.uniform(padding_y, SCREEN_HEIGHT - padding_y)
    # Initial radius covers most screen
    screen_diag = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
    circle_start_radius = screen_diag / 2 * CIRCLE_START_RADIUS_FACTOR
    circle_current_radius = circle_start_radius # Start at max
    print(f"Circle center: ({circle_center_x:.0f}, {circle_center_y:.0f}), Start Radius: {circle_start_radius:.0f}") # Debug
    # --- End Safe Zone Setup ---

    # --- Create Boundary Walls ---
    wall_list = [
        Wall(0, 0, SCREEN_WIDTH, BORDER_THICKNESS),
        Wall(0, SCREEN_HEIGHT - BORDER_THICKNESS, SCREEN_WIDTH, BORDER_THICKNESS),
        Wall(0, 0, BORDER_THICKNESS, SCREEN_HEIGHT),
        Wall(SCREEN_WIDTH - BORDER_THICKNESS, 0, BORDER_THICKNESS, SCREEN_HEIGHT)
    ]
    for wall in wall_list:
        all_sprites.add(wall)
        walls.add(wall)

    # --- Create Player ---
    player = Player()
    # Calculate padding based on player size *after* creating player
    BARRIER_PADDING = player.size * BARRIER_PADDING_FACTOR
    PLAYER_START_CLEARANCE = player.size * PLAYER_START_CLEARANCE_FACTOR
    player_start_area = player.rect.inflate(PLAYER_START_CLEARANCE * 2, PLAYER_START_CLEARANCE * 2)

    # --- Generate Random Barriers ---
    for i in range(BARRIER_COUNT):
        attempts = 0
        while attempts < 100:
            attempts += 1
            width = random.randint(MIN_BARRIER_WIDTH, MAX_BARRIER_WIDTH)
            height = random.randint(MIN_BARRIER_HEIGHT, MAX_BARRIER_HEIGHT)
            x = random.randint(BORDER_THICKNESS + BARRIER_PADDING, SCREEN_WIDTH - BORDER_THICKNESS - BARRIER_PADDING - width)
            y = random.randint(BORDER_THICKNESS + BARRIER_PADDING, SCREEN_HEIGHT - BORDER_THICKNESS - BARRIER_PADDING - height)
            temp_rect = pygame.Rect(x, y, width, height)

            if temp_rect.colliderect(player_start_area): continue
            collides_existing = False
            for existing_wall in walls:
                if temp_rect.colliderect(existing_wall.rect.inflate(player.size // 2, player.size // 2)):
                    collides_existing = True
                    break
            if collides_existing: continue

            barrier = Wall(x, y, width, height)
            all_sprites.add(barrier)
            walls.add(barrier)
            break
        if attempts >= 100: print(f"Warning: Could not place barrier {i+1} after 100 attempts.")

    # --- Add Player to Groups (Check spawn safety) ---
    player_collides_spawn = pygame.sprite.spritecollide(player, walls, False)
    if player_collides_spawn:
         print("WARNING: Player spawned inside a barrier! Repositioning slightly.")
         while pygame.sprite.spritecollide(player, walls, False):
             player.rect.x += 5
             if player.rect.right > SCREEN_WIDTH - BORDER_THICKNESS:
                  player.rect.center = player.start_pos # Reset
                  print("ERROR: Could not find clear spawn for player.")
                  break
    players.add(player)
    all_sprites.add(player) # Add player AFTER barriers

    # --- Create Enemies ---
    for _ in range(ENEMY_COUNT):
        spawn_attempts = 0
        while spawn_attempts < 200:
             spawn_attempts += 1
             temp_type = random.choice(list(ENEMY_TYPES.keys()))
             temp_size = ENEMY_TYPES[temp_type]['size']
             x = random.randint(BORDER_THICKNESS + temp_size, SCREEN_WIDTH - BORDER_THICKNESS - temp_size)
             y = random.randint(BORDER_THICKNESS + temp_size, SCREEN_HEIGHT - BORDER_THICKNESS - temp_size)
             enemy = Enemy(x, y, walls)
             if not pygame.sprite.spritecollide(enemy, walls, False) and \
                not enemy.rect.colliderect(player.rect.inflate(player.size * 1.5, player.size * 1.5)):
                     all_sprites.add(enemy)
                     enemies.add(enemy)
                     break
        if spawn_attempts >= 200: print("Warning: Could not place an enemy after 200 attempts.")

    # Return all the necessary items for the game loop
    # Return the new circle and timer variables
    return (all_sprites, players, enemies, player_bullets, enemy_bullets,
            walls, powerups, particles, player, score, game_over, win,
            next_powerup_spawn_time, # Keep existing ones
            game_start_time, circle_center_x, circle_center_y, # Add new ones
            circle_current_radius, circle_start_radius) # Add new ones


# --- Pygame Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tank Mayhem - Restartable")
clock = pygame.time.Clock()
random.seed()

# --- Main Game Control Loop ---
running = True
while running:
    # --- Call setup to get fresh game state ---
    (all_sprites, players, enemies, player_bullets, enemy_bullets,
     walls, powerups, particles, player, score, game_over, win,
     next_powerup_spawn_time,
     # --- Unpack new variables ---
     game_start_time, circle_center_x, circle_center_y,
     circle_current_radius, circle_start_radius # Initial radius needed for lerp
     ) = setup_game()

    # --- Gameplay Loop ---
    game_active = True
    # Variable to track damage tick for circle
    last_circle_damage_time = pygame.time.get_ticks()

    while game_active:
        current_time = pygame.time.get_ticks()

        # --- Calculate Time and Circle Radius ---
        elapsed_time = current_time - game_start_time
        time_remaining = max(0, GAME_DURATION - elapsed_time)
        time_ratio = min(1.0, elapsed_time / GAME_DURATION) # Clamp between 0 and 1

        # Linear interpolation for radius
        circle_current_radius = circle_start_radius + (CIRCLE_END_RADIUS - circle_start_radius) * time_ratio
        circle_current_radius = max(CIRCLE_END_RADIUS, circle_current_radius) # Ensure it doesn't go below min

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_active = False # Exit gameplay loop
                running = False     # Exit main control loop
            if event.type == pygame.MOUSEBUTTONDOWN:
                 if event.button == 1 and player.alive():
                     player.shoot(all_sprites, player_bullets)
            # --- Check for quit/restart keys DURING gameplay? Optional ---
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_ESCAPE: # Example quit key
            #         game_active = False
            #         running = False

        # If running is false due to QUIT event, stop processing this frame
        if not running:
            break

        # --- Input Handling (Continuous Keys) ---
        keys = pygame.key.get_pressed()
        if player.alive():
            if keys[pygame.K_a]: player.move_left()
            if keys[pygame.K_d]: player.move_right()
            if keys[pygame.K_w]: player.move_up()
            if keys[pygame.K_s]: player.move_down()

        # --- Powerup Spawning --- (Use new name and function)
        if not powerups and current_time >= next_powerup_spawn_time:
            # Pass current time and player sprite to spawn function
            if spawn_powerup(current_time, all_sprites, powerups, walls, players.sprite):
                 pass # Spawn successful, timer reset on collection/despawn
            else:
                # If failed to spawn, try again shortly
                next_powerup_spawn_time = current_time + 5000

        # --- Update ---
        # --- Safe Zone Damage Logic ---
        circle_center = pygame.Vector2(circle_center_x, circle_center_y)

        # Check Player
        if player.alive():
            player_pos = pygame.Vector2(player.rect.center)
            distance = player_pos.distance_to(circle_center)
            if distance > circle_current_radius:
                # --- Simplified Damage: Apply small fixed damage per frame outside ---
                player.take_damage(0.05) # Example: 0.05 HP damage per frame outside
                # ---------------------------
                if not player.alive():
                    create_explosion(player.rect.center, all_sprites, particles)
                    game_over = True
                    print("GAME OVER - Player Destroyed by Circle")

        # Check Enemies
        for enemy in enemies:
             enemy_pos = pygame.Vector2(enemy.rect.center)
             distance = enemy_pos.distance_to(circle_center)
             if distance > circle_current_radius:
                 # Kill enemies instantly when outside
                 print(f"Enemy {enemy.type} outside circle. Destroyed.") # Debug
                 create_explosion(enemy.rect.center, all_sprites, particles)
                 enemy.kill() # No score for circle kills
                 
        # Update the player tank
        if player.alive():
            players.update(walls, enemies)

        # Update each enemy tank
        for enemy in enemies:
            enemy.update(all_sprites, enemy_bullets, player.rect, players, enemies)


        # Update bullets and particles
        player_bullets.update()
        enemy_bullets.update()
        particles.update()
        powerups.update(current_time)

        # Note: Walls and AmmoRefills don't have update methods, so they don't need calling.

        # --- Collision Detection ---
        # Player bullets hitting enemies
        enemy_hits = pygame.sprite.groupcollide(player_bullets, enemies, True, False)
        for bullet, enemies_hit_list in enemy_hits.items():
            create_explosion(bullet.rect.center, all_sprites, particles)
            for enemy in enemies_hit_list:
                if enemy.take_damage(bullet.damage):
                    score += enemy.score_value
                    enemy.kill()

        # Enemy bullets hitting player
        if player.alive():
            player_hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
            for bullet in player_hits:
                create_explosion(bullet.rect.center, all_sprites, particles)
                player.take_damage(bullet.damage)
                if not player.alive():
                    create_explosion(player.rect.center, all_sprites, particles)
                    game_over = True # Set game_over flag
                    print("GAME OVER - Player Destroyed")
                    # Don't break here, let the loop finish naturally

        # Bullets hitting walls
        player_wall_hits = pygame.sprite.groupcollide(player_bullets, walls, True, False)
        for bullet, _ in player_wall_hits.items(): create_explosion(bullet.rect.center, all_sprites, particles)
        enemy_wall_hits = pygame.sprite.groupcollide(enemy_bullets, walls, True, False)
        for bullet, _ in enemy_wall_hits.items(): create_explosion(bullet.rect.center, all_sprites, particles)

        # --- Player hitting Powerups --- (Check type)
        if player.alive():
            collected_powerups = pygame.sprite.spritecollide(player, powerups, True) # True kills powerup
            if collected_powerups:
                for powerup in collected_powerups:
                    if powerup.type == 'ammo':
                        player.ammo = PLAYER_MAX_AMMO
                        print(f"Player collected AMMO! Ammo refilled to {player.ammo}")
                    elif powerup.type == 'health':
                        player.health = PLAYER_MAX_HEALTH
                        print(f"Player collected HEALTH! Health restored to {player.health}")

                    # Reset spawn timer regardless of type collected
                    next_powerup_spawn_time = current_time + POWERUP_RESPAWN_TIME
                    # Add score? Optional

        # --- Win/Loss Conditions Check ---
        if not enemies and not win and not game_over: # Check win only if not already ended
            win = True
            print("YOU WIN! - All Enemies Destroyed")

        # Check if time ran out (and player hasn't won or already lost)
        if time_remaining <= 0 and not win and not game_over:
            print("GAME OVER - Time Ran Out!")
            game_over = True
            # Optionally kill player if timer runs out?
            if player.alive():
                 create_explosion(player.rect.center, all_sprites, particles)
                 player.kill()


        # --- Check if game should end this frame ---
        if game_over or win:
            game_active = False # Exit the gameplay loop

        # --- Drawing ---
        screen.fill(GRASS_GREEN)
        all_sprites.draw(screen)

        # --- NEW: Draw Safe Zone Circle ---
        # Use a surface for transparency
        circle_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        current_circle_color = CIRCLE_COLOR
        # Optional: Warning color if player is close to edge
        if player.alive():
            player_dist_from_edge = circle_current_radius - player_pos.distance_to(circle_center)
            if 0 < player_dist_from_edge < PLAYER_SIZE * 3: # If within 3x player size of edge
                 current_circle_color = CIRCLE_WARNING_COLOR

        pygame.draw.circle(circle_surface, current_circle_color,
                           (int(circle_center_x), int(circle_center_y)),
                           int(circle_current_radius), CIRCLE_THICKNESS)
        screen.blit(circle_surface, (0,0))
        # --- End Circle Drawing ---

        # --- Draw UI ---
        draw_text(screen, f"Score: {score}", 24, 15, 15)
        hp_color = WHITE if player.alive() else RED
        draw_text(screen, f"HP: {max(0, player.health):.0f}/{PLAYER_MAX_HEALTH}", 24, 15, 40, hp_color) # Format HP as int
        draw_text(screen, f"Ammo: {player.ammo}/{PLAYER_MAX_AMMO}", 24, 15, 65)

        # Draw Countdown Timer
        minutes = int(time_remaining / 1000 // 60)
        seconds = int(time_remaining / 1000 % 60)
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        time_color = YELLOW if time_remaining < 30000 else WHITE # Yellow warning under 30s
        draw_text(screen, time_text, 24, SCREEN_WIDTH - 150, 15, time_color) # Top-right


        pygame.display.flip()
        clock.tick(60)

    # --- End Screen Loop --- (Only run if game didn't quit during gameplay)
    if running:
        end_font_large = pygame.font.Font(None, 74)
        end_font_small = pygame.font.Font(None, 36)
        restart_text_surf = end_font_small.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
        quit_text_surf = end_font_small.render("Press Q to Quit", True, WHITE)
        quit_rect = quit_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 90))

        final_message_text = ""
        final_message_color = WHITE
        if win:
            final_message_text = "YOU WIN!"
            final_message_color = GREEN
        elif game_over:
            final_message_text = "GAME OVER"
            final_message_color = RED

        if final_message_text:
            final_message_surface = end_font_large.render(final_message_text, True, final_message_color)
            final_message_rect = final_message_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

            # Draw the end screen elements once before the loop
            screen.blit(final_message_surface, final_message_rect)
            screen.blit(restart_text_surf, restart_rect)
            screen.blit(quit_text_surf, quit_rect)
            pygame.display.flip()


        running_end_screen = True
        while running_end_screen and running: # Need to check 'running' too
             for event in pygame.event.get():
                 if event.type == pygame.QUIT:
                     running_end_screen = False
                     running = False # Ensure main loop terminates
                 if event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_r:
                         print("Restarting...")
                         running_end_screen = False # Exit end screen loop, main loop continues
                     if event.key == pygame.K_q:
                         running_end_screen = False
                         running = False # Ensure main loop terminates
             clock.tick(15) # Lower tick rate for end screen

# --- Quit Pygame --- (This runs after the main 'while running:' loop exits)
pygame.quit()
sys.exit()