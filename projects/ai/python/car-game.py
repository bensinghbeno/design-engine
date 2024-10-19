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
        self.lateral_speed = self.speed / 3  # Slower by 3 times when moving left-right

    def move(self, dx):
        self.x += dx * self.lateral_speed  # Apply lateral speed adjustment
        # Boundary check
        self.x = max((SCREEN_WIDTH - ROAD_WIDTH) // 2, min(self.x, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH))

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

class Obstacle:
    def __init__(self, speed_factor):
        self.image = pygame.transform.scale(OBSTACLE_IMAGE, (CAR_WIDTH, CAR_HEIGHT))
        self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)
        self.y = -CAR_HEIGHT
        self.crossed = False  # Track if the obstacle has crossed

        base_speed = 1  # Base speed for level 0
        self.speed = base_speed * (speed_factor + 1)

    def move(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.crossed = True  # Mark as crossed when it goes off screen
            self.y = -CAR_HEIGHT
            self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def check_collision(self, car):
        car_rect = pygame.Rect(car.x, car.y, CAR_WIDTH, CAR_HEIGHT)
        obstacle_rect = pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)
        return car_rect.colliderect(obstacle_rect)

def game_over():
    font = pygame.font.SysFont(None, 75)
    game_over_text = font.render('GAME OVER', True, RED)
    screen.blit(game_over_text, ((SCREEN_WIDTH - game_over_text.get_width()) // 2, SCREEN_HEIGHT // 2))
    pygame.display.update()
    time.sleep(2)

def draw_collision_effect(obstacle):
    # Draw a red circle around the obstacle to indicate collision
    collision_radius = max(CAR_WIDTH, CAR_HEIGHT)
    pygame.draw.circle(screen, RED, (obstacle.x + CAR_WIDTH // 2, obstacle.y + CAR_HEIGHT // 2), collision_radius, 5)

def game_loop(speed_level):
    global move_left, move_right, game_over_flag

    car = Car()

    # Scoring variables
    score = 0
    original_num_obstacles = 5  # 3 + 2
    num_obstacles = max(1, int(original_num_obstacles * 0.7))  # Reduce by 30%
    obstacles = [Obstacle(speed_level) for _ in range(num_obstacles)]

    start_time = time.time()
    finished_without_collision = False
    collision_effect_time = 0
    last_collided_obstacle = None  # Keep track of the last collided obstacle

    while not game_over_flag:
        screen.fill(WHITE)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over_flag = True

        # Move car based on key input or human detection
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or move_left:
            car.move(-1)  # Moving left
        if keys[pygame.K_RIGHT] or move_right:
            car.move(1)  # Moving right

        # Draw the road and the car
        draw_road()
        car.draw()

        # Move and draw obstacles
        collision_occurred = False
        for obstacle in obstacles:
            obstacle.move()
            obstacle.draw()

            # Check for collision
            if obstacle.check_collision(car):
                collision_occurred = True
                collision_effect_time = pygame.time.get_ticks()  # Record the time of collision
                last_collided_obstacle = obstacle  # Update the last collided obstacle
                score = max(0, score - 1)  # Decrease score by 1 (don't let it go below zero)

            # Add 1 point if obstacle crossed without collision
            if obstacle.crossed:
                if not collision_occurred:
                    score += 1  # Increase score by 1
                obstacle.crossed = False  # Reset crossing state

        # Draw collision effect if recent collision on the last collided obstacle
        if last_collided_obstacle and pygame.time.get_ticks() - collision_effect_time < 500:  # Show effect for 0.5 seconds
            draw_collision_effect(last_collided_obstacle)

        # Display score at the top right corner
        font = pygame.font.SysFont(None, 55)
        score_text = font.render(f'Score: {score}', True, BLACK)
        screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, 20))

        # Check for finish condition (200 seconds)
        if time.time() - start_time > FINISH_TIME:
            game_over_flag = True
            finished_without_collision = True

        # Update display
        pygame.display.update()

        # Cap the frame rate
        clock.tick(FPS)

    # Show winning screen if no collision
    if finished_without_collision:
        screen.fill(GREEN)
        win_text = font.render('Wooow, You did it!!!, You Win!!!!!', True, WHITE)
        screen.blit(win_text, ((SCREEN_WIDTH - win_text.get_width()) // 2, SCREEN_HEIGHT // 2))
        pygame.display.update()
        time.sleep(2)

    # Quit the game
    pygame.quit()


def detect_human_movement(video_file=None):
    global move_left, move_right, game_over_flag

    # Open the video file or the webcam feed
    if video_file:
        cap = cv2.VideoCapture(video_file)
    else:
        cap = cv2.VideoCapture(0)

    # Reduce frame size for faster processing
    FRAME_WIDTH = 320  # Set a smaller width for the frame
    FRAME_HEIGHT = 240  # Set a smaller height for the frame
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    frame_skip = 30  # Process every 2nd frame to speed up detection
    frame_count = 0

    while cap.isOpened() and not game_over_flag:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue  # Skip this frame to speed up detection

        # Convert the frame to RGB for Mediapipe processing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x

            # Swapped the direction for correct left/right movement
            if left_shoulder < 0.4:  # Move right
                move_left = False
                move_right = True
            elif right_shoulder > 0.6:  # Move left
                move_left = True
                move_right = False
            else:  # Stay neutral
                move_left = False
                move_right = False

    cap.release()
    cv2.destroyAllWindows()


# Start the game
if __name__ == "__main__":
    # Handle command line argument for speed level and optional video file
    if len(sys.argv) < 2 or not sys.argv[1].isdigit() or not (0 <= int(sys.argv[1]) <= 5):
        print("Usage: python car_game.py <speed_level: 0-5> [optional_video_path]")
        sys.exit(1)

    speed_level = int(sys.argv[1])
    video_file = sys.argv[2] if len(sys.argv) == 3 else None

    # Start human movement detection in a separate thread
    human_thread = threading.Thread(target=detect_human_movement, args=(video_file,))
    human_thread.start()

    # Start the game loop
    game_loop(speed_level)

    # Wait for human movement detection thread to finish
    human_thread.join()
