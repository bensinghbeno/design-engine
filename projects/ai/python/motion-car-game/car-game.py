import pygame
import random
import time
import sys
import cv2
import mediapipe as mp
import threading
import os  # For handling file paths

# Initialize pygame
pygame.init()

# Initialize pygame mixer
pygame.mixer.init()
score = 0


def play_mp3(mp3_path):
    # Function to play the mp3 in a separate thread
    def play_music():
        # Check if the file exists and is an MP3 file
        if not os.path.exists(mp3_path):
            print(f"File {mp3_path} does not exist.")
            return
        if not mp3_path.endswith(".mp3"):
            print("Please provide a valid MP3 file.")
            return

        # Check if music is already playing, and skip if it is
        if pygame.mixer.music.get_busy():
            print(f"Audio already playing, skipping play attempt for {mp3_path}")
            return
        
        # Load and play the MP3 file
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.play()
        print(f"Playing {mp3_path}...")

        # Keep the program running while the music plays
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Check if the music is still playing

    # Run the play_music function in a new thread to avoid blocking
    music_thread = threading.Thread(target=play_music)
    music_thread.daemon = True  # Ensure the thread will close when the program exits
    music_thread.start()


# Mediapipe pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Constants for screen size based on command-line argument
SCREEN_INFO = pygame.display.Info()  # Get display screen info

# Function to parse command-line arguments
def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen_size", type=str, choices=["half", "full"], help="Set the screen size to 'half' or 'full'")
    parser.add_argument("--speed_level", type=int, choices=range(1, 6), required=True, help="Set the speed level (1-5)")
    parser.add_argument("--video", type=str, help="Path to the optional video file")
    parser.add_argument("--image_path", type=str, default=".", help="Path to the folder containing car and obstacle images")
    parser.add_argument("--skip_frames", type=int, default=0, help="Number of frames to skip for reducing processing load")
    return parser.parse_args()

args = parse_arguments()

# Set screen size
if args.screen_size == "half":
    SCREEN_WIDTH = int(SCREEN_INFO.current_w / 2)  # Get screen width
else:
    SCREEN_WIDTH = SCREEN_INFO.current_w  # Full width
SCREEN_HEIGHT = SCREEN_INFO.current_h  # Full height

ROAD_WIDTH = int(SCREEN_WIDTH * 0.8)  # Increase road width to 80% of the screen width
CAR_WIDTH = 50
CAR_HEIGHT = 100
FPS = 60
FINISH_TIME = 200  # Finish time

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Load assets with default or user-specified image path
image_path = args.image_path
CAR_IMAGE = pygame.image.load(os.path.join(image_path, 'car.jpg'))  # Load car image
OBSTACLE_IMAGE = pygame.image.load(os.path.join(image_path, 'obstacle.png'))  # Load obstacle image


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



def draw_player_info(player_name, score_value):
    font = pygame.font.SysFont("Arial", 30)
    name_text = font.render(f"{player_name}", True, (255, 255, 0))  # Yellow text
    score_text = font.render(f"Score: {score_value}", True, (255, 255, 0))  # Yellow text

    box_width = max(name_text.get_width(), score_text.get_width()) + 20
    box_height = name_text.get_height() + score_text.get_height() + 20
    box_x = SCREEN_WIDTH - box_width - 10
    box_y = 10

    pygame.draw.rect(screen, (0, 0, 255), (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, (255, 255, 0), (box_x, box_y, box_width, box_height), 2)

    screen.blit(name_text, (box_x + 10, box_y + 5))
    screen.blit(score_text, (box_x + 10, box_y + 10 + name_text.get_height()))



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
        # Restrict the car movement within the road bounds
        left_road_edge = (SCREEN_WIDTH - ROAD_WIDTH) // 2
        right_road_edge = (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH
        car_x_position = max(left_road_edge, min(car_x_position, right_road_edge))

    def draw(self):
        screen.blit(self.image, (car_x_position, self.y))


class Obstacle:
    def __init__(self, speed_factor):
        self.image = pygame.transform.scale(OBSTACLE_IMAGE, (CAR_WIDTH, CAR_HEIGHT))
        self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)
        self.y = random.randint(-SCREEN_HEIGHT, -100)  # Ensure obstacles appear at random heights
        self.speed = speed_factor
        self.is_avoided = False  # Track if the obstacle has been avoided

    def move(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            # Reset the obstacle position and mark it as not avoided yet
            self.y = random.randint(-SCREEN_HEIGHT, -100)
            self.x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - CAR_WIDTH)
            self.is_avoided = False

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


def detect_human_movement(video_file=None, skip_frames=0):
    global car_x_position

    # Use webcam if no video file is provided
    cap = cv2.VideoCapture(video_file) if video_file else cv2.VideoCapture(0)
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    frame_counter = 0  # To track the current frame

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Skip frames if necessary
        if frame_counter % (skip_frames + 1) != 0:
            frame_counter += 1
            continue

        # Flip the frame horizontally for a mirror effect
        frame = cv2.flip(frame, 1)

        # Convert the frame to RGB for mediapipe processing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            # Calculate the center x position of the person
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x
            person_center_x = int((left_shoulder + right_shoulder) / 2 * FRAME_WIDTH)

            # Update the car's x position based on the detected human position
            car_x_position = person_center_x / FRAME_WIDTH * SCREEN_WIDTH  # Normalize to screen size

        frame_counter += 1

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()





def game_loop(speed_level):
    global move_left, move_right, score
    car = Car()
    num_obstacles = 5
    obstacles = [Obstacle(speed_level) for _ in range(num_obstacles)]
    start_time = time.time()
    finished_without_collision = True
    collision_start_time = None  # Time when collision occurred

    while True:
        screen.fill(WHITE)
        draw_road()
        draw_player_info("PLAYER 1", score)

        
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
                score -= 1
                play_mp3('sounds/sangi-mangi.mp3')
            else:
                # If the obstacle passes the car without collision, increase the score
                if obstacle.y > car.y + CAR_HEIGHT and not obstacle.is_avoided:
                    score += 50
                    obstacle.is_avoided = True  # Mark obstacle as avoided
                    play_mp3('sounds/eppadi-raa.mp3')

                    


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
    human_detection_thread = threading.Thread(target=detect_human_movement, args=(args.video, args.skip_frames))
    human_detection_thread.daemon = True
    human_detection_thread.start()

    time.sleep(2)  # Wait for 2 seconds before starting the game
    game_loop(args.speed_level)
