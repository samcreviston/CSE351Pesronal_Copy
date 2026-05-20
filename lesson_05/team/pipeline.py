import random
import time
import multiprocessing as mp

def do_a_lot_of_work(conn, q, barrier, value):
    print('do something important')
    total = 0
    for x in range(500_000_000):
        x += 1
        total += x
        # value.value += x # BAD DON'T DO THIS

    print(f'finished important work: {total}')
    conn.send(total)
    q.put(total)
    # value.value += total # GOOD WAY TO DO THIS
    print(f'Process {mp.current_process().pid} value: {value.value}')
    if barrier.wait() == 0:
        q.put(None)


# put our main code
def main():
    total = 0
    q = mp.Queue()
    NUM_PROCESSES = 5
    barrier = mp.Barrier(NUM_PROCESSES)
    value = mp.Value('l', 0)
    # p0 = mp.Process(target=do_a_lot_of_work, args=())
    # p1 = mp.Process(target=do_a_lot_of_work, args=())
    # p0.start()
    # p1.start()
    # p0.join()
    # p1.join()
    # processes = [mp.Process(target=do_a_lot_of_work, args=()) for _ in range(5)]
    processes = []
    end_connections = []
    for _ in range(NUM_PROCESSES):
        conn1, conn2 = mp.Pipe()
        p = mp.Process(target=do_a_lot_of_work, args=(conn1, q, barrier, value))
        p.start()
        processes.append(p)
        end_connections.append(conn2)
    #
    # for p in processes:
    #     p.start()

    for conn in end_connections:
        print(f"before connect recv {total}")
        total += conn.recv()
        print(f"after connect recv {total}")

    q_total = 0
    while True:
        item = q.get()
        if item is None:
            break
        q_total += item

    for p in processes:
        p.join()

    print(f'pipe total: {total}')
    print(f'queue total: {q_total}')
    print(f'value total: {value.value}')


print(f"Process: {__name__}")


if __name__ == '__main__':
    main()