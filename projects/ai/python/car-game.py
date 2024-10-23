import pygame
import random
import time
import sys
import threading
import mediapipe as mp
import cv2

# Initialize pygame
pygame.init()

# Constants for screen size (fullscreen mode)
SCREEN_INFO = pygame.display.Info()  # Get display screen info
SCREEN_WIDTH = SCREEN_INFO.current_w  # Get screen width
SCREEN_HEIGHT = SCREEN_INFO.current_h  # Get screen height
ROAD_WIDTH = int(SCREEN_WIDTH * 0.8)  # Increase road width to 80% of the screen width
CAR_WIDTH = 50
CAR_HEIGHT = 100
FPS = 60
FINISH_TIME = 200  # Increased finish time to 200 seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Load assets
CAR_IMAGE = pygame.image.load('car.jpg')  # Your car image here
OBSTACLE_IMAGE = pygame.image.load('obstacle.jpg')  # Other cars/obstacles image
pygame.mixer.init()
NICE_SOUND = pygame.mixer.Sound('nice.mp3')  # Sound file for "Nice" message

# Initialize screen in fullscreen mode
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Car Game")

# Create clock for FPS
clock = pygame.time.Clock()

# Mediapipe pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Global variables for controlling the car
move_left = False
move_right = False
game_over_flag = False

def draw_road():
    # Adjust tree/rock width by reducing it further
    tree_area_width = (SCREEN_WIDTH - ROAD_WIDTH) // 2

    # Road in the middle
    road_rect = pygame.Rect((SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, ROAD_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, GRAY, road_rect)

    # Grass and trees/rocks on both sides (reduced width)
    pygame.draw.rect(screen, GREEN, pygame.Rect(0, 0, tree_area_width, SCREEN_HEIGHT))
    pygame.draw.rect(screen, GREEN, pygame.Rect(SCREEN_WIDTH - tree_area_width, 0, tree_area_width, SCREEN_HEIGHT))

    # Add random trees/rocks in the smaller area
    for i in range(10):
        tree_x = random.choice([random.randint(10, tree_area_width - 10), random.randint(SCREEN_WIDTH - tree_area_width + 10, SCREEN_WIDTH - 10)])
        tree_y = random.randint(0, SCREEN_HEIGHT)
        pygame.draw.circle(screen, BLACK, (tree_x, tree_y), random.randint(15, 25))

class Car:
    def __init__(self):
        self.image = pygame.transform.scale(CAR_IMAGE, (CAR_WIDTH, CAR_HEIGHT))
        self.x = (SCREEN_WIDTH - CAR_WIDTH) // 2
        self.y = SCREEN_HEIGHT - CAR_HEIGHT - 10
        self.speed = 10
        self.lateral_speed = self.speed / 3

    def move(self, dx):
        self.x += dx * self.lateral_speed  
        self.x = max((SCREEN_WIDTH - ROAD_WIDTH) // 2, min(self.x, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH))

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

class Obstacle:
    def __init__(self, speed_factor):
        self.image = pygame.transform.scale(OBSTACLE_IMAGE, (CAR_WIDTH, CAR_HEIGHT))
        self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)
        self.y = -CAR_HEIGHT
        self.crossed = False  

        base_speed = 1  
        self.speed = base_speed * (speed_factor + 1)

    def move(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.crossed = True  
            self.y = -CAR_HEIGHT
            self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def check_collision(self, car):
        car_rect = pygame.Rect(car.x, car.y, CAR_WIDTH, CAR_HEIGHT)
        obstacle_rect = pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)
        return car_rect.colliderect(obstacle_rect)

def draw_close_button():
    button_size = 60
    button_padding = 30
    button_x = button_padding
    button_y = button_padding
    
    # Draw the button rectangle and 'X'
    pygame.draw.rect(screen, RED, (button_x, button_y, button_size, button_size))
    
    line_padding = 5
    
    # Draw 'X' lines on the button to indicate close functionality.
    pygame.draw.line(screen,
                     WHITE,
                     (button_x + line_padding,
                      button_y + line_padding),
                     (button_x + button_size - line_padding,
                      button_y + button_size - line_padding),
                     width=2)
    
    pygame.draw.line(screen,
                     WHITE,
                     (button_x + button_size - line_padding,
                      button_y + line_padding),
                     (button_x + line_padding,
                      button_y + button_size - line_padding),
                     width=2)
    
    return pygame.Rect(button_x,
                       button_y,
                       button_size,
                       button_size)

def game_loop(speed_level):
    global move_left, move_right, game_over_flag

    car = Car()
    score = 0
    num_obstacles = 5
    obstacles = [Obstacle(speed_level) for _ in range(num_obstacles)]
    start_time = time.time()
    finished_without_collision = False
    collision_effect_time = 0
    last_collided_obstacle = None
    
    while not game_over_flag:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over_flag = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if close_button_rect.collidepoint(event.pos):
                    game_over_flag = True
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or move_left:
            car.move(-1)  
        if keys[pygame.K_RIGHT] or move_right:
            car.move(1)  

        draw_road()
        car.draw()

        collision_occurred = False
        for obstacle in obstacles:
            obstacle.move()
            obstacle.draw()

            if obstacle.check_collision(car):
                collision_occurred = True
                collision_effect_time = pygame.time.get_ticks()
                last_collided_obstacle = obstacle
                score = max(score - 1, 0)
            if obstacle.crossed:
                if not collision_occurred:
                    score += 1
                obstacle.crossed = False

        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, 10))

        if time.time() - start_time > FINISH_TIME:
            game_over_flag = True
            finished_without_collision = True

        close_button_rect = draw_close_button()
        pygame.display.update()
        clock.tick(FPS)

    if finished_without_collision:
        screen.fill(GREEN)
        font = pygame.font.SysFont(None, 72)
        win_text = font.render("You Win!", True, WHITE)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - win_text.get_height() // 2))
        pygame.display.update()
        time.sleep(3)

    pygame.quit()

def detect_human_movement(video_file=None):
    global move_left, move_right, game_over_flag

    cap = cv2.VideoCapture(video_file if video_file else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_skip = 5
    frame_count = 0
    
    while cap.isOpened() and not game_over_flag:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x

            if left_shoulder < 0.4:
                move_left = True
                move_right = False
            elif right_shoulder > 0.6:
                move_left = False
                move_right = True
            else:
                move_left = False
                move_right = False

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed_level", type=int, choices=range(1, 6), required=True, help="Set the speed level (1-5)")
    parser.add_argument("--video", type=str, help="Path to the optional video file")
    
    args = parser.parse_args()
    
    speed_level = args.speed_level
    video_file = args.video

    human_thread = threading.Thread(target=detect_human_movement, args=(video_file,))
    
    human_thread.start()
    
    game_loop(speed_level)
    
    human_thread.join()
    
    sys.exit()
