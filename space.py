import pygame
import os
import math
pygame.init()

SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100

BACKGROUND = pygame.image.load(os.path.join("assets", "background.png"))

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

class Movable:
    def __init__(self, x, y, rotation, velocity, images):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.velocity = velocity
        self.traveled = 0
        self.images = images
        self.rect = pygame.Rect(self.x, self.y, images[0].get_width(), images[0].get_height())
        self.animation_timer = 0
        self.animation_index = 0

    def animate(self):
        self.animation_timer += 1
        if self.animation_timer >= 5:
            self.animation_timer = 0
            self.animation_index += 1
            if self.animation_index >= len(self.images):
                self.animation_index = 0
    
    def draw(self):
        self.animate()
        image = self.images[self.animation_index].convert_alpha()
        rotated_image = pygame.transform.rotate(image, self.rotation)
        self.rect = pygame.Rect(self.x, self.y, rotated_image.get_width(), rotated_image.get_height())
        SCREEN.blit(rotated_image, (self.x, self.y))

    def move(self):
        rot_radians = math.radians(self.rotation)
        dx = math.floor(self.velocity * math.cos(rot_radians))
        dy = math.floor(self.velocity * math.sin(rot_radians))
        self.x += dx
        self.y -= dy
        if ( self.x < 0 ):
            self.x = SCREEN_WIDTH
        if ( self.y < 0 ):
            self.y = SCREEN_HEIGHT
        if ( self.x > SCREEN_WIDTH ):
            self.x = 0
        if ( self.y > SCREEN_HEIGHT ):
            self.y = 0
        self.traveled += self.velocity

    def collidesWith(self, movable):
        return self.rect.colliderect(movable.rect)

class Laser(Movable):
    def __init__(self, x, y, rotation):
        image = pygame.image.load(os.path.join("assets", "laserB.png"))
        Movable.__init__(self, x, y, rotation, 35, [image])
        self.ttl = 600        
    
    def still_alive(self):
        return self.traveled < self.ttl    

class Asteroid(Movable):
    def __init__(self, x, y, rotation, velocity, size):
        image = None
        if size == 3:
            image = pygame.image.load(os.path.join("assets", "bigrock.png"))
        elif size == 2:
            image = pygame.image.load(os.path.join("assets", "rock.png"))
        elif size == 1:
            image = pygame.image.load(os.path.join("assets", "smallrock.png"))
        
        self.size = size
        
        Movable.__init__(self, x, y, rotation, velocity, [image])

    def spawn_children(self, laser):
        if self.size == 1:
            return None, None, None
        
        rotation1 = laser.rotation
        rotation2 = laser.rotation - 45
        if rotation2 < 0:
            rotation2 += 360
        rotation3 = laser.rotation + 45
        if rotation3 >= 360:
            rotation3 -= 360
        
        cx = self.images[0].get_width() // 2
        cy = self.images[0].get_height() // 2
        return (
            Asteroid(self.x - cx, self.y, rotation1, self.velocity, self.size-1),
            Asteroid(self.x, self.y - cy, rotation2, self.velocity, self.size-1),
            Asteroid(self.x + cx, self.y, rotation3, self.velocity, self.size-1)
        )
            
class Explosion(Movable):
    def __init__(self, x, y):
        images = [
            pygame.image.load(os.path.join("assets", "explosion1.png")),
            pygame.image.load(os.path.join("assets", "explosion2.png")),
            pygame.image.load(os.path.join("assets", "explosion3.png"))
        ]
        Movable.__init__(self, x, y, 0, 0, images)
        self.ttl = 15
        self.been_alive = 0

    def draw(self):
        self.been_alive += 1
        return Movable.draw(self)

    def still_alive(self):
        return self.ttl > self.been_alive

class Ship(Movable):
    def __init__(self):
        self.image_still = pygame.image.load(os.path.join("assets", "ship.png"))
        self.image_accel = pygame.image.load(os.path.join("assets", "ship_fire.png"))
        Movable.__init__(self, 550, 300, 0, 0, [self.image_still])

    def input(self, user_input):
        if user_input[pygame.K_RIGHT]:
            self.rotation -= 5
            if self.rotation < 0:
                self.rotation = 360 + self.rotation
        
        if user_input[pygame.K_LEFT]:
            self.rotation += 5
            if self.rotation >= 360:
                self.rotation = self.rotation - 360

        if user_input[pygame.K_UP]:
            self.images = [self.image_accel]
            self.velocity += 1
            if self.velocity > 20:
                self.velocity = 20
        else:
            self.images = [self.image_still]
        
        if user_input[pygame.K_DOWN]:
            self.velocity -= 1
            if self.velocity < -7:
                self.velocity = -7

if __name__=="__main__":
    clock = pygame.time.Clock()
    
    ship = Ship()
    lasers = []
    explosions = []
    asteroids = [Asteroid(50,50,10,5,3), Asteroid(50,150,210,6,3)]

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    new_laser = Laser(ship.x + 20, ship.y + 20, ship.rotation)
                    lasers.append(new_laser)

        user_input = pygame.key.get_pressed()
        ship.input(user_input)

        ship.move()

        # draw background
        SCREEN.blit(BACKGROUND, (0,0))
        
        # draw ship
        ship.draw()

        # draw lasers
        for laser in lasers:
            laser.draw()
            laser.move()
            if not laser.still_alive():
                lasers.remove(laser)
        
        # draw explosions
        for explosion in explosions:
            explosion.draw()
            if not explosion.still_alive():
                explosions.remove(explosion)

        # draw and move asteroids
        for i, asteroid in enumerate(asteroids):
            asteroid.draw()
            asteroid.move()
            
            # action for laser hitting asteroid
            for laser in lasers:
                if asteroid.collidesWith(laser):
                    lasers.remove(laser)
                    asteroids.remove(asteroid)

                    explosions.append(Explosion(asteroid.x, asteroid.y))
                    
                    child1, child2, child3 = asteroid.spawn_children(laser)
                    if child1 != None:
                        asteroids.extend( [child1, child2, child3] )

            # check if asteroid collides with ship
            if asteroid.collidesWith(ship):
                explosions.append(Explosion(ship.x, ship.y))

            
            # check if asteroid collides with another asteroid
            for j, asteroid2 in enumerate(asteroids):
                if i != j and asteroid.collidesWith(asteroid2):
                    opp = asteroid.y - asteroid2.y
                    adj = asteroid.x - asteroid2.x
                    
                    impact_angle = 0
                    if adj != 0:
                        impact_angle = math.floor(math.degrees(math.atan2(opp, adj)))

                    asteroid.rotation = -impact_angle + 360
                    asteroid2.rotation = impact_angle 
                    asteroid.move()
                    asteroid2.move()

        clock.tick(30)
        pygame.display.update()