"""
Course    : CSE 351
Assignment: 04
Student   : <your name here>

Instructions:
    - review instructions in the course

In order to retrieve a weather record from the server, Use the URL:

f'{TOP_API_URL}/record/{name}/{recno}

where:

name: name of the city
recno: record number starting from 0

"""

import time
from common import *

from cse351 import *

THREADS = 150               # set
WORKERS = 5                 # set
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
# thread function (and arguments) - gets data from the server and puts it in the output queue
def retrieve_weather_data(in_queue, out_queue, cmd_slots, cmd_items, cmd_lock, out_slots, out_items, out_lock):
    while True:
        cmd_items.acquire()
        with cmd_lock:
            city, recno = in_queue.get()
        cmd_slots.release()

        if city is None:
            break

        item = get_data_from_server(f"{TOP_API_URL}/record/{city}/{recno}")
        if item is None or item.get("status") != "OK":
            continue

        out_slots.acquire()
        with out_lock:
            out_queue.put((item["city"], item["date"], item["temp"]))
        out_items.release()
        
        # Print a dot to indicate progress
        #print('.', end='', flush=True)
    
    


# ---------------------------------------------------------------------------
# worker threaded class - takes data from the output queue and adds it to NOAA
class WorkerThread(threading.Thread):
    def __init__(self, out_queue, noaa, out_slots, out_items, out_lock):
        super().__init__()
        self.out_queue = out_queue
        self.noaa = noaa
        self.out_slots = out_slots
        self.out_items = out_items
        self.out_lock = out_lock

    def run(self):
        while True:
            self.out_items.acquire()
            with self.out_lock:
                city, date, temp = self.out_queue.get()
            self.out_slots.release()

            if city is None:
                break

            self.noaa.add_record(city, date, temp)
            # Print a dot to indicate progress
            print('.', end='', flush=True)


# ---------------------------------------------------------------------------
# class
# This class stores all of the information of each city.
# A city will have a list of date and temperature values.
class NOAA:

    def __init__(self):
        self.lock = threading.Lock()
        self.data = {
            city: {'records': [], 'sum': 0.0, 'count': 0}
            for city in CITIES
        }

    def add_record(self, city, date, temp):
        with self.lock:
            self.data[city]['records'].append((date, temp))
            self.data[city]['sum'] += temp
            self.data[city]['count'] += 1

    def get_temp_details(self, city):
        with self.lock:
            count = self.data[city]['count']
            if count == 0:
                return 0.0
            return self.data[city]['sum'] / count


# ---------------------------------------------------------------------------
class Queue351():
    """ This is the queue object to use for this class. Do not modify!! """

    def __init__(self):
        self.__items = []
   
    def put(self, item):
        assert len(self.__items) <= 10
        self.__items.append(item)

    def get(self):
        return self.__items.pop(0)

    def get_size(self):
        """ Return the size of the queue like queue.Queue does -> Approx size """
        extra = 1 if random.randint(1, 50) == 1 else 0
        if extra > 0:
            extra *= -1 if random.randint(1, 2) == 1 else 1
        return len(self.__items) + extra


# ---------------------------------------------------------------------------
def verify_noaa_results(noaa):

    answers = {
        'sandiego': 14.5004,
        'philadelphia': 14.865,
        'san_antonio': 14.638,
        'san_jose': 14.5756,
        'new_york': 14.6472,
        'houston': 14.591,
        'dallas': 14.835,
        'chicago': 14.6584,
        'los_angeles': 15.2346,
        'phoenix': 12.4404,
    }

    print()
    print('NOAA Results: Verifying Results')
    print('===================================')
    for name in CITIES:
        answer = answers[name]
        avg = noaa.get_temp_details(name)

        if abs(avg - answer) > 0.00001:
            msg = f'FAILED  Expected {answer}'
        else:
            msg = f'PASSED'
        print(f'{name:>15}: {avg:<10} {msg}')
    print('===================================')


# ---------------------------------------------------------------------------
def main():
    log = Log(show_terminal=True, filename_log='assignment.log')
    log.start_timer()

    noaa = NOAA()

    # Start server
    data = get_data_from_server(f'{TOP_API_URL}/start')

    # Get all cities number of records
    print('Retrieving city details')
    city_details = {}
    name = 'City'
    print(f'{name:>15}: Records')
    print('===================================')
    for name in CITIES:
        city_details[name] = get_data_from_server(f'{TOP_API_URL}/city/{name}')
        print(f"{name:>15}: Records = {city_details[name]['records']:,}")
    print('===================================')

    records = RECORDS_TO_RETRIEVE

    # --- Synchronization primitives ---
    cmd_slots = threading.Semaphore(10)
    cmd_items = threading.Semaphore(0)
    out_slots = threading.Semaphore(10)
    out_items = threading.Semaphore(0)
    cmd_lock = threading.Lock()
    out_lock = threading.Lock()

    in_q = Queue351()
    out_q = Queue351()

    # Start retriever threads for data to the output queue
    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=retrieve_weather_data, args=(in_q, out_q, cmd_slots, cmd_items, cmd_lock, out_slots, out_items, out_lock))
        threads.append(t)
        t.start()

    # Start worker threads before joining retrievers
    worker_threads = []
    for _ in range(WORKERS):
        t = WorkerThread(out_q, noaa, out_slots, out_items, out_lock)
        worker_threads.append(t)
        t.start()

    # Producer: enqueue all work with semaphore protection
    for city in CITIES:
        for recno in range(records):
            cmd_slots.acquire()
            with cmd_lock:
                in_q.put((city, recno))
            cmd_items.release()

    # Add sentinels for retrievers
    for _ in range(THREADS):
        cmd_slots.acquire()
        with cmd_lock:
            in_q.put((None, None))
        cmd_items.release()

    # Join retriever threads
    for t in threads:
        t.join()

    # Add sentinels for workers
    for _ in range(WORKERS):
        out_slots.acquire()
        with out_lock:
            out_q.put((None, None, None))
        out_items.release()

    # Join worker threads for data from the output queue to NOAA
    for t in worker_threads:
        t.join()

    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()

