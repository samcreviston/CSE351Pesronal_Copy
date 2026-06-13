"""
Course: CSE 251 
Assignment: 08 Prove Part 1
File:   prove_part_1.py
Author: <Add name here>

Purpose: Part 1 of assignment 8, finding the path to the end of a maze using recursion.

Instructions:

- Do not create classes for this assignment, just functions.
- Do not use any other Python modules other than the ones included.
- Complete any TODO comments.
"""

import math
from screen import Screen
from maze import Maze
import cv2
import sys

# Include cse 351 files
from cse351 import *

SCREEN_SIZE = 800
COLOR = (0, 0, 255)
SLOW_SPEED = 100
FAST_SPEED = 1
speed = SLOW_SPEED


def _enable_auto_advance():
    """Make cv2.waitKey non-blocking so each maze proceeds automatically."""
    if getattr(_enable_auto_advance, "_patched", False):
        return

    original_wait_key = cv2.waitKey

    def non_blocking_wait_key(_delay):
        return original_wait_key(1)

    cv2.waitKey = non_blocking_wait_key
    _enable_auto_advance._patched = True

def solve_path(maze):
    """ Solve the maze and return the path found between the start and end positions.  
        The path is a list of positions, (x, y) """
    _enable_auto_advance()
    path = []

    def recurse(row, col):
        # Base case: reached the exit
        if maze.at_end(row, col):
            path.append((row, col))
            return True

        # Mark current cell as part of current exploration
        maze.move(row, col, COLOR)

        # Prefer right/down before up/left when exploring neighbors
        possible_moves = maze.get_possible_moves(row, col)
        priority = {
            (0, 1): 0,   # right
            (1, 0): 1,   # down
            (-1, 0): 2,  # up
            (0, -1): 3   # left
        }
        possible_moves.sort(key=lambda move: priority.get((move[0] - row, move[1] - col), 99))

        for next_row, next_col in possible_moves:
            if recurse(next_row, next_col):
                # On the way back up, add this position to the correct path
                path.append((row, col))
                return True

        # Dead end — restore cell to grey and backtrack
        maze.restore(row, col)
        return False

    start_row, start_col = maze.get_start_pos()
    recurse(start_row, start_col)
    path.reverse()   # path was built end-to-start; flip it
    return path


def get_path(log, filename):
    """ Do not change this function """
    # 'Maze: Press "q" to quit, "1" slow drawing, "2" faster drawing, "p" to play again'
    global speed

    # create a Screen Object that will contain all of the drawing commands
    screen = Screen(SCREEN_SIZE, SCREEN_SIZE)
    screen.background((255, 255, 0))

    maze = Maze(screen, SCREEN_SIZE, SCREEN_SIZE, filename)

    path = solve_path(maze)

    log.write(f'Drawing commands to solve = {screen.get_command_count()}')

    done = False
    while not done:
        if screen.play_commands(speed): 
            key = cv2.waitKey(0)
            if key == ord('1'):
                speed = SLOW_SPEED
            elif key == ord('2'):
                speed = FAST_SPEED
            elif key == ord('q'):
                exit()
            elif key != ord('p'):
                done = True
        else:
            done = True

    return path


def find_paths(log):
    """ Do not change this function """

    files = (
        'very-small.bmp',
        'very-small-loops.bmp',
        'small.bmp',
        'small-loops.bmp',
        'small-odd.bmp',
        'small-open.bmp',
        'large.bmp',
        'large-loops.bmp',
        'large-squares.bmp',
        'large-open.bmp'
    )

    log.write('*' * 40)
    log.write('Part 1')
    for filename in files:
        filename = f'./mazes/{filename}'
        log.write()
        log.write(f'File: {filename}')
        path = get_path(log, filename)
        log.write(f'Found path has length     = {len(path)}')
    log.write('*' * 40)


def main():
    """ Do not change this function """
    sys.setrecursionlimit(5000)
    log = Log(show_terminal=True)
    find_paths(log)


if __name__ == "__main__":
    main()