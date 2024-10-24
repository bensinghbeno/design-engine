import pygame
import random
import time
import sys
import cv2
import mediapipe as mp
import threading

# Initialize pygame
pygame.init()

# Mediapipe pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Constants for screen size based on command-line argument
SCREEN_INFO = pygame.display.Info()  # Get display screen info

# Set default screen size to full
screen_size_arg = None  # Placeholder for screen size argument

# Function to parse command-line arguments
def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen_size", type=str, choices=["half", "full"], help="Set the screen size to 'half' or 'full'")
    parser.add_argument("--speed_level", type=int, choices=range(1, 6), required=True, help="Set the speed level (1-5)")
    parser.add_argument("--video", type=str, help="Path to the optional video file")
    return parser.parse_args()

args = parse_arguments()

if args.screen_size == "half":
    SCREEN_WIDTH = int(SCREEN_INFO.current_w / 2)  # Get screen width
else:
    SCREEN_WIDTH = SCREEN_INFO.current_w  # Full width

SCREEN_HEIGHT = SCREEN_INFO.current_h  # Full height
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

# Initialize screen
if args.screen_size == "half":
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # Use SCREEN_WIDTH based on argument
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

pygame.display.set_caption("Car Game")

# Create clock for FPS
clock = pygame.time.Clock()

# Global variables for controlling the car
car_x_position = (SCREEN_WIDTH - CAR_WIDTH) // 2  # Start in the middle of the screen
move_left = False
move_right = False
game_over_flag = False

def draw_road():
    tree_area_width = (SCREEN_WIDTH - ROAD_WIDTH) // 2

    road_rect = pygame.Rect((SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, ROAD_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, GRAY, road_rect)

    pygame.draw.rect(screen, GREEN, pygame.Rect(0, 0, tree_area_width, SCREEN_HEIGHT))
    pygame.draw.rect(screen, GREEN, pygame.Rect(SCREEN_WIDTH - tree_area_width, 0, tree_area_width, SCREEN_HEIGHT))

    for i in range(10):
        tree_x = random.choice([random.randint(10, tree_area_width - 10), random.randint(SCREEN_WIDTH - tree_area_width + 10, SCREEN_WIDTH - 10)])
        tree_y = random.randint(0, SCREEN_HEIGHT)
        pygame.draw.circle(screen, BLACK, (tree_x, tree_y), random.randint(15, 25))

class Car:
    def __init__(self):
        self.image = pygame.transform.scale(CAR_IMAGE, (CAR_WIDTH, CAR_HEIGHT))
        self.y = SCREEN_HEIGHT - CAR_HEIGHT - 10
        self.speed = 10
        self.lateral_speed = self.speed / 3

    def move(self, dx):
        global car_x_position
        car_x_position += dx * self.lateral_speed  
        car_x_position = max((SCREEN_WIDTH - ROAD_WIDTH) // 2, min(car_x_position, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH))

    def draw(self):
        screen.blit(self.image, (car_x_position, self.y))

class Obstacle:
    def __init__(self, speed_factor):
        self.image = pygame.transform.scale(OBSTACLE_IMAGE, (CAR_WIDTH, CAR_HEIGHT))
        self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)
        self.y = random.randint(-150, -100)
        self.speed = speed_factor

    def move(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = random.randint(-150, -100)
            self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def check_collision(self, car):
        car_rect = pygame.Rect(car_x_position, car.y, CAR_WIDTH, CAR_HEIGHT)
        obstacle_rect = pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)
        return car_rect.colliderect(obstacle_rect)

def draw_close_button():
    button_size = 60
    button_padding = 30
    button_x = button_padding
    button_y = button_padding
    
    pygame.draw.rect(screen, RED, (button_x, button_y, button_size, button_size))
    
    line_padding = 5
    pygame.draw.line(screen, WHITE, (button_x + line_padding, button_y + line_padding),
                     (button_x + button_size - line_padding, button_y + button_size - line_padding), width=2)
    pygame.draw.line(screen, WHITE, (button_x + button_size - line_padding, button_y + line_padding),
                     (button_x + line_padding, button_y + button_size - line_padding), width=2)
    
    return pygame.Rect(button_x, button_y, button_size, button_size)

def draw_animating_red_box(car, time_passed):
    """Draws an animating red outline around the car to indicate a collision."""
    max_outline_size = 15  # Max thickness of the outline
    outline_size = int((time_passed / 3) * max_outline_size)

    if outline_size > 0:  # Only draw if the outline size is greater than 0
        car_rect = pygame.Rect(car_x_position - outline_size // 2, car.y - outline_size // 2, CAR_WIDTH + outline_size, CAR_HEIGHT + outline_size)
        pygame.draw.rect(screen, RED, car_rect, outline_size)  # Draw the outline without filling

def detect_human_movement(video_file=None):
    global car_x_position

    # Use webcam if no video file is provided
    cap = cv2.VideoCapture(video_file) if video_file else cv2.VideoCapture(0)
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    # Skip displaying the window altogether by commenting out or removing cv2.imshow
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip the frame horizontally for a mirror effect
        frame = cv2.flip(frame, 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            # Calculate the center x position of the person
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x
            person_center_x = int((left_shoulder + right_shoulder) / 2 * FRAME_WIDTH)

            # Update the car's x position based on the detected human position
            car_x_position = person_center_x / FRAME_WIDTH * SCREEN_WIDTH  # Normalize to screen size

        # No window display using cv2.imshow

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def game_loop(speed_level):
    global move_left, move_right, game_over_flag

    car = Car()
    score = 0
    num_obstacles = 5
    obstacles = [Obstacle(speed_level) for _ in range(num_obstacles)]
    start_time = time.time()
    finished_without_collision = False
    collision_start_time = None  # Time when collision occurred

    while True:
        screen.fill(WHITE)
        draw_road()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_left = True
                if event.key == pygame.K_RIGHT:
                    move_right = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left = False
                if event.key == pygame.K_RIGHT:
                    move_right = False

        # Move the car
        if move_left:
            car.move(-1)
        if move_right:
            car.move(1)

        # Move and draw obstacles
        for obstacle in obstacles:
            obstacle.move()
            obstacle.draw()

            if obstacle.check_collision(car):
                if collision_start_time is None:  # Only start the timer on the first collision
                    collision_start_time = time.time()
                finished_without_collision = False
                draw_animating_red_box(car, time.time() - collision_start_time)
            else:
                finished_without_collision = True  # Reset if there's no collision

        # Draw the car
        car.draw()

        # Draw the close button
        close_button = draw_close_button()

        # Handle close button click
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:  # Left mouse button
            if close_button.collidepoint((mouse_x, mouse_y)):
                pygame.quit()
                sys.exit()

        # Update the display
        pygame.display.flip()
        clock.tick(FPS)

        # Check game over condition
        if finished_without_collision and (time.time() - start_time) >= FINISH_TIME:
            break

    # Game over screen
    screen.fill(WHITE)
    font = pygame.font.SysFont("Arial", 50)
    game_over_text = font.render("Game Over!", True, BLACK)
    screen.blit(game_over_text, ((SCREEN_WIDTH - game_over_text.get_width()) // 2, SCREEN_HEIGHT // 3))
    pygame.display.flip()
    time.sleep(3)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Start human detection in a separate thread
    human_detection_thread = threading.Thread(target=detect_human_movement, args=(args.video,))
    human_detection_thread.daemon = True  # Allow thread to exit when the main program does
    human_detection_thread.start()

    # Wait for 5 seconds before starting the game
    time.sleep(2)

    # Start the game loop
    game_loop(args.speed_level)
