import pygame, sys
import os
import asyncio
import random
from os import listdir
from os.path import isfile, join
import math
pygame.font.init()

pygame.init()

pygame.display.set_caption("HAMSTER ADVENTURE 1")

FPS = 60
PLAYER_VEL = 5
HEIGHT = 800
WIDTH = 1200
window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction = False):
    path = join("sprite", dir1, dir2)
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
            all_sprites[image.replace(".png", "") + "_right"] = flip(sprites)
            all_sprites[image.replace(".png", "") + "_left"] = sprites
        else:
            all_sprites[image.replace(".png", "")] = sprites
    return all_sprites

def get_block(size):
    path = join("background", "terrain", "map.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size,size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0,0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255,0,0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("idle animation", "mc", 50, 35, True)
    ANIMATION_DELAY = 5

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "right"  
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.win = False
        self.hit_count = 0
        self.win_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 10
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
        
    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def make_win(self):
        self.win = True
        self.win_count = 0

    def move(self,dx,dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self,vel):
        self.x_vel = -vel 
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self,vel):
        self.x_vel = vel 
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        
        if self.hit:
            self.hit_count += 70
        if self.hit_count > 60:
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
        self.y_vel = 0
        

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.win_count >= 1:
            sprite_sheet = "hamwin"
        if self.hit:
            sprite_sheet = "hit"
        if self.y_vel < 0:
            sprite_sheet = "jumpalt"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "walk"
    
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self,win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self,win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.block = load_sprite_sheets('objects','terrain', width, height)
        self.image = self.block ['tile grass'][0]
        self.mask = pygame.mask.from_surface(self.image)


class Trap(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "trap")
        self.trap = load_sprite_sheets("objects", "Traps", width, height)
        self.image = self.trap ["trap"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "trap"

    def on(self):
        self.animation_name = "trap"   

    def off(self):
        self.animation_name = "trap"    

    def loop(self):
       
        sprites = self.trap [self.animation_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Portal(Object):
    ANIMATION_DELAY = 3
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "portal")
        self.portal = load_sprite_sheets("objects", "Nuts", width, height)
        self.image = self.portal ["win2"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "win2"    

    def loop(self):
        sprites = self.portal [self.animation_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

def get_background(name):
    image = pygame.image.load(join("background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = [i * width, j * height]
            tiles.append(pos)

    return tiles, image
        

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_rect(player, obj):
            collided_object = obj
            break
    player.move(-dx,0)
    player.update()
    return collided_object   

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_rect(player, obj):
            if dy > 0 and player.rect.top != obj.rect.bottom:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0 and player.rect.bottom != obj.rect.top:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            collided_objects.append(obj)
    return collided_objects

class Health_bar():
    def __init__(self, x, y, w, h, max_hp):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = max_hp
        self.max_hp = max_hp
    def draw(self, win):
        ratio = self.hp / self.max_hp
        pygame.draw.rect(win, "red", (self.x, self.y, self.w, self.h))
        pygame.draw.rect(win, "green", (self.x, self.y, self.w * ratio, self.h))
 
def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
    if keys[pygame.K_SPACE] and player.jump_count < 15:
        player.jump()

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "trap":
            player.make_hit()
        if obj and obj.name == "portal":
            player.make_win()
            player.win_count += 1


class Floor(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)


async def main():
    clock = pygame.time.Clock()
    background, bg_image = get_background ("tile start screen.png")
    block_size = 64
    path = join("grand9k_pixel/Grand9K Pixel.ttf")
    font = pygame.font.SysFont(path, 30, bold=False, italic=False)

    def draw(window, background, bg_image, player, objects, offset_x):
        for tile in background:
            window.blit(bg_image, tile)
        for obj in objects:
            obj.draw(window, offset_x)

        player.draw(window, offset_x)

    pygame.display.update()
    lost = False
    win = False
    player = Player(100,100, 50,35)
    health_bar = Health_bar (10, 10, 200, 40, 100)
    portal = Portal(100, HEIGHT - block_size *3.31, 32, 32)
    trap = Trap(100, HEIGHT - block_size * 3.8, 32, 32)
    #trap.on()
    floor = [Floor(-100, 650, 100)]
    
    objects = [*floor,
               #left wall            
               #upper terrain
               Block(block_size * 1, HEIGHT - block_size * 6, 32, 32),
               Block(block_size * 2, HEIGHT - block_size * 6, 32, 64),
               

               Block(block_size * 4, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 5, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 6, HEIGHT - block_size * 8, 32, 32),

               Block(block_size * 9, HEIGHT - block_size * 12, 32, 32),
               
               Block(block_size * 13, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 14, HEIGHT - block_size * 8, 32, 64),
               Trap(block_size * 13, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 17, HEIGHT - block_size * 7, 32, 32),
               Block(block_size * 18, HEIGHT - block_size * 7, 32, 32),
               
               Block(block_size * 21, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 22, HEIGHT - block_size * 9, 32, 64),
               Trap(block_size * 22, HEIGHT - block_size * 9.5, 32, 32),
               Block(block_size * 22, HEIGHT - block_size * 7, 32, 64),

               Block(block_size * 24, HEIGHT - block_size * 6, 32, 64),
               Block(block_size * 25, HEIGHT - block_size * 7, 32, 32),
               Block(block_size * 26, HEIGHT - block_size * 6, 32, 32),

               Block(block_size * 29, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 30, HEIGHT - block_size * 8, 32, 64),
               Trap(block_size * 29, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 35, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 36, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 38, HEIGHT - block_size * 8, 32, 32),
               
               Block(block_size * 40, HEIGHT - block_size * 12, 32, 32),
               Trap(block_size * 40, HEIGHT - block_size * 12.5, 32, 32),
               Block(block_size * 41, HEIGHT - block_size * 12, 32, 32),
               Trap(block_size * 41, HEIGHT - block_size * 12.5, 32, 32),
               Block(block_size * 42, HEIGHT - block_size * 13, 32, 32),

               Block(block_size * 40, HEIGHT - block_size * 8, 32, 32),
               Trap(block_size * 41, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 41, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 42, HEIGHT - block_size * 8, 32, 32),


               Block(block_size * 45, HEIGHT - block_size * 7, 32, 32),
               Block(block_size * 46, HEIGHT - block_size * 7, 32, 32),
               Block(block_size * 47, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 47, HEIGHT - block_size * 7.5, 32, 32),

               Block(block_size * 50, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 51, HEIGHT - block_size * 8, 32, 64),
               Trap(block_size * 51, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 54, HEIGHT - block_size * 8, 32, 32),

               Block(block_size * 57, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 58, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 58, HEIGHT - block_size * 7, 32, 64),
               Trap(block_size * 59, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 59, HEIGHT - block_size * 8, 32, 32),

               Block(block_size * 63, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 64, HEIGHT - block_size * 8, 32, 64),
               Trap(block_size * 64, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 65, HEIGHT - block_size * 8, 32, 32),
               Trap(block_size * 65, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 66, HEIGHT - block_size * 8, 32, 32),

               Block(block_size * 63, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 64, HEIGHT - block_size * 9, 32, 64),
               Trap(block_size * 64, HEIGHT - block_size * 9.5, 32, 32),
               Block(block_size * 65, HEIGHT - block_size * 8, 32, 32),
               Trap(block_size * 65, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 66, HEIGHT - block_size * 9, 32, 32),

               Block(block_size * 70, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 71, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 71, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 72, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 72, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 73, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 73, HEIGHT - block_size * 7, 32, 32),
               
               Block(block_size * 76, HEIGHT - block_size * 6, 32, 32),
               Block(block_size * 77, HEIGHT - block_size * 6, 32, 32),

               Block(block_size * 80, HEIGHT - block_size * 10, 32, 32),
               Block(block_size * 81, HEIGHT - block_size * 10, 32, 64),
               Trap(block_size * 81, HEIGHT - block_size * 10.5, 32, 32),
             
               Block(block_size * 84, HEIGHT - block_size * 9, 32, 32),
               Block(block_size * 85, HEIGHT - block_size * 9, 32, 32),
               Block(block_size * 86, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 87, HEIGHT - block_size * 8, 32, 32),
              


               Block(block_size * 94, HEIGHT - block_size * 9, 32, 32),
               Block(block_size * 95, HEIGHT - block_size * 9, 32, 32),
               Block(block_size * 96, HEIGHT - block_size * 9, 32, 32),
               Block(block_size * 97, HEIGHT - block_size * 9, 32, 32),
               Block(block_size * 98, HEIGHT - block_size * 9, 32, 32),



               Block(block_size * 100, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 101, HEIGHT - block_size * 8.5, 32, 64),
               Trap(block_size * 101, HEIGHT - block_size * 9, 32, 32),

               Block(block_size * 104, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 105, HEIGHT - block_size * 7.5, 32, 32),

               Block(block_size * 108, HEIGHT - block_size * 7, 32, 32),
               Block(block_size * 110, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 110, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 112, HEIGHT - block_size * 7, 32, 32),
               Trap(block_size * 112, HEIGHT - block_size * 7.5, 32, 32),
               Block(block_size * 114, HEIGHT - block_size * 7, 32, 32),
               Block(block_size * 116, HEIGHT - block_size * 7, 32, 32),


               Block(block_size * 119, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 120, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 121, HEIGHT - block_size * 8 ,32, 32),
               Block(block_size * 122, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 123, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 124, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 125, HEIGHT - block_size * 8, 32, 32),
               Trap(block_size * 119, HEIGHT - block_size * 10, 32, 32),

               Block(block_size * 127, HEIGHT - block_size * 8, 32, 32),
               Trap(block_size * 128, HEIGHT - block_size * 8.5, 32, 32),
               Block(block_size * 128, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 129, HEIGHT - block_size * 8, 32, 32),
               Trap(block_size * 129, HEIGHT - block_size * 8.5, 32, 32),


               Trap(block_size * 130, HEIGHT - block_size * 2.84, 32, 32),
               Trap(block_size * 132, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 130, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 131, HEIGHT - block_size * 8, 32, 64),
               Block(block_size * 132, HEIGHT - block_size * 8, 32, 32),
               Block(block_size * 134, HEIGHT - block_size * 5, 32, 32),
               

                #ground     y= HEIGHT - BLOCKSIZE - 2.84 or 2.35       
               Trap(block_size * 5, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 5, HEIGHT - block_size * 2.35, 32, 32),
               Trap(block_size * 6, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 6, HEIGHT - block_size * 2.35, 32, 32),
               

               Block(block_size * 13, HEIGHT - block_size * 3.31, 32, 32),
               Trap(block_size * 12, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 12, HEIGHT - block_size * 2.35, 32, 32),
               
             
               Block(block_size * 17, HEIGHT - block_size * 2.35, 32, 32),
               

               Block(block_size * 24, HEIGHT - block_size * 3.31, 32, 32),
               Trap(block_size * 25, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 25, HEIGHT - block_size * 2.35, 32, 32),
               Block(block_size * 28, HEIGHT - block_size * 3.31, 32, 32),

               

               Block(block_size * 32, HEIGHT - block_size * 3, 32, 32),
               Block(block_size * 33, HEIGHT - block_size * 3, 32, 32),
               Block(block_size * 34, HEIGHT - block_size * 3, 32, 32),
               Block(block_size * 35, HEIGHT - block_size * 3, 32, 32),

               

               Block(block_size * 45, HEIGHT - block_size * 2, 32, 32),
               Block(block_size * 46, HEIGHT - block_size * 2, 32, 32),
               Block(block_size * 47, HEIGHT - block_size * 2, 32, 32),
               Block(block_size * 48, HEIGHT - block_size * 2, 32, 32),

               Block(block_size * 51, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 52, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 53, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 54, HEIGHT - block_size * 3.31, 32, 32),
               Trap(block_size * 53, HEIGHT - block_size * 3.8, 32, 32),

               Block(block_size * 73, HEIGHT - block_size * 3.31, 32, 32),
               Trap(block_size * 74, HEIGHT - block_size * 2.84, 32, 32),
               Trap(block_size * 76, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 74, HEIGHT - block_size * 2.35, 32, 32),
               Block(block_size * 76, HEIGHT - block_size * 2.35, 32, 32),
               Block(block_size * 75, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 77, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 78, HEIGHT - block_size * 3.31, 32, 32),

               Block(block_size * 80, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 81, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 82, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 83, HEIGHT - block_size * 3.31, 32, 32),

               Block(block_size * 87, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 88, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 90, HEIGHT - block_size * 4.31, 32, 32),
               Block(block_size * 92, HEIGHT - block_size * 4.31, 32, 32),


               

               Block(block_size * 110, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 111, HEIGHT - block_size * 3.31, 32, 32),
               Block(block_size * 112, HEIGHT - block_size * 4.31, 32, 32),
               Block(block_size * 113, HEIGHT - block_size * 4.31, 32, 32),

               
               Trap(block_size * 130, HEIGHT - block_size * 2.84, 32, 32),
               Block(block_size * 130, HEIGHT - block_size * 2.35, 32, 32),
               Block(block_size * 131, HEIGHT - block_size * 4.31, 32, 32),
               Block(block_size * 132, HEIGHT - block_size * 4.31, 32, 32),

               #136
               Portal(block_size * 136, HEIGHT - block_size * 5, 64, 64),

               
               #inviwall to prevent clip thru map
               #
               
                ]
    
    #implement the [] map layout here prob

    offset_x = 0
    offset_y = 0
    scroll_area_width = 420
    scroll_area_height= 792

    run = True
    while run:
        pygame.display.update()

        clock.tick(FPS)
        if player.hit:
            player.hit_count += 1
            if player.direction == "left":
                player.x_vel +=  60
            if player.direction == "right":
                player.x_vel -= 35
            health_bar.hp -= 10
            #PLES FIX THIS SHIT WTF

        if health_bar.hp <= 0:
            lost = True
        if player.win_count >= 1:
            win = True
        #fall dmg
        if player.y_vel >= player.GRAVITY *40:
            health_bar.hp -= 1000

        if win:
            win_label = font.render(f"YOU WIN! (pls press R to replay sowwy >~<)", 1, (255,0,0))
            window.blit(win_label, (WIDTH/2 - win_label.get_width()/2, 350))
            pygame.display.update()

        if lost:
            lost_label = font.render(f"YOU DIED! (press R to restart >~<)", 1, (255,0,0))
            window.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))
            player.x_vel= 100
            player.y_vel = 100
            player.rect.x = 100
            player.rect.y = 100
            pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                run = True        
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r and {lost or win}:
                    player = Player(100,100,50,35)
                    lost = False
                    win = False
                    player.win_count = 0
                    health_bar.hp = health_bar.max_hp
                    scroll_area_width = 350
                    scroll_area_height = -10
                    offset_x = 0
                    offset_y = 0

        player.loop(FPS)
        trap.loop()
        portal.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)
        
        health_bar.draw(window)
        #window.blit(level_label, (WIDTH - level_label.get_width()- 10, 10))
        window.blit(window, (0,0))
        pygame.display.update()

        if((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
            (player.rect.left - offset_x <= scroll_area_width) and player.x_vel <0):
            offset_x += player.x_vel

        if((player.rect.top - offset_y >= HEIGHT - scroll_area_height) and player.y_vel > 0) or (
            (player.rect.bottom - offset_y <= scroll_area_height) and player.y_vel <0):
            offset_y += player.y_vel
                #python -m pygbag main.py
        await asyncio.sleep(0)
asyncio.run(main())