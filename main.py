import pygame, os

from os import listdir
from os.path import isfile, join

pygame.init()
pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 960, 620
FPS = 60
PLAYER_VEL = 5
PATH = os.path.abspath('.') + '/'
font_path = pygame.font.match_font('comicsansms')

window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)


# Ensure all paths are correct
def check_path_exists(path):
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
    else:
        print(f"Path exists: {path}")


check_path_exists(PATH)
check_path_exists(join(PATH, "assets", "Terrain", "Terrain.png"))
check_path_exists(join(PATH, "assets", "Background", "Blue.png"))
check_path_exists(join(PATH, "assets", "Home", "exit.png"))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join(PATH, "assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join(PATH, "assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


def get_background(name):
    image = pygame.image.load(join(PATH, "assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    def reset(self):
        self.rect.x = 100
        self.rect.y = 100
        self.x_vel = 0
        self.y_vel = 0
        self.hit = False
        self.hit_count = 0
        self.jump_count = 0
        self.direction = "right"
        self.animation_count = 0

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if isinstance(obj, Exit):
            game_won = True
            show_win_screen(window)
            run = False
            pygame.quit()
            quit()

        if obj and obj.name == "fire":
            player.make_hit()


def show_home_screen(window):
    window.fill((0, 0, 0))  # Fill the screen with black color
    font = pygame.font.Font(font_path, 74)
    text = font.render("Game Over", True, (255, 0, 0))
    window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

    font = pygame.font.Font(font_path, 36)
    text = font.render("Press any key to go home", True, (255, 255, 255))
    window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + text.get_height()))

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                waiting = False


def show_win_screen(window):
    window.fill((0, 0, 0))  # Fill the screen with black color
    font = pygame.font.Font(font_path, 74)
    text = font.render("Hope you had fun!", True, (255, 255, 0))
    window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                waiting = False


def draw_lives(window, lives):
    font = pygame.font.Font(font_path, 36)
    lives_text = font.render(f'Lives: {lives}', True, (255, 0, 0))
    window.blit(lives_text, (10, 10))


def load_exit_image():
    exit_image = pygame.image.load(join(PATH, "assets", "Home", "exit.png")).convert_alpha()
    return pygame.transform.scale2x(exit_image)


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_exit_image()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, window, offset_x):
        window.blit(self.image, (self.rect.x - offset_x, self.rect.y))


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")
    block_size = 96
    player = Player(100, 100, 50, 50)

    # Define positions for multiple blocks on the ground and in the air
    block_positions = [
                          (block_size * i, HEIGHT - block_size) for i in range(20)
                      ] + [
                          (0, HEIGHT - block_size * 2),
                          (block_size * 3, HEIGHT - block_size * 4),
                          (block_size * 5, HEIGHT - block_size * 6),
                          (block_size * 7, HEIGHT - block_size * 3),
                          (block_size * 10, HEIGHT - block_size * 5),
                          (block_size * 12, HEIGHT - block_size * 2),
                          (block_size * 14, HEIGHT - block_size * 4),
                          (block_size * 16, HEIGHT - block_size * 3),
                          (block_size * 18, HEIGHT - block_size * 6)
                      ]

    # Create block objects from the defined positions
    blocks = [Block(x, y, block_size) for x, y in block_positions]

    # Define positions for fire objects (on the ground)
    fire_positions = [
        (block_size * 4, HEIGHT - block_size - 64),
        (block_size * 8, HEIGHT - block_size - 64),
        (block_size * 15, HEIGHT - block_size - 64),
        (block_size * 17, HEIGHT - block_size - 64),
    ]

    # Create fire objects from the defined positions
    fires = [Fire(x, y, 16, 32) for x, y in fire_positions]

    for fire in fires:
        fire.on()

    # Define the floor
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]

    # Define exit position and create exit object
    exit_position = (block_size * 19, HEIGHT - block_size * 2)
    exit = Exit(*exit_position)

    # Combine all objects
    objects = [*floor, *blocks, *fires, exit]

    offset_x = 0
    scroll_area_width = 200

    difficulty = 1  # Start with difficulty level 1
    lives = 3  # Player starts with 3 lives

    run = True
    game_won = False

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        for fire in fires:
            fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)
        draw_lives(window, lives)  # Draw the lives counter

        # Check for collisions with fire and handle player death
        if player.hit:
            lives -= 1
            if lives > 0:
                player.reset()
                offset_x = 0  # Reset scrolling
            else:
                # Game over, show home screen
                show_home_screen(window)
                run = False
                break

        # Check if the player has reached the exit
        if pygame.sprite.collide_mask(player, exit):
            game_won = True
            show_win_screen(window)
            run = False
            break

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        # Increase difficulty based on player's position
        if player.rect.x > WIDTH * difficulty:
            difficulty += 1
            # Add more blocks and fires as difficulty increases
            new_block_position = (block_size * (18 + difficulty * 2), HEIGHT - block_size * (2 + difficulty))
            blocks.append(Block(*new_block_position, block_size))
            if difficulty % 2 == 0:
                new_fire_position = (block_size * (20 + difficulty * 2), HEIGHT - block_size - 64)
                new_fire = Fire(*new_fire_position, 16, 32)
                new_fire.on()
                fires.append(new_fire)
                objects.append(new_fire)
            objects.append(blocks[-1])

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
