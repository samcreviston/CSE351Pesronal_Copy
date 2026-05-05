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

# threaded class to make a call to the server where
#   it retrieves data based on a URL.  The class should have a method
#   called get_name() that returns the name of the character, planet, etc...
# - The threaded class should only retrieve one URL.
class URLThread(threading.Thread):
    def __init__(self, kind, url: str):
        super().__init__()
        self.kind = kind
        self.url = url
        self.result = None


    def run(self):
        global call_count
        self.result = get_data_from_server(self.url)
        call_count += 1

    def get_name(self):
        return self.result.get("name")



def get_urls(film6, kind):
    global call_count

    urls = film6[kind]
    print(kind)
    for url in urls:
        call_count += 1
        item = get_data_from_server(url)
        print(f'  - {item["name"]}')

def main():
    global call_count

    log = Log(show_terminal=True)
    log.start_timer('Starting to retrieve data from the server')

    film6 = get_data_from_server(f'{TOP_API_URL}/films/6')
    call_count += 1
    print_dict(film6)

    # call get_urls for each of the 5 categories (characters, planets, starships, vehicles, species) in a separate thread
    kinds = ['characters', 'planets', 'starships', 'vehicles', 'species']
    threads = []
    
    for kind in kinds:
        for url in film6[kind]:
            thread = URLThread(kind, url=url)
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    results = {kind: [] for kind in kinds}
    for t in threads:
        results[t.kind].append(t.get_name())

    for kind, t in zip(kinds, threads):
        print(kind)
        for name in results[kind]:
            print(f'  - {name}')

    log.stop_timer('Total Time To complete')
    log.write(f'There were {call_count} calls to the server')

if __name__ == "__main__":
    main()
