import random
import time
import multiprocessing as mp

#practicing with processes in python for parallelism

global_total = 0

def do_a_lot_of_work():
    # print("Starting work")
    # time.sleep(4 + 3 * random.random())
    # print("Finished work")

    print("Starting work")
    total = 0
    x = 0
    for i in range(100000000):
        x += 1
        total += x

    global_total += total
    print("Finished work: ", total)
    conn.send(total)

def main():
    global global_total

    processes = []
    end_connections = []
    for _ in range(5):
        conn1, conn2 = mp.Pipe()
        p = mp.Process(target=do_a_lot_of_work, args=(conn1,))
        p.start()
        processes.append(p)
        end_connections.append(conn2)

    for conn in end_connections: 
        print("Print before received")
        global_total += conn.recv()

    print("Global total: ", global_total)

if __name__ == '__main__':
    main()