"""
Course: CSE 351
Assignment: 06
Author: [Your Name]

Instructions:

- see instructions in the assignment description in Canvas

""" 

import multiprocessing as mp
import os
import cv2

from cse351 import *

# Folders
INPUT_FOLDER = "faces"
STEP1_OUTPUT_FOLDER = "step1_smoothed"
STEP2_OUTPUT_FOLDER = "step2_grayscale"
STEP3_OUTPUT_FOLDER = "step3_edges"

# Parameters for image processing
GAUSSIAN_BLUR_KERNEL_SIZE = (5, 5)
CANNY_THRESHOLD1 = 75
CANNY_THRESHOLD2 = 155

# Allowed image extensions
ALLOWED_EXTENSIONS = ['.jpg']

# Queue sentinel value
DONE = None

# ---------------------------------------------------------------------------
def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")

# ---------------------------------------------------------------------------
def task_convert_to_grayscale(image):
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        return image # Already grayscale
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# ---------------------------------------------------------------------------
def task_smooth_image(image, kernel_size):
    return cv2.GaussianBlur(image, kernel_size, 0)

# ---------------------------------------------------------------------------
def task_detect_edges(image, threshold1, threshold2):
    if len(image.shape) == 3 and image.shape[2] == 3:
        print("Warning: Applying Canny to a 3-channel image. Converting to grayscale first for Canny.")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 3 and image.shape[2] != 1 : # Should not happen with typical images
        print(f"Warning: Input image for Canny has an unexpected number of channels: {image.shape[2]}")
        return image # Or raise error
    return cv2.Canny(image, threshold1, threshold2)

# ---------------------------------------------------------------------------
def get_pipeline_process_counts():
    cpu_count = max(1, mp.cpu_count())
    per_stage = max(1, cpu_count // 3)
    smooth_workers = per_stage
    grayscale_workers = per_stage
    edge_workers = max(1, cpu_count - smooth_workers - grayscale_workers)
    return smooth_workers, grayscale_workers, edge_workers


# ---------------------------------------------------------------------------
def smooth_worker(input_queue, output_queue):
    while True:
        filename = input_queue.get()
        if filename is DONE:
            break

        try:
            input_image_path = os.path.join(INPUT_FOLDER, filename)
            image = cv2.imread(input_image_path)
            if image is None:
                continue

            smoothed = task_smooth_image(image, GAUSSIAN_BLUR_KERNEL_SIZE)
            output_queue.put((filename, smoothed))
        except Exception as ex:
            print(f"Error smoothing '{filename}': {ex}")


# ---------------------------------------------------------------------------
def grayscale_worker(input_queue, output_queue):
    while True:
        item = input_queue.get()
        if item is DONE:
            break

        try:
            filename, image = item
            gray = task_convert_to_grayscale(image)
            output_queue.put((filename, gray))
        except Exception as ex:
            print(f"Error converting grayscale '{filename}': {ex}")


# ---------------------------------------------------------------------------
def edge_worker(input_queue, output_folder):
    while True:
        item = input_queue.get()
        if item is DONE:
            break

        try:
            filename, image = item
            edges = task_detect_edges(image, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
            output_image_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_image_path, edges)
        except Exception as ex:
            print(f"Error detecting edges '{filename}': {ex}")


# ---------------------------------------------------------------------------
def list_input_images(folder):
    files = []
    for filename in os.listdir(folder):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ALLOWED_EXTENSIONS:
            files.append(filename)
    return files


# ---------------------------------------------------------------------------
def clear_output_images(folder):
    for filename in os.listdir(folder):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ALLOWED_EXTENSIONS:
            try:
                os.remove(os.path.join(folder, filename))
            except OSError as ex:
                print(f"Warning: unable to remove '{filename}': {ex}")

# ---------------------------------------------------------------------------
def run_image_processing_pipeline():
    print("Starting image processing pipeline...")

    create_folder_if_not_exists(STEP3_OUTPUT_FOLDER)
    clear_output_images(STEP3_OUTPUT_FOLDER)

    image_files = list_input_images(INPUT_FOLDER)
    smooth_count, grayscale_count, edge_count = get_pipeline_process_counts()

    queue1 = mp.Queue(maxsize=128)
    queue2 = mp.Queue(maxsize=128)
    queue3 = mp.Queue(maxsize=128)

    smooth_processes = [
        mp.Process(target=smooth_worker, args=(queue1, queue2))
        for _ in range(smooth_count)
    ]
    grayscale_processes = [
        mp.Process(target=grayscale_worker, args=(queue2, queue3))
        for _ in range(grayscale_count)
    ]
    edge_processes = [
        mp.Process(target=edge_worker, args=(queue3, STEP3_OUTPUT_FOLDER))
        for _ in range(edge_count)
    ]

    for process in smooth_processes + grayscale_processes + edge_processes:
        process.start()

    for filename in image_files:
        queue1.put(filename)

    for _ in range(smooth_count):
        queue1.put(DONE)
    for process in smooth_processes:
        process.join()

    for _ in range(grayscale_count):
        queue2.put(DONE)
    for process in grayscale_processes:
        process.join()

    for _ in range(edge_count):
        queue3.put(DONE)
    for process in edge_processes:
        process.join()

    queue1.close()
    queue2.close()
    queue3.close()

    print("\nImage processing pipeline finished!")
    print(f"Original images are in: '{INPUT_FOLDER}'")
    print(f"Images processed: {len(image_files)}")
    print(f"Pipeline workers (smooth, grayscale, edge): ({smooth_count}, {grayscale_count}, {edge_count})")
    print(f"Edge images are in: '{STEP3_OUTPUT_FOLDER}'")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log = Log(show_terminal=True)
    log.start_timer('Processing Images')

    # check for input folder
    if not os.path.isdir(INPUT_FOLDER):
        print(f"Error: The input folder '{INPUT_FOLDER}' was not found.")
        print(f"Create it and place your face images inside it.")
        print('Link to faces.zip:')
        print('   https://drive.google.com/file/d/1eebhLE51axpLZoU6s_Shtw1QNcXqtyHM/view?usp=sharing')
    else:
        run_image_processing_pipeline()

    log.write()
    log.stop_timer('Total Time To complete')
