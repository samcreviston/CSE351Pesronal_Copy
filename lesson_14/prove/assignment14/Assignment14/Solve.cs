using System.Collections.Concurrent;
using Newtonsoft.Json.Linq;

namespace Assignment14;

public static class Solve
{
    private static readonly HttpClient HttpClient = new()
    {
        Timeout = TimeSpan.FromSeconds(180)
    };
    public const string TopApiUrl = "http://127.0.0.1:8123";

    // This function retrieves JSON from the server
    public static async Task<JObject?> GetDataFromServerAsync(string url)
    {
        try
        {
            var jsonString = await HttpClient.GetStringAsync(url);
            return JObject.Parse(jsonString);
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine($"Error fetching data from {url}: {e.Message}");
            return null;
        }
    }

    // This function takes in a person ID and retrieves a Person object
    // Hint: It can be used in a "new List<Task<Person?>>()" list
    private static async Task<Person?> FetchPersonAsync(long personId)
    {
        var personJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/person/{personId}");
        return personJson != null ? Person.FromJson(personJson.ToString()) : null;
    }

    // This function takes in a family ID and retrieves a Family object
    // Hint: It can be used in a "new List<Task<Family?>>()" list
    private static async Task<Family?> FetchFamilyAsync(long familyId)
    {
        var familyJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/family/{familyId}");
        return familyJson != null ? Family.FromJson(familyJson.ToString()) : null;
    }
    
    // =======================================================================================================
    public static async Task<bool> DepthFS(long familyId, Tree tree)
    {
        // Note: invalid IDs are zero not null
        var visited = new HashSet<long>();
        var visitedLock = new object();
        var treeLock = new object();
        var resultLock = new object();
        var successful = true;
        // Limit requests because 44 concurrent requests crashed the Python server.
        using var requestSemaphore = new SemaphoreSlim(30);

        void FetchPerson(long personId, Person?[] people, int index)
        {
            try
            {
                requestSemaphore.Wait();
                Person? person;
                try
                {
                    person = FetchPersonAsync(personId).GetAwaiter().GetResult();
                }
                finally
                {
                    requestSemaphore.Release();
                }

                if (person == null)
                {
                    lock (resultLock) successful = false;
                    return;
                }

                lock (treeLock)
                {
                    if (!tree.DoesPersonExist(person.Id))
                    {
                        tree.AddPerson(person);
                    }
                }

                people[index] = person;
            }
            catch (Exception)
            {
                lock (resultLock) successful = false;
            }
        }

        void SearchFamily(long currentFamilyId)
        {
            if (currentFamilyId == 0) return;

            lock (visitedLock)
            {
                if (!visited.Add(currentFamilyId)) return;
            }

            Family? family;
            try
            {
                requestSemaphore.Wait();
                try
                {
                    family = FetchFamilyAsync(currentFamilyId).GetAwaiter().GetResult();
                }
                finally
                {
                    requestSemaphore.Release();
                }
            }
            catch (Exception)
            {
                lock (resultLock) successful = false;
                return;
            }

            if (family == null)
            {
                lock (resultLock) successful = false;
                return;
            }

            lock (treeLock)
            {
                if (!tree.DoesFamilyExist(family.Id))
                {
                    tree.AddFamily(family);
                }
            }

            var personIds = new[] { family.HusbandId, family.WifeId }
                .Concat(family.Children)
                .Where(id => id != 0)
                .ToList();
            var people = new Person?[personIds.Count];
            var personThreads = personIds
                .Select((id, index) => new Thread(() => FetchPerson(id, people, index)))
                .ToList();

            personThreads.ForEach(thread => thread.Start());
            personThreads.ForEach(thread => thread.Join());

            var parentThreads = new List<Thread>();
            for (var index = 0; index < 2; index++)
            {
                var personIndex = personIds.IndexOf(index == 0 ? family.HusbandId : family.WifeId);
                if (personIndex >= 0 && people[personIndex]?.ParentId is long parentId && parentId != 0)
                {
                    parentThreads.Add(new Thread(() => SearchFamily(parentId)));
                }
            }

            parentThreads.ForEach(thread => thread.Start());
            parentThreads.ForEach(thread => thread.Join());
        }

        SearchFamily(familyId);
        return successful;
    }

    // =======================================================================================================
    public static async Task<bool> BreadthFS(long famid, Tree tree)
    {
        // Note: invalid IDs are zero not null
        var visited = new HashSet<long>();
        var visitedLock = new object();
        var treeLock = new object();
        var resultLock = new object();
        var successful = true;
        // Limit requests because 44 concurrent requests crashed the Python server.
        using var requestSemaphore = new SemaphoreSlim(30);

        void FetchPerson(long personId, Person?[] people, int index)
        {
            try
            {
                requestSemaphore.Wait();
                Person? person;
                try
                {
                    person = FetchPersonAsync(personId).GetAwaiter().GetResult();
                }
                finally
                {
                    requestSemaphore.Release();
                }

                if (person == null)
                {
                    lock (resultLock) successful = false;
                    return;
                }

                lock (treeLock)
                {
                    if (!tree.DoesPersonExist(person.Id))
                    {
                        tree.AddPerson(person);
                    }
                }

                people[index] = person;
            }
            catch (Exception)
            {
                lock (resultLock) successful = false;
            }
        }

        void FetchFamily(long currentFamilyId, List<long> nextLevel, object nextLevelLock)
        {
            Family? family;
            try
            {
                requestSemaphore.Wait();
                try
                {
                    family = FetchFamilyAsync(currentFamilyId).GetAwaiter().GetResult();
                }
                finally
                {
                    requestSemaphore.Release();
                }
            }
            catch (Exception)
            {
                lock (resultLock) successful = false;
                return;
            }

            if (family == null)
            {
                lock (resultLock) successful = false;
                return;
            }

            lock (treeLock)
            {
                if (!tree.DoesFamilyExist(family.Id))
                {
                    tree.AddFamily(family);
                }
            }

            var personIds = new[] { family.HusbandId, family.WifeId }
                .Concat(family.Children)
                .Where(id => id != 0)
                .ToList();
            var people = new Person?[personIds.Count];
            var personThreads = personIds
                .Select((id, index) => new Thread(() => FetchPerson(id, people, index)))
                .ToList();

            personThreads.ForEach(thread => thread.Start());
            personThreads.ForEach(thread => thread.Join());

            foreach (var parentPersonId in new[] { family.HusbandId, family.WifeId })
            {
                var personIndex = personIds.IndexOf(parentPersonId);
                if (personIndex < 0 || people[personIndex]?.ParentId is not long parentId || parentId == 0) continue;

                lock (visitedLock)
                {
                    if (!visited.Add(parentId)) continue;
                }

                lock (nextLevelLock)
                {
                    nextLevel.Add(parentId);
                }
            }
        }

        if (famid == 0) return false;

        lock (visitedLock) visited.Add(famid);
        var currentLevel = new List<long> { famid };

        while (currentLevel.Count > 0)
        {
            var nextLevel = new List<long>();
            var nextLevelLock = new object();
            var familyThreads = currentLevel
                .Select(id => new Thread(() => FetchFamily(id, nextLevel, nextLevelLock)))
                .ToList();

            familyThreads.ForEach(thread => thread.Start());
            familyThreads.ForEach(thread => thread.Join());
            currentLevel = nextLevel;
        }

        return successful;
    }
}
