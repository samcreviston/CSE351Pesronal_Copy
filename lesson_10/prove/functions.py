"""
Course: CSE 351, week 10
File: functions.py
Author: <your name>

Instructions:

Depth First Search
https://www.youtube.com/watch?v=9RHO6jU--GU

Breadth First Search
https://www.youtube.com/watch?v=86g8jAQug04


Requesting a family from the server:
family_id = 6128784944
data = get_data_from_server('{TOP_API_URL}/family/{family_id}')

Example JSON returned from the server
{
    'id': 6128784944, 
    'husband_id': 2367673859,        # use with the Person API
    'wife_id': 2373686152,           # use with the Person API
    'children': [2380738417, 2185423094, 2192483455]    # use with the Person API
}

Requesting an individual from the server:
person_id = 2373686152
data = get_data_from_server('{TOP_API_URL}/person/{person_id}')

Example JSON returned from the server
{
    'id': 2373686152, 
    'name': 'Stella', 
    'birth': '9-3-1846', 
    'parent_id': 5428641880,   # use with the Family API
    'family_id': 6128784944    # use with the Family API
}


--------------------------------------------------------------------------------------
You will lose 10% if you don't detail your part 1 and part 2 code below

Describe how to speed up part 1

All people/persons in a family are fetched in parallel using threads.
When the DFS recurses into the husband's and wife's parent families, both branches are sent
as separate threads so both lineages are explored concurrently instead of one at a time.


Describe how to speed up part 2

All family IDs are fetched simultaneously using one thread per family.
Within each family fetch, the husband, wife, and every child are also fetched in parallel threads.
Thus, an entire generation is fetched at once, and the number of round-trips to the server
is reduced to the number of generations instead of the number of families.


Extra (Optional) 10% Bonus to speed up part 3

Same level-by-level BFS as part 2, but a threading.Semaphore(5) is given to every helper.
Thus each helper acquires the semaphore before calling get_data_from_server and
releases it immediately after, capping the number of concurrent server connections at 5,
all while still keeping all threads alive and queued to run as soon as a slot is free!

"""
import threading
from common import *


# -----------------------------------------------------------------------------
def depth_fs_pedigree(family_id, tree):
    # KEEP this function even if you don't implement it

    visited_lock = threading.Lock()
    visited = set()
    tree_lock = threading.Lock()

    def _fetch_person(pid, results, idx):
        data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
        if data:
            person = Person(data)
            with tree_lock:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)
            results[idx] = person

    def _dfs(fam_id):
        if fam_id is None:
            return

        with visited_lock:
            if fam_id in visited:
                return
            visited.add(fam_id)

        data = get_data_from_server(f'{TOP_API_URL}/family/{fam_id}')
        if not data:
            return

        family = Family(data)
        with tree_lock:
            tree.add_family(family)

        # Collect all person IDs: husband at [0], wife at [1], then the children
        husband_id = family.get_husband()
        wife_id = family.get_wife()
        person_ids = [pid for pid in [husband_id, wife_id] + family.get_children() if pid]
        results = [None] * len(person_ids)

        person_threads = [
            threading.Thread(target=_fetch_person, args=(pid, results, i))
            for i, pid in enumerate(person_ids)
        ]
        for t in person_threads:
            t.start()
        for t in person_threads:
            t.join()

        # Recurse into husband's and wife's parent families concurrently
        recurse_threads = []
        for idx, pid in enumerate([husband_id, wife_id]):
            if pid and results[idx] is not None:
                parent_fam_id = results[idx].get_parentid()
                if parent_fam_id:
                    t = threading.Thread(target=_dfs, args=(parent_fam_id,))
                    recurse_threads.append(t)
                    t.start()

        for t in recurse_threads:
            t.join()

    _dfs(family_id)


# -----------------------------------------------------------------------------
def breadth_fs_pedigree(family_id, tree):
    # KEEP this function even if you don't implement it

    visited_lock = threading.Lock()
    visited = {family_id}
    tree_lock = threading.Lock()

    def _fetch_person(pid, results, idx):
        data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
        if data:
            person = Person(data)
            with tree_lock:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)
            results[idx] = person

    def _fetch_family(fam_id, next_level, next_lock):
        data = get_data_from_server(f'{TOP_API_URL}/family/{fam_id}')
        if not data:
            return

        family = Family(data)
        with tree_lock:
            tree.add_family(family)

        husband_id = family.get_husband()
        wife_id = family.get_wife()
        person_ids = [pid for pid in [husband_id, wife_id] + family.get_children() if pid]
        results = [None] * len(person_ids)

        person_threads = [
            threading.Thread(target=_fetch_person, args=(pid, results, i))
            for i, pid in enumerate(person_ids)
        ]
        for t in person_threads:
            t.start()
        for t in person_threads:
            t.join()

        # Collect parent family IDs for husband and wife for the next BFS level
        for idx, pid in enumerate([husband_id, wife_id]):
            if pid and results[idx] is not None:
                parent_fam_id = results[idx].get_parentid()
                if parent_fam_id:
                    with visited_lock:
                        if parent_fam_id not in visited:
                            visited.add(parent_fam_id)
                            with next_lock:
                                next_level.append(parent_fam_id)

    current_level = [family_id]

    while current_level:
        next_level = []
        next_lock = threading.Lock()

        level_threads = [
            threading.Thread(target=_fetch_family, args=(fid, next_level, next_lock))
            for fid in current_level
        ]
        for t in level_threads:
            t.start()
        for t in level_threads:
            t.join()

        current_level = next_level


# -----------------------------------------------------------------------------
def breadth_fs_pedigree_limit5(family_id, tree):
    # KEEP this function even if you don't implement it
    # Limit number of concurrent connections to the FS server to 5

    semaphore = threading.Semaphore(5)
    visited_lock = threading.Lock()
    visited = {family_id}
    tree_lock = threading.Lock()

    def _fetch_server(url):
        semaphore.acquire()
        data = get_data_from_server(url)
        semaphore.release()
        return data

    def _fetch_person(pid, results, idx):
        data = _fetch_server(f'{TOP_API_URL}/person/{pid}')
        if data:
            person = Person(data)
            with tree_lock:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)
            results[idx] = person

    def _fetch_family(fam_id, next_level, next_lock):
        data = _fetch_server(f'{TOP_API_URL}/family/{fam_id}')
        if not data:
            return

        family = Family(data)
        with tree_lock:
            tree.add_family(family)

        husband_id = family.get_husband()
        wife_id = family.get_wife()
        person_ids = [pid for pid in [husband_id, wife_id] + family.get_children() if pid]
        results = [None] * len(person_ids)

        person_threads = [
            threading.Thread(target=_fetch_person, args=(pid, results, i))
            for i, pid in enumerate(person_ids)
        ]
        for t in person_threads:
            t.start()
        for t in person_threads:
            t.join()

        # Collect parent family IDs for husband and wife for the next BFS level
        for idx, pid in enumerate([husband_id, wife_id]):
            if pid and results[idx] is not None:
                parent_fam_id = results[idx].get_parentid()
                if parent_fam_id:
                    with visited_lock:
                        if parent_fam_id not in visited:
                            visited.add(parent_fam_id)
                            with next_lock:
                                next_level.append(parent_fam_id)

    current_level = [family_id]

    while current_level:
        next_level = []
        next_lock = threading.Lock()

        level_threads = [
            threading.Thread(target=_fetch_family, args=(fid, next_level, next_lock))
            for fid in current_level
        ]
        for t in level_threads:
            t.start()
        for t in level_threads:
            t.join()

        current_level = next_level