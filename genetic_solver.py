import operator
import functools
import random
import datetime

PARAMETERS = {'population_size': 100, 'mutation_possibility': 0.25, 'number_of_generations': 30000, 'survivor_size': 5}
problem_instance = None
dbg = True

def debug_print(*args, **kwargs):
    if dbg:
        print(*args, **kwargs)


class Candidate:
    def __init__(self, day_list, fitness_=None):
        # ctor
        self.day_list = day_list
        if fitness_ is not None:
            self.fit = fitness_
        else:
            self.fit = self.fitness_heuristic()

    def __str__(self):
        return 'CANDIDATE (' + str(self.fit) + '): ' + str(self.day_list)

    def __eq__(self, other):
        return self.day_list == other.day_list

    def fitness_heuristic(self):
        max_cars = 0
        sum_cars = 0
        sum_distance = 0
        tsp_per_day = []
        for day in self.day_list:
            cars = []
            for request in day:
                # TODO get no. cars, get tsp
                # - auslastung der autos
                # - nearest neighbour (+ depotbesuche dazwischen erlaubt)
                # - tools mit dem gleichen typ mit dem gleichen auto machen wenn möglich (=> weniger tools nötig)
                break
            sum_cars += len(cars)
            if len(cars) > max_cars:
                max_cars = len(cars)

        max_tools = {}#[0 for _ in range(len(problem_instance['tools']))]
        for k in problem_instance['tools'].keys():
            max_tools[k] = 0

        for tsp in tsp_per_day:
            for request in tsp:
                # TODO
                break

        sum_tool_costs = 0
        for tool in max_tools:
            break
            # TODO sum_tool_costs += tool.max * problem_instance['tools'][tool.id].price

        return 0
        # return max_cars * cars_per_day + \
        #        sum_cars * cars_per_day + \
        #        sum_distance * distance_cost + \
        #        sum_tool_costs

    def mutate(self):
        """Perform random mutations on Candidate a

        :return:
        """

        r = random.random()

        if r < PARAMETERS['mutation_possibility']:
            # TODO
            return


def initial_population(population_size):
    """Create the initial population for the genetic algorithm

    :return: a list of candidates
    """

    # for each request, pick a random starting day and the corresponding end day
    population = []
    for i in range(0, population_size):
        day_list = [[] for _ in range(problem_instance['days'])]
        for key, request in problem_instance['requests'].items():
            start_day = random.randrange(request.first_day, request.last_day + 1) # randrange excludes the stop point of the range.
            day_list[start_day]                   .append({'id': request.id, 'return': False})
            day_list[start_day + request.num_days].append({'id': request.id, 'return': True })

        population.append(Candidate(day_list))
    return population


def combine(a, b):
    """Let Candidates a and b create a child element, inheriting some characteristics of each

    :param a:
    :param b:
    :return:
    """

    # TODO recombination has to be smart (check if some requests are now duplicated or missing,
    # TODO or the start/end day requirement is violated
    # TODO dunno if this kind of recombination is still smart, or if there would be some better way
    combined_content = ''
    for idx in range(0, 10):
        r = random.random()
        if r < 0.5:
            combined_content += a.content[idx]
        else:
            combined_content += b.content[idx]

    return Candidate(combined_content)


def find_mating_pair(values, scale, blocked_values=None):
    """From the values list, find a pair which is not in the blocked_list.

    :param values:
    :param scale:
    :param blocked_values:
    :return: A tuple of Candidates
    """

    if len(values) < 2:
        raise Exception('Population too small')

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


def solve_problem(problem):
    start = datetime.datetime.now()
    print('Starting now: ' + start.isoformat())

    global problem_instance
    problem_instance = problem

    #create initial population
    population = initial_population(PARAMETERS['population_size'])
    population = sorted(population, key=lambda p: p.fit)
    population_size = len(population)
    #debug_print([str(p) for p in population])
    [print(str(p) + '\n') for p in population[0].day_list]

    '''for i in range(0, 30000):
        debug_print ('\nIteration: =====' + str(i) + '=======')
        sum_fitness_values = functools.reduce(operator.add, [p.fit for p in population], 0)
        # debug_print(sum_fitness_values)

        fitness_range = make_fitness_range(population)
        
        # crossover
        # select crossover candidates (candidates with higher fitness have a higher chance to get reproduced)
        (one, two) = find_mating_pair(fitness_range, sum_fitness_values)

        combined = combine(one, two)

        # mutate (happens randomly)
        combined.mutate()

        if combined in population:
            debug_print('WHAT IS HAPPENING')
            continue

        debug_print('1: ' + str(one))
        debug_print('2: ' + str(two))
        debug_print('Combined: ' + combined.content)

        # select survivors (the best ones survive)
        population.append(combined)
        population = sorted(population, key=lambda p: p.fit)[-population_size:]
        debug_print('Population after mutation: ' + str([str(p) for p in population]))
        debug_print('Best: ' + str(population[-1:][0]))
        debug_print('Worst: ' + str(population[0]))
'''

    end = datetime.datetime.now()
    print('Done: ' + end.isoformat())
    print('Took me: ' + str((end - start).seconds) + 's')


