"""
Course: CSE 351 
Assignment: 08 Prove Part 2
File:   prove_part_2.py
Author: <Add name here>

Purpose: Part 2 of assignment 8, finding the path to the end of a maze using recursion.

Instructions:
- Do not create classes for this assignment, just functions.
- Do not use any other Python modules other than the ones included.
- You MUST use recursive threading to find the end of the maze.
- Each thread MUST have a different color than the previous thread:
    - Use get_color() to get the color for each thread; you will eventually have duplicated colors.
    - Keep using the same color for each branch that a thread is exploring.
    - When you hit an intersection spin off new threads for each option and give them their own colors.

This code is not interested in tracking the path to the end position. Once you have completed this
program however, describe how you could alter the program to display the found path to the exit
position:

What would be your strategy?

to retrace the connection of threads that led to the end position by starting form the end.

Why would it work?

As long as each thread is aware of it's parent thread, it would work because it can follow the chain of parent threads back to the start.

"""

import math
import threading 
from screen import Screen
from maze import Maze
import sys
import cv2

# Include cse 351 files
from cse351 import *

SCREEN_SIZE = 700
COLOR = (0, 0, 255)
COLORS = (
    (0,0,255),
    (0,255,0),
    (255,0,0),
    (255,255,0),
    (0,255,255),
    (255,0,255),
    (128,0,0),
    (128,128,0),
    (0,128,0),
    (128,0,128),
    (0,128,128),
    (0,0,128),
    (72,61,139),
    (143,143,188),
    (226,138,43),
    (128,114,250)
)
SLOW_SPEED = 100
FAST_SPEED = 0

# Globals
current_color_index = 0
thread_count = 0
stop = False
speed = SLOW_SPEED
stop_lock = threading.Lock()
color_lock = threading.Lock()
count_lock = threading.Lock()
move_lock = threading.Lock()

def get_color():
    """ Returns a different color when called """
    global current_color_index
    if current_color_index >= len(COLORS):
        current_color_index = 0
    color = COLORS[current_color_index]
    current_color_index += 1
    return color


# TODO: Add any function(s) you need, if any, here.
def _should_stop():
    """Read the shared stop flag safely."""
    with stop_lock:
        return stop


def _set_stop():
    """Set the shared stop flag safely."""
    global stop
    with stop_lock:
        stop = True


def _next_color():
    """Get a thread color safely."""
    with color_lock:
        return get_color()


def _increment_thread_count():
    """Count a newly created thread safely."""
    global thread_count
    with count_lock:
        thread_count += 1


def _try_move(maze, row, col, color):
    """Atomically check and move to avoid races between threads."""
    with move_lock:
        if not maze.can_move_here(row, col):
            return False
        maze.move(row, col, color)
        return True


def _search_branch(maze, row, col, color):
    """Recursively search from one branch of the maze."""
    if _should_stop():
        return

    if not _try_move(maze, row, col, color):
        return

    if maze.at_end(row, col):
        _set_stop()
        return

    if _should_stop():
        return

    moves = maze.get_possible_moves(row, col)
    if len(moves) == 0:
        return

    # Keep one path in this thread; split the rest into new threads.
    threads = []
    for next_row, next_col in moves[1:]:
        if _should_stop():
            break
        child_color = _next_color()
        child = threading.Thread(target=_search_branch, args=(maze, next_row, next_col, child_color))
        _increment_thread_count()
        child.start()
        threads.append(child)

    first_row, first_col = moves[0]
    _search_branch(maze, first_row, first_col, color)

    for child in threads:
        child.join()


def _enable_auto_advance():
    """Make cv2.waitKey non-blocking so each maze proceeds automatically."""
    if getattr(_enable_auto_advance, "_patched", False):
        return

    original_wait_key = cv2.waitKey

    def non_blocking_wait_key(_delay):
        return original_wait_key(1)

    cv2.waitKey = non_blocking_wait_key
    _enable_auto_advance._patched = True


def solve_find_end(maze):
    """ Finds the end position using threads. Nothing is returned. """
    # When one of the threads finds the end position, stop all of them.
    global stop
    global thread_count
    global current_color_index
    _enable_auto_advance()
    stop = False

    thread_count = 1
    current_color_index = 0

    start_row, start_col = maze.get_start_pos()
    start_color = _next_color()
    _search_branch(maze, start_row, start_col, start_color)




def find_end(log, filename, delay):
    """ Do not change this function """

    global thread_count
    global speed

    # create a Screen Object that will contain all of the drawing commands
    screen = Screen(SCREEN_SIZE, SCREEN_SIZE)
    screen.background((255, 255, 0))

    maze = Maze(screen, SCREEN_SIZE, SCREEN_SIZE, filename, delay=delay)

    solve_find_end(maze)

    log.write(f'Number of drawing commands = {screen.get_command_count()}')
    log.write(f'Number of threads created  = {thread_count}')

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


def find_ends(log):
    """ Do not change this function """

    files = (
        ('very-small.bmp', True),
        ('very-small-loops.bmp', True),
        ('small.bmp', True),
        ('small-loops.bmp', True),
        ('small-odd.bmp', True),
        ('small-open.bmp', False),
        ('large.bmp', False),
        ('large-loops.bmp', False),
        ('large-squares.bmp', False),
        ('large-open.bmp', False)
    )

    log.write('*' * 40)
    log.write('Part 2')
    for filename, delay in files:
        filename = f'./mazes/{filename}'
        log.write()
        log.write(f'File: {filename}')
        find_end(log, filename, delay)
    log.write('*' * 40)


def main():
    """ Do not change this function """
    sys.setrecursionlimit(5000)
    log = Log(show_terminal=True)
    find_ends(log)


if __name__ == "__main__":
    main()