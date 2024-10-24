import pygame
import sys
import os

# Initialize pygame mixer
pygame.mixer.init()

def play_mp3(mp3_path):
    # Check if the file exists and is an MP3 file
    if not os.path.exists(mp3_path):
        print(f"File {mp3_path} does not exist.")
        return
    if not mp3_path.endswith(".mp3"):
        print("Please provide a valid MP3 file.")
        return

    # Load and play the MP3 file
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.play()

    print(f"Playing {mp3_path}...")

    # Keep the program running while the music plays
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)  # Check if the music is still playing

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python play_mp3.py <path_to_mp3>")
        sys.exit(1)

    mp3_path = sys.argv[1]
    play_mp3(mp3_path)
