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
ROAD_WIDTH = SCREEN_WIDTH // 2  # Adjust road width to fit half the screen width
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
    # Road in the middle
    road_rect = pygame.Rect((SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, ROAD_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, GRAY, road_rect)

    # Grass and trees on both sides
    pygame.draw.rect(screen, GREEN, pygame.Rect(0, 0, (SCREEN_WIDTH - ROAD_WIDTH) // 2, SCREEN_HEIGHT))
    pygame.draw.rect(screen, GREEN, pygame.Rect(SCREEN_WIDTH - (SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, (SCREEN_WIDTH - ROAD_WIDTH) // 2, SCREEN_HEIGHT))

    # Add some random trees/rocks (for effect)
    for i in range(10):
        tree_x = random.choice([random.randint(10, 100), random.randint(SCREEN_WIDTH - 100, SCREEN_WIDTH - 10)])
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

def game_loop(speed_level):
    global move_left, move_right, game_over_flag

    car = Car()

    # Increase the number of obstacles and reduce by 30%
    original_num_obstacles = 5  # 3 + 2
    num_obstacles = max(1, int(original_num_obstacles * 0.7))  # Reduce by 30%
    obstacles = [Obstacle(speed_level) for _ in range(num_obstacles)]

    start_time = time.time()
    finished_without_collision = False

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
                game_over()
                game_over_flag = True
                collision_occurred = True

            # Play sound if the obstacle has crossed and there was no collision
            if obstacle.crossed and not collision_occurred:
                NICE_SOUND.play()
                obstacle.crossed = False  # Reset crossing state

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
        font = pygame.font.SysFont(None, 55)
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

    while cap.isOpened() and not game_over_flag:
        ret, frame = cap.read()
        if not ret:
            break

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
