import time
import threading
count = 0

# 

def do_work(name:str, lock:threading.Lock):
    lock.acquire()
    print(f"{name}: Starting work...")
    lock.release()
    time.sleep(2)
    # count should be locked because it has multiple steps that could be interupted by another thread, thus resulting is a race condition and lower count than expected
    with lock:
        count += 1
    with lock:
        print(f"{name}: Work completed!")

def main():
    # lock class
    l = threading.Lock()
    # thread class
    t1 = threading.Thread(target=do_work, args=('T1', l))
    t2 = threading.Thread(target=do_work, args=('T2', l))
    t3 = threading.Thread(target=do_work, args=('T3', l))
    t1.start()
    t2.start()
    t3.start()
    l.acquire()
    print("Main thread is doing other work...")
    l.release()
    t1.join()
    t2.join()
    t3.join()
    print(f"Main: Total count: {count}")


if __name__ == "__main__":
    main()