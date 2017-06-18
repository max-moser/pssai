import random
import datetime

PARAMETERS = {'population_size': 100, 'survivor_size': 5, 'mutation_possibility': 0.0015,
              'number_of_generations': 30000, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 14}
problem_instance = None
dbg = True


def debug_print(*args, **kwargs):
    if dbg:
        print(*args, **kwargs)


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
        self.valid = True  # gets set in repair()
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
        #         each index has a dictionary with two entries: min and max
        #         min denotes how many tools are minimally required at that day -
        #         by fetching tools and delivering them on the same day
        usage = {}
        for tool_id in problem_instance['tools'].keys():
            usage[tool_id] = [{'min': 0, 'max': 0} for _ in day_list]

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

                # min = assuming that we are lucky, we can fetch tools and directly deliver them to another customer
                usage[tool_id][idx]['min'] += (delivery_amount - fetch_amount)
                usage[tool_id][idx]['max'] += delivery_amount

            # don't forget to take those tools into account which are still at a customer's place
            for tool_id in problem_instance['tools'].keys():
                if idx > 0:
                    usage[tool_id][idx]['min'] += usage[tool_id][idx - 1]['min']
                    # add min in both cases (because on the next day, all the tools we fetched are at the depot!)
                    usage[tool_id][idx]['max'] += usage[tool_id][idx - 1]['min']

        return usage

    def fitness_heuristic(self):
        max_cars = 0
        sum_cars = 0
        sum_distance = 0
        tsp_per_day = []

        # first, get the 1) optimistic minimum of tools needed per day and 2) the maximum of tools needed per day
        # TODO get usage bois
        cars = []

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

        max_tools = {}  # [0 for _ in range(len(problem_instance['tools']))]
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
        """Perform a random mutation

        :return:
        """

        r = random.random()
        print("mutate")
        print(self.day_list)
        if r < PARAMETERS['mutation_possibility']:
            # TODO mutate only one request?

            while True: # find a request to mutate where first start day != last start day
                request_id = random.randrange(1, len(problem_instance['requests']) + 1)
                first_day = problem_instance['requests'][request_id].first_day
                last_day  = problem_instance['requests'][request_id].last_day
                num_days  = problem_instance['requests'][request_id].num_days

                if first_day != last_day:
                    break

            print("request to mutate:", request_id)

            while True: # find a new start day
                new_start_day = random.randrange(first_day, last_day + 1)
                old_start_day = self.find_start_day_of_request(request_id, first_day, last_day)

                print("new start day vs old start day:", new_start_day, old_start_day)

                if new_start_day != old_start_day: # change the startday and endday of the request
                    self.day_list[new_start_day]           [request_id] = 'deliver'
                    self.day_list[new_start_day + num_days][request_id] = 'fetch'
                    self.day_list[old_start_day]           .pop(request_id, None)
                    self.day_list[old_start_day + num_days].pop(request_id, None)
                    break

        print(self.day_list)


    def find_start_day_of_request(self, request_id, first_day, last_day):
        for day_idx in range(first_day, last_day + 1):
            if request_id in self.day_list:
                return day_idx

        return -1


    def get_extended_daylist(self):
        """
        create day_list of length days, where all the currently running requests
        (=the tools are at the customer's place)are included
        :return:
        """
        new_daylist = [{} for _ in range(problem_instance['days'])]
        for (day_idx, requests_on_day) in enumerate(self.day_list):
            new_daylist[day_idx].update(requests_on_day)
            if day_idx != 0:
                # append all the elems from the last day, which do not have the value 'fetch'
                # and are not on the current day (so they are still running)
                new_daylist[day_idx].update({key: 'running'
                                             for (key, value)
                                             in new_daylist[day_idx - 1].items()
                                             if (value != 'fetch') and not (key in requests_on_day)})

        return new_daylist


    # TODO REMOVE ME!
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
                request_list = {req_id: req_status for (req_id, req_status) in
                                extended_daylist[largest_peak_day].items()
                                if
                                (problem_instance['requests'][req_id].tool_id == tool_id) and (req_status != 'fetch')}
                # and sort them by num_tools descending
                request_list = sorted(request_list.items(),
                                      key=lambda x: problem_instance['requests'][x[0]].num_tools, reverse=True)

                # print("sorted request list" + str(request_list))

                # try to move a tool of the request_list, accept the movement, if we reduce the largest peak
                for (req_id, req_status) in request_list:

                    possible_moves_for_request = choose_request_to_move(largest_peak_day, req_id)
                    successful_move = len(possible_moves_for_request) != 0

                    print("request_id: " + str(req_id) + ", possible_moves: " + str(possible_moves_for_request) + "\n")
                    # print(successful_move)

                    for possible_start_day in possible_moves_for_request:
                        request_length = problem_instance['requests'][req_id].num_days
                        first_day = problem_instance['requests'][req_id].first_day
                        last_day = problem_instance['requests'][req_id].last_day
                        num_tools = problem_instance['requests'][req_id].num_tools
                        old_start_day = self.find_start_day_of_request(req_id, first_day, last_day)

                        # check the days, which have changed (= days between new start day and old start day
                        # and old end day and new end day)
                        # if there is no larger peak, then our move is successful
                        successful_move = True
                        for day_idx in range(first_day, last_day + 1):
                            if (day_idx != largest_peak_day) and \
                                    (((day_idx >= possible_start_day) and (day_idx < old_start_day)) or
                                         ((day_idx > old_start_day + request_length) and
                                              (day_idx <= possible_start_day + request_length))):

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


    # TODO REMOVE ME
    def persist_successful_move(self, first_day, last_day, extended_daylist, req_id, possible_start_day,
                                request_length):
        # change self.day_list and extended_daylist
        active = False
        for day_idx in range(first_day, last_day + 1):
            # first, remove the entries
            self.day_list[day_idx].pop(req_id, None)
            extended_daylist[day_idx].pop(req_id, None)

            # we are between start day and end day
            if active:
                extended_daylist[day_idx][req_id] = 'running'

            # we are on the start day
            if day_idx == possible_start_day:
                extended_daylist[day_idx][req_id] = 'deliver'
                self.day_list[day_idx][req_id] = 'deliver'
                active = True

            # we are on the end day
            if day_idx == possible_start_day + request_length:
                extended_daylist[day_idx][req_id] = 'fetch'
                self.day_list[day_idx][req_id] = 'fetch'
                active = False

    def repair2(self):
        # TODO remove me! => just for debugging
        # self.smallest_peak = {k: 10000000000 for k, v in problem_instance['tools'].items()}

        usages = self.get_tool_usages()
        extended_day_list = self.get_extended_daylist()

        for (tool_id, usages_per_day) in usages.items():
            indexed_usages_per_day = enumerate(usages_per_day)
            (day_idx, peak_amount) = max(indexed_usages_per_day, key=lambda x: x[1]['min'])
            tool_availability = problem_instance["tools"][tool_id].num_available

            # if the peak does not exceed the availability of the tool, we can ignore it :)
            if peak_amount['min'] <= tool_availability:
                continue

            # possibly involved requests:
            # all requests on the peak day
            possibly_involved_requests = extended_day_list[day_idx]
            involved_requests = []
            start_day_dict = {}

            # calculate the involved requests:
            # those, which are DELIVER or RUNNING
            # and actually request the wanted tool
            for req_id in possibly_involved_requests.keys():
                req_state = possibly_involved_requests[req_id]

                if req_state == "deliver" or req_state == "running":
                    req = problem_instance["requests"][req_id]

                    if req.tool_id == tool_id:
                        involved_requests.append(req)

            # calculate the possible start positions of the requests...
            for request in involved_requests:
                first_start_day = request.first_day
                last_start_day = request.last_day
                start_day_dict[request.id] = list(range(first_start_day, last_start_day + 1))

            max_depth = PARAMETERS['max_depth_start']
            while True:
                print("max_depth:", max_depth)
                repair_result = self.rec_repair2(start_day_dict, extended_day_list, 0, max_depth)

                if repair_result is None:
                    if max_depth < PARAMETERS['max_depth']:
                        max_depth += PARAMETERS['max_depth_increase']
                        continue
                    else:
                        print("WE ARE SORRY BUT YOUR PROBLEM CANNOT GET FIXED.")
                        self.valid = False
                        return
                else:
                    print("WE FIXED YOUR PROBLEM FOR YOU MATE")
                    self.valid = True
                    # to create a "normal" day-list from the extended day-list,
                    # we only need to delete the "running" entries from the latter

                    new_day_list = []
                    for requests_per_day in repair_result:
                        new_day_list.append({req_id: state for req_id, state in requests_per_day.items() if state != "running"})

                    # make the result stick
                    self.day_list = new_day_list
                    break


    def rec_repair2(self, move_dict, current_extended_daylist, depth, max_depth):
        """

        :param move_dict:
        :param current_extended_daylist:
        :return:
        """

        chosen_request = None
        max_impact = 0
        next_move_dict = move_dict.copy()
        tool_id = None
        tool_availability = None

        for req_id in move_dict:
            # if the list of possible start days is not empty...
            if move_dict[req_id]: #if not empty
                tmp_request = problem_instance["requests"][req_id]
                if tmp_request.num_tools > max_impact:
                    max_impact = tmp_request.num_tools
                    chosen_request = tmp_request
                    tool_id = chosen_request.tool_id
                    tool_availability = problem_instance["tools"][tool_id].num_available

        if chosen_request is None:
            # at this point, we have exhausted all possible moves
            return None

        # we don't want to move the same request twice in recursive calls
        next_move_dict[chosen_request.id] = []

        # look at all the possible positions for the chosen request
        for position in move_dict[chosen_request.id]:
            #print("depth, chosen request, chosen position:", depth, chosen_request, position)
            #print("move dict:", move_dict, "\n")
            tmp_ext_daylist = current_extended_daylist.copy()
            start_day = position
            end_day = position + chosen_request.num_days

            # update the extended day list:
            # remove all old occurrences of the chosen request
            # and set up the new ones
            for (day_idx, req_dict) in enumerate(tmp_ext_daylist):
                req_dict.pop(chosen_request.id, None)

                if start_day == day_idx:
                    tmp_ext_daylist[day_idx][chosen_request.id] = "deliver"
                elif end_day == day_idx:
                    tmp_ext_daylist[day_idx][chosen_request.id] = "fetch"
                elif start_day < day_idx < end_day:
                    tmp_ext_daylist[day_idx][chosen_request.id] = "running"

            # get usages for our tool and the new daylist
            tmp_usages = tool_usages_from_extended_daylist(tmp_ext_daylist)[tool_id]
            new_peak = max(tmp_usages)

            # TODO remove me => debugging
            #if new_peak < self.smallest_peak[tool_id]:
                #self.smallest_peak[tool_id] = new_peak
            #print("new peak, max_available, smallest_peak:", new_peak, tool_availability, self.smallest_peak[tool_id])

            # if this move fixed the peak, let's return the extended day list that fixed the problem
            if new_peak <= tool_availability:
                return tmp_ext_daylist

            # if we haven't repaired the problem at this stage, let's try to go deeper
            if depth < max_depth:
                deeper_result = self.rec_repair2(next_move_dict, tmp_ext_daylist, depth+1, max_depth)
                if deeper_result is not None:
                    return deeper_result

        # at this point, we have exhausted all possibilities and still not found a solution
        return None


def tool_usages_from_extended_daylist(ext_day_list):
    """Calculate the tool usages from the given extended day list.

    The result will be a dictionary with Tool IDs as keys and a list as value.
    The value list has one entry per day of the problem and the entry's value equals to the amount of tools
    required at this day as per optimistic maximum
    (i.e. tools still at a customer's place + tools requested - tools returned)
    :param ext_day_list:
    :return:
    """
    usage = {}
    for tool_id in problem_instance["tools"]:
        usage[tool_id] = [0 for day in ext_day_list]

    for (day_idx, req_dict) in enumerate(ext_day_list):
        for (req_id, req_state) in req_dict.items():
            request = problem_instance["requests"][req_id]
            tool_id = request.tool_id
            delivery_amount = 0
            running_amount = 0
            fetch_amount = 0

            if req_state == "deliver":
                delivery_amount = request.num_tools
            elif req_state == "running":
                running_amount = request.num_tools
            elif req_state == "fetch":
                fetch_amount = request.num_tools

            change_amount = (delivery_amount + running_amount) - fetch_amount
            usage[tool_id][day_idx] += change_amount

    return usage


def choose_request_to_move(largest_peak_day, req_id):
    """ for a certain tool id, find possible movements of requests to move them away from the peak day.
    :param largest_peak_day:
    :param req_id:
    :return: a list with all possible movements of a request, to move the request out of the way of the largest peak day
    """
    possible_start_days = []

    # loop over possible start days
    request_length = problem_instance['requests'][req_id].num_days
    first_day = problem_instance['requests'][req_id].first_day
    last_day = problem_instance['requests'][req_id].last_day
    print("choose_req_to_move() first_day: " + str(first_day) + ", last_day: " + str(last_day))

    # check if we could move the request, so that the tools are not at the customer at the collision day.
    for day in range(first_day, last_day + 1):

        print("day:", day, "dar+req_len:", day + request_length, "largest_peak_day:", largest_peak_day)
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
    i = 0
    while i < population_size:
        day_list = [{} for _ in range(problem_instance['days'])]

        for key, request in problem_instance['requests'].items():
            start_day = random.randrange(request.first_day,
                                         request.last_day + 1)  # randrange excludes the stop point of the range.
            day_list[start_day][request.id] = 'deliver'
            day_list[start_day + request.num_days][request.id] = 'fetch'

        candidate = Candidate(day_list)
        # print(candidate.get_tool_usages())
        candidate.repair2()
        if not candidate.valid:  # we need to create an additional candidate
            continue
        # print(candidate.get_extended_daylist())
        population.append(candidate)
        i += 1
    return population


def combine(a, b):
    """Let Candidates a and b create a child element, inheriting some characteristics of each

    :param a:
    :param b:
    :return:
    """

    new_day_list = [{} for _ in range(problem_instance['days'])]
    for (request_id, request) in problem_instance['requests'].items():
        r = random.random()

        if r < 0.5:  # use the startday and endday from candidate a
            chosen_candidate = a
        else:  # use the startday and endday from candidate b
            chosen_candidate = b

        for day_idx in range(request.first_day, request.last_day + 1):
            if request_id in chosen_candidate.day_list[day_idx]:
                new_day_list[day_idx]                   [request_id] = 'deliver'
                new_day_list[day_idx + request.num_days][request_id] = 'fetch'
                break

    new_candidate = Candidate(new_day_list)
    new_candidate.repair2()  # repair the candidate
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

    # create initial population
    population = initial_population(PARAMETERS['population_size'])
    population = sorted(population, key=lambda p: p.fit)
    debug_print("population size:", len(population))
    # debug_print([str(p) for p in population])
    # [print(str(p) + '\n') for p in population[0].day_list]

    # new_candidate = combine(population[0], population[1])
    # print(population[0])
    # print("\n", population[1])
    # print("\n", new_candidate)

    for i in range(1):  # TODO range(0, PARAMETERS['number_of_generations']):
        debug_print('\nIteration: =====' + str(i) + '=======')
        sum_fitness_values = sum(p.fit for p in population)
        debug_print(sum_fitness_values)

        fitness_range = make_fitness_range(population)
        debug_print(fitness_range)

        # create new population through crossover
        new_population = []
        i = 0
        while i < PARAMETERS['population_size'] - PARAMETERS['survivor_size']:

            # select crossover candidates (candidates with higher fitness have a higher chance to get reproduced)
            (one, two) = find_mating_pair(fitness_range, sum_fitness_values)
            new_candidate = combine(one, two)

            if not new_candidate.valid:  # we need to generate an additional candidate
                continue

            # mutate (happens randomly)
            new_candidate.mutate()

            # TODO can this still happen often enough?
            if new_candidate in population:  # we need to generate an additional candidate
                debug_print('WHAT IS HAPPENING')
                continue

            # debug_print('1: ', str(one))
            # debug_print('2: ', str(two))
            # debug_print('Combined: ', new_candidate)
            new_population.append(new_candidate)
            i += 1

        debug_print("new_population size b4 insert pop size:", len(new_population))
        # select survivors (the best ones survive)

        population = sorted(population, key=lambda p: p.fit)
        population = population[-PARAMETERS['survivor_size']:]
        debug_print("population size to insert:", len(population))

        new_population.extend(population)


        debug_print("new_population size:", len(new_population))

        # debug_print('Population after mutation: ' + str([str(p) for p in population]))
        debug_print('Best: ' + str(population[-1:][0]))
        debug_print('Worst: ' + str(population[0]))

    end = datetime.datetime.now()
    print('Done: ' + end.isoformat())
    print('Took me: ' + str((end - start).seconds) + 's')
