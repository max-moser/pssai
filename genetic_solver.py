import random
import datetime

PARAMETERS = {'population_size': 100, 'survivor_size': 5, 'mutation_possibility': 0.0015, 'number_of_generations': 30000}
problem_instance = None
dbg = True


def debug_print(*args, **kwargs):
    if dbg:
        print(*args, **kwargs)

#TODO REMOVE ME?
class Validity:
    def __init__(self, valid=True, problem_at_day=None, problem_tool=None, involved_requests=None):
        self.valid = valid
        self.day = problem_at_day
        self.tool = problem_tool
        self.involved_requests = involved_requests

    def __bool__(self):
        return self.valid


class InOut:
    def __init__(self, in_=0, out_=0):
        self.in_ = in_
        self.out_ = out_

    def add_in(self, value):
        self.in_ += value

    def add_out(self, value):
        self.out_ += value

    def __str__(self):
        return 'INOUT (' + str(self.in_) + ', ' + str(self.out_) + ')'


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


    def get_tool_usages(self):
        day_list = self.day_list
        # usage:
        # Key:   TOOL ID
        # Value: List of length = len(day_list),
        #         each index denotes how many tools are required at that day
        usage = {}
        for tool_id in problem_instance['tools'].keys():
            usage[tool_id] = [0 for _ in day_list]

        # walk through every day
        for (idx, req_dict) in enumerate(day_list):

            # for each day, walk through every request on that day
            for (req_id, req_state) in req_dict.items():

                # calculate the variables that we need
                request = problem_instance['requests'][req_id]
                tool_id = request.tool_id
                delivery_amount = 0
                fetch_amount = 0

                # if it's the beginning of the request (i.e. delivery), add to the delivery amount
                # else to the fetch amount
                if req_state == 'deliver':
                    delivery_amount = request.num_tools
                else:
                    fetch_amount = request.num_tools
                # assuming that we are lucky, we can fetch tools and directly deliver them to another customer
                usage[tool_id][idx] += (delivery_amount - fetch_amount)

            # don't forget to take those tools into account which are still at a customer's place
            for tool_id in problem_instance['tools'].keys():
                if idx > 0:
                    usage[tool_id][idx] += usage[tool_id][idx - 1]

        return usage

    #TODO REMOVE ME?
    def get_problems_for_tool(self, tool_id):
        """Calculate a list of problems for the tool_id

        :param tool_id:
        :return:
        """
        usages = self.get_tool_usages()[tool_id]
        available = problem_instance['tools'][tool_id].num_available
        problems = []

        for (day, usage) in enumerate(usages):
            involved_requests = []
            uses = usage

            for request in problem_instance['requests']:
                if request.first_day <= day <= request.last_day:
                    involved_requests.append(request)

            if usage > available:
                problems.append((day, uses, available, involved_requests))

        return problems

    #TODO REMOVE ME?
    def is_valid(self):
        usages = self.get_tool_usages()

        for tool_id in problem_instance['tools'].keys():
            available = problem_instance['tools'][tool_id].num_available

            for usage in usages[tool_id]:
                if usage > available:
                    return False

        return True


    def fitness_heuristic(self):
        max_cars = 0
        sum_cars = 0
        sum_distance = 0
        tsp_per_day  = []

        tools_in_out   = [{} for _ in range(problem_instance['days'])]
        optimistic_max = {}

        for (day_index, requests_on_day) in enumerate(self.day_list):
            cars = []

            # initialise the deliver/fetch tuple
            for tool_key in problem_instance['tools'].keys():
                tools_in_out[day_index].update({tool_key:InOut(0, 0)})
                optimistic_max[tool_key] = 0

            # calculate the deliver/fetch tuple for each day
            for (req_id, req_status) in requests_on_day.items():
                tool_request = problem_instance['requests'][req_id]
                tool_id = tool_request.tool_id
                in_out = tools_in_out[day_index][tool_id]

                if req_status == 'fetch':
                    in_out.add_in(tool_request.num_tools)
                else:
                    in_out.add_out(tool_request.num_tools)

        for (day_index, requests_on_day) in enumerate(self.day_list):
            pass
            for (req_id, req_status) in requests_on_day.items():
                request = problem_instance['requests'][req_id]

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

        return 1
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

    def get_extended_daylist(self):
        '''
        create day_list of length days, where all the currently running requests
        (=the tools are at the customer's place)are included
        :return:
        '''
        new_daylist = [{} for _ in range(problem_instance['days'])]
        for (day_idx, requests_on_day) in enumerate(self.day_list):
            new_daylist[day_idx].update(requests_on_day)
            if day_idx != 0:
                # append all the elems from the last day, which do not have the value 'fetch'
                # and are not on the current day (so they are still running)
                new_daylist[day_idx].update({key: 'running' for (key, value) in new_daylist[day_idx - 1].items()
                     if (value != 'fetch') and not (key in requests_on_day)})

        return new_daylist


    def repair(self):
        usages = self.get_tool_usages()
        print("\nusages:", usages)

        # create an extended datastructure from day_list, with all the tools currently at the customer's place
        extended_daylist = self.get_extended_daylist()

        # loop over each tool, and look for problems. This approach works, because the tools don't interfere with each other
        for (tool_id, usage_on_day) in usages.items():

            # get the largest peak and its day + the max available for the tool
            print("repair() tool: " + str(tool_id) + ", usage_on_day: " + str(usage_on_day))
            largest_peak_day, largest_peak = max(enumerate(usage_on_day), key=lambda p: p[1])
            available = problem_instance['tools'][tool_id].num_available

            # while the largest peak is greater than allowed, reduce it!
            while largest_peak > available:
                print("largest_peak: " + str(largest_peak))
                # get all the requests from this day and this tool.
                request_list = {req_id: req_status for (req_id, req_status) in extended_daylist[largest_peak_day].items()
                                if (problem_instance['requests'][req_id].tool_id == tool_id) and (req_status != 'fetch')}
                # and sort them by num_tools descending
                request_list = sorted(request_list.items(),
                                      key=lambda x: problem_instance['requests'][x[0]].num_tools, reverse=True)

                #print("sorted request list" + str(request_list))

                #try to move a tool of the request_list, accept the movement, if we reduce the largest peak
                for (req_id, req_status) in request_list:

                    possible_moves_for_request = choose_request_to_move(largest_peak_day, req_id)
                    successful_move = len(possible_moves_for_request) != 0

                    print("request_id: " + str(req_id) + ", possible_moves: " + str(possible_moves_for_request) + "\n")
                    #print(successful_move)

                    for possible_start_day in possible_moves_for_request:
                        request_length = problem_instance['requests'][req_id].num_days
                        first_day      = problem_instance['requests'][req_id].first_day
                        last_day       = problem_instance['requests'][req_id].last_day
                        num_tools      = problem_instance['requests'][req_id].num_tools
                        old_start_day  = self.find_start_day_of_request(req_id, first_day, last_day)

                        # check the days, which have changed (= days between new start day and old start day
                        # and old end day and new end day)
                        # if there is no larger peak, then our move is successful
                        successful_move = True
                        for day_idx in range(first_day, last_day + 1):
                            if (day_idx != largest_peak_day) and \
                                (((day_idx >= possible_start_day) and (day_idx < old_start_day)) or
                                 ((day_idx > old_start_day+request_length) and (day_idx <= possible_start_day+request_length))):
                                if usage_on_day[day_idx] + num_tools > largest_peak:
                                    successful_move = False
                                    break

                        if successful_move:
                            self.persist_successful_move(first_day, last_day, extended_daylist, req_id,
                                                         possible_start_day, request_length)
                            break

                    if successful_move:
                        break

                if not successful_move:
                    print("greedy repair did not work!")
                    return


            # TODO could update usages manually => performance
                usages = self.get_tool_usages()
                largest_peak_day, largest_peak = max(enumerate(usages[tool_id]), key=lambda p: p[1])


    def find_start_day_of_request(self, request_id, first_day, last_day):
        for day_idx in range (first_day, last_day + 1):
            if request_id in self.day_list:
                return day_idx

        return -1

    def persist_successful_move(self, first_day, last_day, extended_daylist, req_id, possible_start_day, request_length):
        # change self.day_list and extended_daylist
        active = False
        for day_idx in range(first_day, last_day + 1):
            # first, remove the entries
            self.day_list   [day_idx].pop(req_id, None)
            extended_daylist[day_idx].pop(req_id, None)

            # we are between start day and end day
            if active:
                extended_daylist[day_idx][req_id] = 'running'

            # we are on the start day
            if day_idx == possible_start_day:
                extended_daylist[day_idx][req_id] = 'deliver'
                self.day_list   [day_idx][req_id] = 'deliver'
                active = True

            # we are on the end day
            if day_idx == possible_start_day + request_length:
                extended_daylist[day_idx][req_id] = 'fetch'
                self.day_list   [day_idx][req_id] = 'fetch'
                active = False

def choose_request_to_move(largest_peak_day, req_id):
    ''' for a certain tool id, find possible movements of requests to move them away from the peak day.
    :param largest_peak_day:
    :param req_id:
    :return: a list with all possible movements of a request, to move the request out of the way of the largest peak day
    '''
    possible_start_days = []

    # loop over possible start days
    request_length = problem_instance['requests'][req_id].num_days
    first_day      = problem_instance['requests'][req_id].first_day
    last_day       = problem_instance['requests'][req_id].last_day
    print("choose_req_to_move() first_day: " + str(first_day) + ", last_day: " + str(last_day))

    # check if we could move the request, so that the tools are not at the customer at the collision day.
    for day in range(first_day, last_day+ 1):

        print("day:", day, "dar+req_len:", day+request_length, "largest_peak_day:", largest_peak_day)
        # to not collide with the peak-day, the request has to either end before or start after the collision day
        if ((day + request_length) < largest_peak_day) or (day > largest_peak_day):
            possible_start_days.append(day)

    return possible_start_days


def initial_population(population_size):
    """Create the initial population for the genetic algorithm

    :return: a list of candidates
    """

    # for each request, pick a random starting day and the corresponding end day
    population = []
    for i in range(0, population_size):
        day_list = [{} for _ in range(problem_instance['days'])]

        for key, request in problem_instance['requests'].items():
            start_day = random.randrange(request.first_day, request.last_day + 1) # randrange excludes the stop point of the range.
            day_list[start_day]                   [request.id] = 'deliver'
            day_list[start_day + request.num_days][request.id] = 'fetch'

        candidate = Candidate(day_list)
        #print(candidate.get_tool_usages())
        candidate.repair()
        #print(candidate.get_extended_daylist())
        population.append(candidate)
    return population


def combine(a, b):
    """Let Candidates a and b create a child element, inheriting some characteristics of each

    :param a:
    :param b:
    :return:
    """

    new_candidate = [{} for _ in range(problem_instance['days'])]
    for (request_id, request) in problem_instance['requests'].items():
        r = random.random()

        if r < 0.5: # use the startday and endday from candidate a
            chosen_candidate = a
        else: # use the startday and endday from candidate b
            chosen_candidate = b

        for day_idx in range(request.first_day, request.last_day + 1):
            if request_id in chosen_candidate.day_list[day_idx]:
                new_candidate[day_idx]                   [request_id] = 'deliver'
                new_candidate[day_idx + request.num_days][request_id] = 'fetch'

    new_candidate = Candidate(new_candidate)
    new_candidate.repair() # repair the candidate
    return new_candidate


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
    #[print(str(p) + '\n') for p in population[0].day_list]

    #new_candidate = combine(population[0], population[1])
    #print(population[0])
    #print("\n", population[1])
    #print("\n", new_candidate)

    for i in range(1):# TODO range(0, PARAMETERS['number_of_generations']):
        debug_print ('\nIteration: =====' + str(i) + '=======')
        sum_fitness_values = sum(p.fit for p in population)
        debug_print(sum_fitness_values)

        fitness_range = make_fitness_range(population)
        debug_print(fitness_range)

        # create new population through crossover
        new_population = []
        for i in range(PARAMETERS['population_size'] - PARAMETERS['survivor_size']):

            # select crossover candidates (candidates with higher fitness have a higher chance to get reproduced)
            (one, two) = find_mating_pair(fitness_range, sum_fitness_values)
            new_candidate = combine(one, two)
            # mutate (happens randomly)
            new_candidate.mutate()

            if new_candidate in population: # TODO can this still happen often enough?
                debug_print('WHAT IS HAPPENING')
                i -= 1
                continue

            #debug_print('1: ', str(one))
            #debug_print('2: ', str(two))
            #debug_print('Combined: ', new_candidate)
            new_population.append(new_candidate)

        # select survivors (the best ones survive)
        population = sorted(population, key=lambda p: p.fit)[-PARAMETERS['survivor_size']:]
        new_population.append(population)

        #debug_print('Population after mutation: ' + str([str(p) for p in population]))
        debug_print('Best: '  + str(population[-1:][0]))
        debug_print('Worst: ' + str(population[0]))

    end = datetime.datetime.now()
    print('Done: ' + end.isoformat())
    print('Took me: ' + str((end - start).seconds) + 's')


