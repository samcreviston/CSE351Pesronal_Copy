using System.Diagnostics;
using System.Collections.Concurrent;

namespace assignment11;

public class Assignment11
{
    private const long START_NUMBER = 10_000_000_000;
    private const int RANGE_COUNT = 1_000_000;

    private static bool IsPrime(long n)
    {
        if (n <= 3) return n > 1;
        if (n % 2 == 0 || n % 3 == 0) return false;

        for (long i = 5; i * i <= n; i = i + 6)
        {
            if (n % i == 0 || n % (i + 2) == 0)
                return false;
        }
        return true;
    }

    public static void Main(string[] args)
    {
        const int NUM_THREADS = 10;

        // Step 1 - bounded queue (backpressure: blocks producer when full)
        var queue = new BlockingCollection<long>(NUM_THREADS * 100);

        // Step 2 - thread-safe bag to collect primes, sorted at the end
        var primes = new ConcurrentBag<long>(); 

        // Use local variables for counting since we are in a single thread.
        int numbersProcessed = 0;
        int primeCount = 0;

        Console.WriteLine("Prime numbers found:");

        var stopwatch = Stopwatch.StartNew();
        
        Thread[] workers = new Thread[NUM_THREADS];
        for (int t = 0; t < NUM_THREADS; t++)
        {
            workers[t] = new Thread(() =>
            {
                foreach(var num in queue.GetConsumingEnumerable())
                    if (IsPrime(num))
                    {
                        primes.Add(num);
                        Interlocked.Increment(ref primeCount);
                    }
            });
            workers[t].Start();
        }

        for(long i = START_NUMBER; i < START_NUMBER + RANGE_COUNT; i++)
            queue.Add(i);

        queue.CompleteAdding();

        foreach (var worker in workers)
            worker.Join();

        stopwatch.Stop();

        var sortedPrimes = primes.ToList();
        sortedPrimes.Sort();

        foreach (var p in sortedPrimes)
            Console.Write($"{p}, ");

        Console.WriteLine(); // New line after all primes are printed
        Console.WriteLine();

        // Should find 43427 primes for range_count = 1000000
        Console.WriteLine($"Numbers processed = {numbersProcessed}");
        Console.WriteLine($"Primes found      = {primeCount}");
        Console.WriteLine($"Total time        = {stopwatch.Elapsed}");        
    }
}