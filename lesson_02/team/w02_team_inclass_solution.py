"""
Course: CSE 351 
Lesson: L02 team activity
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
- Create a threaded class to make a call to the server where
  it retrieves data based on a URL.  The class should have a method
  called get_name() that returns the name of the character, planet, etc...
- The threaded class should only retrieve one URL.
  
- Speed up this program as fast as you can by:
    - creating as many as you can
    - start them all
    - join them all

"""

from datetime import datetime, timedelta
import threading

from common import *

# Include cse 351 common Python files
from cse351 import *

# global
call_count = 0

class RequestThread(threading.Thread):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.result = None

    def getName(self):
        return self.name

    def run(self):
        global call_count
        item = get_data_from_server(self.url)
        call_count += 1
        self.name = item.name
        self.barrier.wait()

def get_urls(film6, kind, barrier):
    global call_count

    urls = film6[kind]
    #print(kind)
    threads = []
    for url in urls:
        thread = RequestThread(url)
        thread.start()
        threads.append(thread)

    return threads

def main():
    global call_count

    log = Log(show_terminal=True)
    log.start_timer('Starting to retrieve data from the server')
    barrier = threading.Barrier(92)

    film6 = get_data_from_server(f'{TOP_API_URL}/films/6')
    call_count += 1
    kind_of_threads = {}
    print_dict(film6)

    # Retrieve people
    kind_of_threads['characters'] = get_urls(film6, 'characters', barrier)
    kind_of_threads['planets'] = get_urls(film6, 'planets', barrier)
    kind_of_threads['starships'] = get_urls(film6, 'starships', barrier)
    kind_of_threads['vehicles'] = get_urls(film6, 'vehicles', barrier)
    kind_of_threads['species'] = get_urls(film6, 'species', barrier)

    for kind in kind_of_threads:
        print(kind)
        for thread in kind_of_threads[kind]:
            thread.join()
            print(f'  - {thread.getName()}')

    log.stop_timer('Total Time To complete')
    log.write(f'There were {call_count} calls to the server')

if __name__ == "__main__":
    main()
