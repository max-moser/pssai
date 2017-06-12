import operator
import functools
import random
import datetime

dbg = True


def debug_print(*args, **kwargs):
    if dbg:
        print(*args, **kwargs)


class Candidate:
    def __init__(self, content, fitness_=None):
        # ctor
        self.content = content[0:10]
        if fitness_ is not None:
            self.fit = fitness_
        else:
            self.fit = fitness(self)

    def __str__(self):
        return "C (" + str(self.fit) + "): " + self.content

    def __eq__(self, other):
        return self.content == other.content


def initial_population(size=100):
    """Create the initial population for the genetic algorithm

    :return:
    """

    population = []
    for i in range(0, size):
        candidate = ""
        for j in range(0, 10):
            x = random.randrange(65, 91)
            candidate += chr(x)

        population.append(Candidate(candidate))
    return population


def combine(a, b):
    """Let Candidates a and b create a child element, inheriting some characteristics of each

    :param a:
    :param b:
    :return:
    """

    combined_content = ""
    for idx in range(0, 10):
        r = random.random()
        if r < 0.5:
            combined_content += a.content[idx]
        else:
            combined_content += b.content[idx]

    return Candidate(combined_content)


def fitness(a):
    """Calculate the fitness of a candidate

    :param a:
    :return:
    """
    _fitness = 0
    for c in a.content:
        _fitness += ord(c)
    return _fitness


def mutate(a):
    """Perform random mutations on Candidate a

    :param a:
    :return:
    """
    r = random.random()

    if r < 0.25:
        idx = random.randrange(0, 10)
        x = ord(a.content[idx]) + 1
        if x > 126:
            x = 126
        x = chr(x)
        a.content = a.content[0:idx] + x + a.content[(idx + 1):]
        debug_print("Mutation: " + a.content)

    return a


def find_mating_pair(values, scale, blocked_values=None):
    """From the values list, find a pair which is not in the blocked_list.

    :param values:
    :param scale:
    :param blocked_values:
    :return: A tuple of Candidates
    """

    if len(values) < 2:
        raise Exception("Population too small")

    if blocked_values is None:
        blocked_values = []

    val_0 = get_random_candidate(values, scale)
    val_1 = None

    while (val_1 is None) or (val_0 == val_1) \
            or (val_0, val_1) in blocked_values or (val_1, val_0) in blocked_values:
        val_1 = get_random_candidate(values, scale)

    return (val_0[2], val_1[2])


def get_random_candidate(values, scale):
    """Fetch a random candidate from the supplied values list.

    Generate a random value R in the range [0, SCALE) and fetch that element from the values list
    where LOWER <= R < UPPER.

    :param values: A list containing triples of the form (LOWER, UPPER, ELEMENT)
    :param scale: The sum of all fitness values
    :return: An element from the values list
    """

    r = random.random() * scale
    for v in values:
        # v[0] -> LOWER
        # v[1] -> UPPER
        if v[0] <= r < v[1]:
            return v


def make_fitness_range(values):
    """Create a list containing triples of the form (LOWER, UPPER, ELEMENT)

    :param values:
    :return:
    """
    great_range = []
    upper = 0

    for elem in values:
        lower = upper
        upper = lower + elem.fit
        great_range.append((lower, upper, elem))

    return great_range


if __name__ == "__main__":
    start = datetime.datetime.now()
    print("Starting now: " + start.isoformat())
    population = initial_population()
    # crossover
    # select crossover candidates (candidates with higher fitness have a higher chance to get reproduced)
    population = sorted(population, key=lambda p: p.fit)
    population_size = len(population)
    debug_print([str(p) for p in population])

    for i in range(0, 30_000):
        debug_print ("\nIteration: =====" + str(i) + "=======")
        sum_fitness_values = functools.reduce(operator.add, [p.fit for p in population], 0)
        # debug_print(sum_fitness_values)

        fitness_range = make_fitness_range(population)
        (one, two) = find_mating_pair(fitness_range, sum_fitness_values)

        combined = combine(one, two)

        # mutate (happens randomly)
        combined = mutate(combined)

        if combined in population:
            debug_print("WHAT IS HAPPENING")
            continue

        debug_print("1: " + str(one))
        debug_print("2: " + str(two))
        debug_print("Combined: " + combined.content)

        population.append(combined)
        population = sorted(population, key=lambda p: p.fit)[-population_size:]
        debug_print("Population after mutation: " + str([str(p) for p in population]))
        debug_print("Best: " + str(population[-1:][0]))
        debug_print("Worst: " + str(population[0]))

    end = datetime.datetime.now()
    print("Done: " + end.isoformat())
    print("Took me: " + str((end - start).seconds) + "s")

    # select survivors (the best ones survive)

