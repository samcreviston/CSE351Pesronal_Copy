"""
Course: CSE 351 
Lesson: L03 team activity
File:   team.py
Author: <Add name here>

Purpose: Retrieve Star Wars details from a server

Instructions:

- This program requires that the server.py program be started in a terminal window.
- The program will retrieve the names of:
    - characters
    - planets
    - starships
    - vehicles
    - species

- the server will delay the request by 0.5 seconds

TODO
- Create a threaded function to make a call to the server where
  it retrieves data based on a URL.  The function should have a method
  called get_name() that returns the name of the character, planet, etc...
- The threaded function should only retrieve one URL.
- Create a queue that will be used between the main thread and the threaded functions

# read one name from one url per thread. The main thread will add urls to the queue and the threaded function will read one url from the queue and get the name and print it. The main thread will wait for all threads to finish before it prints the total time and call count.
    - join them all

"""

from datetime import datetime, timedelta
import threading
import queue
from common import *

# Include cse 351 common Python files
from cse351 import *

# global
call_count = 0
worker_count = 0
q = queue.Queue()

def get_urls(film6, kind):
    urls = film6[kind]
    print(kind)
    for url in urls:
        q.put(url)

# read one name from one url per thread
def thread_function(url):
    global worker_count
    worker_count += 1
    item = get_data_from_server(url)
    print(f'  - {item["name"]}')

def main():
    global call_count

    log = Log(show_terminal=True)
    log.start_timer('Starting to retrieve data from the server')

    film6 = get_data_from_server(f'{TOP_API_URL}/films/6')
    call_count += 1
    print_dict(film6)

    # Retrieve people, planets, starships, vehicles, and species
    categories = ['characters', 'planets', 'starships', 'vehicles', 'species']
    for category in categories:
        get_urls(film6, category)
        call_count += len(film6[category])

    threads = []
    for _ in range(q.qsize()):
        t = threading.Thread(target=thread_function, args=(q.get(),))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()



    log.stop_timer('Total Time To complete')
    log.write(f'There were {call_count} calls to the server')
    log.write(f'There were {worker_count} threads that completed')

if __name__ == "__main__":
    main()
