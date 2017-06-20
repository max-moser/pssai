import random
import datetime

PARAMETERS = {'population_size': 100, 'survivor_size': 5, 'mutation_possibility': 0.0015,
              'number_of_generations': 2, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
problem_instance = None
dbg = True


def debug_print(*args, **kwargs):
    if dbg:
        print(*args, **kwargs)


class StopOver:
    def __init__(self, customer_id, request_id, num_tools):
        self.customer_id = customer_id
        self.request_id = request_id
        self.num_tools = num_tools  # negative num_tools = fetch request, positive num_tools = deliver request

    def __str__(self):
        return "StopOver (cust, req, #tools): (" + str(self.customer_id) + ", " + str(self.request_id) + ", " + str(self.num_tools) + ")"


class Trip:
    def __init__(self):
        self.trip_distance_wo_last_stop = 0  # distance of this trip without the distance to the depot at the end
        self.stopovers = [StopOver(0, 0, 0)]  # list of requests the trip contains (0 = depot)
        self.used_tools_per_stop = {tool_id: [0] for (tool_id, tool) in problem_instance['tools'].items()}

    def convert_from_stopovers(self, stopovers):
        #print("convert_from_stopovers")
        for (day_idx, stopover) in enumerate(stopovers):
            if (day_idx != 0) and (day_idx != len(stopovers) - 1):  # do not add the depot at the start and the end
                self.try_add(stopover)
        self.finalize()

    def try_add(self, stopover):
        #print("try_add", stopover)

        # 1. sum up the distance with the additional stopover
        distance_to_stopover = problem_instance['distance'][self.stopovers[-1].customer_id][stopover.customer_id]
        distance_to_depot    = problem_instance['distance'][stopover.customer_id]          [0]
        sum_distances = self.trip_distance_wo_last_stop + distance_to_stopover + distance_to_depot

        # check if the distance is ok
        if sum_distances > problem_instance['max_trip_distance']:
            #print("exceeded max_trip_distance")
            return False

        # 2. sum up all the used tools and check if the distance is ok
        stopover_tool_id = problem_instance['requests'][stopover.request_id].tool_id
        new_num_tools = self.used_tools_per_stop.copy()

        # if the new request is a fetch request, we only have to look at the changes of today
        if stopover.num_tools < 0:
            sum_load = 0
            for (tool_id, usages) in new_num_tools.items():  # add a new day to usages list
                to_add = usages[-1]
                if tool_id == stopover_tool_id:
                    to_add += abs(stopover.num_tools)
                usages.append(to_add)
                sum_load += to_add * problem_instance['tools'][tool_id].size
            if sum_load > problem_instance['capacity']:
                #print("exceeded capacity (fetch)")
                return False

        # if the new request is a deliver request (and we have to load new tools at the depot),
        #    we have to look at all the past days
        else:
            tools_loaded = new_num_tools[stopover_tool_id][-1]
            to_add = stopover.num_tools - tools_loaded
            if to_add < 0:
                to_add = 0  # we have enough tools loaded, so we do not need to load more tools!

            # update the past days, if we had to load something at the depot
            if to_add > 0:
                for stopover_idx in range(len(self.stopovers)):  # loop over all days
                    new_num_tools[stopover_tool_id][stopover_idx] += to_add

            for (tool_id, usages) in new_num_tools.items():  # add a new day to usages list
                usages.append(usages[-1])
                if tool_id == stopover_tool_id:  # now we have to deliver the tools
                    usages.append(usages[-1] - stopover.num_tools)

            # if we had to add tools at the depot, we have to check the capacity of the past days
            if to_add > 0:
                for stopover_idx in range(len(self.stopovers) + 1):  # loop over all days (+1, since we added a new one)
                    sum_load = 0
                    for (tool_id, usages) in new_num_tools.items():
                        sum_load += usages[stopover_idx] * problem_instance['tools'][tool_id].size
                    if sum_load > problem_instance['capacity']:
                        #print("exceeded capacity (deliver)")
                        return False

        # 3. if we get here, we can add the new stop, and update the trip distance and the used tools
        self.stopovers.append(stopover)
        self.trip_distance_wo_last_stop += distance_to_stopover
        self.used_tools_per_stop = new_num_tools
        return True

    def finalize(self):
        # set complete distance
        last_stop_customer_id = self.stopovers[-1].customer_id
        self.distance = self.trip_distance_wo_last_stop + problem_instance['distance'][last_stop_customer_id][0]

        # update stopovers (return to the depot)
        self.stopovers.append(StopOver(0, 0, 0))

        # update tool usages for the last day
        for (tool_id, usages) in self.used_tools_per_stop.items():
            usages.append(usages[-1])

    def __str__(self):
        to_string = "Trip: \n"
        for stopover in self.stopovers:
            to_string += "\t" + stopover.__str__() + "\n"
        return to_string


class Candidate:
    def __init__(self, day_list, fitness_=None):
        # ctor
        self.day_list = day_list
        self.valid = True  # gets set in repair()
        self.fit = -1
        return

    def __str__(self):
        return 'CANDIDATE (' + str(self.fit) + '): ' + str(self.day_list)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.day_list == other.day_list
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

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
        cars_on_day = [[] for _ in range(problem_instance['days'])]

        # first, get the 1) optimistic minimum of tools needed per day and 2) the maximum of tools needed per day
        usages = self.get_tool_usages()
        trips_per_day = {}

        # check if we can use NN heuristic
        # we can only use NN if FOR ALL TOOLS on this day this holds: (usages[tool][day][max] <= num_tools)
        # otherwise we must make sure to fetch the tools before delivering them to not exceed the limit

        for (day_index, requests_on_day) in enumerate(self.day_list):
            tsp_per_day = []

            trips_per_day[day_index] = []
            trips_today = trips_per_day[day_index]

            # 1. find critical tools for this day
            critical_tools = []
            for (tool_id, tool) in problem_instance['tools'].items():
                if usages[tool_id][day_index]['max'] > tool.num_available:
                    critical_tools.append(tool_id)

            # 2. loop over critical tools, make tsp for critical requests
            for critical_tool_id in critical_tools:
                # how many additional tools compared to the previous day are available?
                diff_deliver_fetch = usages[critical_tool_id][day_index]['min'] if day_index == 0 else \
                    usages[critical_tool_id][day_index]['min'] - usages[critical_tool_id][day_index - 1]['min']

                # how much wiggle room do we have for this day?
                wiggle_room = problem_instance['tools'][critical_tool_id].num_available - \
                              usages[critical_tool_id][day_index]['min']

                # filter requests which contain a critical tool with this id
                critical_requests_deliver = [req_id for req_id, req_status in requests_on_day.items()
                                           if (problem_instance['requests'][req_id].tool_id == critical_tool_id) and
                                           (req_status == 'deliver')]

                critical_requests_fetch   = [req_id for req_id, req_status in requests_on_day.items()
                                           if (problem_instance['requests'][req_id].tool_id == critical_tool_id) and
                                           (req_status == 'fetch')]

                # while len(critical_requests_deliver) + len(critical_requests_fetch) > 0:
                # constraints:
                # 1. sum distance per car < max distance
                # 2. -sum(fetch) + sum(deliver) = additional tools
                #  this means for diff_deliver_fetch > 0, we load tools when leaving the depot, and return WITHOUT tools
                #  and for diff_deliver_fetch < 0, we do NOT load tools when leaving the depot, but return with tools

                # we need to fetch first, then deliver

                # order critical requests by amount, highest amount first
                critical_request_deliver_sorted = sorted(critical_requests_deliver,
                                                         key=lambda x: problem_instance['requests'][x].num_tools,
                                                         reverse=True)

                already_used_deliveries = []
                not_yet_used_deliveries = critical_request_deliver_sorted.copy()

                # set request at the end of the route
                for req_deliver_id in critical_request_deliver_sorted:

                    # this should not occur unless we added more delivery requests
                    # to the last trip (see below)
                    if req_deliver_id in already_used_deliveries:
                        continue
                    already_used_deliveries.append(req_deliver_id)
                    not_yet_used_deliveries.remove(req_deliver_id)

                    req_deliver_customer_id = problem_instance['requests'][req_deliver_id].customer_id
                    req_deliver_num_tools   = problem_instance['requests'][req_deliver_id].num_tools
                    fetch_counter            = 0
                    successful_fetch_counter = 0

                    # we start at the depot
                    route = []
                    start_at_depot = StopOver(0, 0, 0)
                    route.append(start_at_depot)

                    if critical_requests_fetch:
                        # calculate the metric, based on which we determine the fetch request to pick next
                        # metric = scaled DISTANCE x scaled DELTA
                        # where by distance we mean distance from current delivery request to the delivery request
                        #          delta: the amount of tools we fetch - tools we deliver
                        distances = {}
                        deltas = {}
                        for req_id in critical_requests_fetch:
                            req_fetch_customer_id = problem_instance["requests"][req_id].customer_id
                            dist = problem_instance["distance"][req_deliver_customer_id][req_fetch_customer_id]
                            delta = abs(problem_instance["requests"][req_fetch_customer_id].num_tools
                                        - req_deliver_num_tools)

                            distances[req_id] = dist
                            deltas[req_id] = delta

                        min_dist  = min(distances.items(), key=lambda x: x[1])[1]
                        max_dist  = max(distances.items(), key=lambda x: x[1])[1]
                        min_delta = min(deltas.items(),    key=lambda x: x[1])[1]
                        max_delta = max(deltas.items(),    key=lambda x: x[1])[1]

                        # try to fill the route with other requests before the deliver request
                        # a request fits if the delta between the num_tools is low and the distance is low
                        requests_with_metric = {}
                        for req_fetch_id in critical_requests_fetch:
                            req_fetch_customer_id = problem_instance["requests"][req_fetch_id].customer_id
                            req_fetch_distance = problem_instance['distance'][req_deliver_customer_id][req_fetch_customer_id]
                            req_fetch_delta = problem_instance['requests'][req_fetch_id].num_tools

                            # distance is mapped to a range from 1 - 4
                            # delta is mapped to a range from 1 - 10
                            # because we want to focus more on the range than the distance
                            score_distance = translate(req_fetch_distance, min_dist, max_dist, 1, 4)
                            score_delta = translate(req_fetch_delta, min_delta, max_delta, 1, 10)
                            score = score_distance * score_delta
                            requests_with_metric[req_fetch_id] = score

                        sorted_requests = sorted(requests_with_metric.items(), key=lambda x: x[1])

                        # add requests to the list (to keep this simple, all fetch req. are before deliver req.)
                        for (fetch_req_id, fetch_req_score) in sorted_requests:

                            # check if the distance is shorter than the max distance per car
                            fetch_customer_id = problem_instance['requests'][fetch_req_id].customer_id
                            fetch_num_tools   = problem_instance['requests'][fetch_req_id].num_tools

                            tmp_route = route.copy()

                            # add the (CUSTOMER_ID, REQUEST_ID) tuples to the tmp route
                            if successful_fetch_counter > 0:
                                # pretty stupid fix
                                # but otherwise we would append the delivery and depot each time
                                # that we append a new fetch
                                tmp_route.pop()
                                tmp_route.pop()

                            neg_fetch_num_tools = (-1) * abs(fetch_num_tools)
                            tmp_route.append(StopOver(fetch_customer_id, fetch_req_id, neg_fetch_num_tools))
                            tmp_route.append(StopOver(req_deliver_customer_id, req_deliver_id, req_deliver_num_tools))
                            tmp_route.append(StopOver(0, 0, 0))

                            fetch_counter += 1
                            successful_move = is_route_valid(tmp_route, critical_tool_id)
                            if successful_move:
                                # we used this fetch request up and cannot re-use it in
                                # further delivery requests
                                critical_requests_fetch.remove(fetch_req_id)
                                route = tmp_route
                                tools_returned_to_depot = tmp_route[-1].num_tools
                                successful_fetch_counter += 1

                                # if we found some route that fetches more than delivers,
                                # we're just gonna stop building up this route
                                if tools_returned_to_depot >= 0:
                                    # TODO we could try to add another delivery request and re-do the sorted_requests
                                    #      loop though this probably won't make much sense for 1 or 2 tools
                                    #      we might need to define some border at which this behaviour gets triggered
                                    break

                    if fetch_counter <= 0:
                        # if there weren't any fetch requests left, we're just gonna
                        # try to deliver and return to depot
                        route.append(StopOver(req_deliver_customer_id, req_deliver_id, req_deliver_num_tools))
                        route.append(StopOver(0, 0, 0))

                    #print("PRE:", [str(so) for so in route], end="\n")
                    route_valid = is_route_valid(route, critical_tool_id)
                    #print("POST:", [str(so) for so in route], end="\n\n")
                    if route_valid:
                        trip = Trip()
                        trip.convert_from_stopovers(route)
                        trips_today.append(trip)
                    else:
                        # at this point, I think we should just cancel this thing
                        #print("THE ROUTE SEEMS TO BE INVALID?")
                        self.valid = False
                        return -1

                # at this point, we have used up all deliver requests
                # but there were some fetch requests that were not yet used
                # so we'll just try to do a NN with them
                if critical_requests_fetch:
                    for req_fetch_crit_id in critical_requests_fetch:
                        # TODO it's a shame how these fetch requests go to waste
                        # TODO could have made better use of them with a nearest neighbour
                        crit_fetch_req = problem_instance["requests"][req_fetch_crit_id]
                        route = []

                        neg_fetch_req_num_tools = abs(crit_fetch_req.num_tools) * (-1)
                        route.append(StopOver(0, 0, 0))
                        route.append(StopOver(crit_fetch_req.customer_id, crit_fetch_req.id, neg_fetch_req_num_tools))
                        route.append(StopOver(0, 0, 0))

                        route_valid = is_route_valid(route, critical_tool_id)
                        if route_valid:
                            trip = Trip()
                            trip.convert_from_stopovers(route)
                            trips_today.append(trip)
                        else:
                            print("For some reason, could not fulfill the single fetch")
                            self.valid = False
                            return -1

                # after we have allocated all requests on that day, let's sum up how many
                # tools we "wasted" (i.e. brought to the depot without further using them)
                unused_tools = 0
                for trip in trips_today:
                    unused_tools += trip.used_tools_per_stop[critical_tool_id][-1]

                available = problem_instance["tools"][critical_tool_id].num_available
                opt_max = usages[critical_tool_id][day_index]['min']
                actual_usage = unused_tools + opt_max
                if actual_usage > available:
                    print("THE WIGGLE ROOM WAS EXHAUSTED")
                    self.valid = False
                    return -1


            # 3. loop over remaining (non critical) requests, use NN heuristic
            # 3.1 get all critical requests
            non_critical_requests = {req_id: req_status for (req_id, req_status) in requests_on_day.items()
                                        if problem_instance['requests'][req_id].tool_id not in critical_tools}

            current_trip = Trip()
            # just loop while we still have requests to to
            while non_critical_requests:
                # sort them (based on their distance to the last point in the trip)
                last_stopover_customer_id = current_trip.stopovers[-1].customer_id

                non_critical_requests_sorted = sorted(non_critical_requests.items(),
                    key=lambda x: problem_instance['distance']
                        [last_stopover_customer_id][problem_instance['requests'][x[0]].customer_id])

                # create a new stopover for the nearest neighbour (a stopover needs customer_id, request_id, num_tools)
                nn_req_id = non_critical_requests_sorted[0][0]
                nn_req_status = non_critical_requests_sorted[0][1]
                nn_customer_id = problem_instance['requests'][nn_req_id].customer_id
                nn_num_tools = problem_instance['requests'][nn_req_id].num_tools
                if nn_req_status == 'fetch':
                    nn_num_tools *= -1
                nn_stopover = StopOver(nn_customer_id, nn_req_id, nn_num_tools)

                if not current_trip.try_add(nn_stopover):  # trip is full
                    #print("try_add was false => new trip")
                    current_trip.finalize()
                    trips_today.append(current_trip)  # finalize the trip
                    current_trip = Trip()  # reset the current_trip
                    current_trip.try_add(nn_stopover)  # the first stop can never fail, unless our problem instance is faulty

                non_critical_requests.pop(nn_req_id, None)  # remove the request from the list of requests yet to assign

            current_trip.finalize()
            trips_today.append(current_trip)  # add the last trip to the array

            # loop over trips, assign them to cars
            car_idx = 0
            sum_distance_car = 0
            cars = [[]]  # list of cars with list of trips inside
            #print(trips_today)
            for trip in trips_today:
                if (sum_distance_car + trip.distance) > problem_instance['max_trip_distance']:
                    cars.append([])
                    car_idx += 1
                    sum_distance_car = 0

                cars[car_idx].append(trip)  # append trip to car
                sum_distance_car += trip.distance

            cars_on_day[day_index] = cars
            # 4. Now we have calculated all TSPs of this day
            # we can calculate the fitness, update max_tools nedded

        #print("cars_on_day", cars_on_day)

        # 5. All TSPs of all cars have been generated.
        # sum up the cars, get max_cars, sum up distance
        max_cars = 0
        sum_cars = 0
        sum_distance = 0
        max_tools_used = {tool_id: 0 for (tool_id, _) in problem_instance['tools'].items()}
        for (day_idx, cars_day) in enumerate(cars_on_day):

            if day_idx == 0:  # on the first day, we havn't used tools previously (obviously)
                max_tools_used_on_day = {tool_id: 0 for (tool_id, _) in problem_instance['tools'].items()}
            else:  # start with the min tools used from the previous day
                max_tools_used_on_day = {tool_id: usages[0] for (tool_id, usages) in usages.items()}

            sum_cars += len(cars_day)
            if len(cars_day) > max_cars:
                max_cars = len(cars_day)

            for car in cars_day:
                for trip in car:
                    for (tool_id, _) in problem_instance['tools'].items():
                        # add all the stuff we load at the depot (first stop)
                        tools_loaded_at_depot = trip.used_tools_per_stop[tool_id][0]
                        max_tools_used_on_day[tool_id] = tools_loaded_at_depot

                    sum_distance += trip.distance

            # check if the max amount of tools is bigger on this day
            for (tool_id, max_amount) in max_tools_used.items():
                if max_tools_used_on_day[tool_id] > max_amount:
                    max_tools_used[tool_id] = max_tools_used_on_day[tool_id]

        #print(max_cars)
        #print(sum_cars)
        #print(sum_distance)
        #print(max_tools_used)

        # sum up tool costs
        sum_tool_costs = 0
        for (tool_id, max_amount) in max_tools_used.items():
            sum_tool_costs += max_amount * problem_instance['tools'][tool_id].cost

        self.cars_on_day = cars_on_day
        #print(cars_on_day)

        return max_cars     * problem_instance['vehicle_cost']     + \
               sum_cars     * problem_instance['vehicle_day_cost'] + \
               sum_distance * problem_instance['distance_cost']    + \
               sum_tool_costs

    def mutate(self):
        """Perform a random mutation on the current candidate.

        :return:
        """

        r = random.random()
        if r < PARAMETERS['mutation_possibility']:
            #print("mutate")
            #print(self.day_list)
            # TODO mutate only one request?

            while True: # find a request to mutate where first start day != last start day
                request_id = random.randrange(1, len(problem_instance['requests']) + 1)
                first_day = problem_instance['requests'][request_id].first_day
                last_day  = problem_instance['requests'][request_id].last_day
                num_days  = problem_instance['requests'][request_id].num_days

                if first_day != last_day:
                    break

            #print("request to mutate:", request_id)

            while True: # find a new start day
                new_start_day = random.randrange(first_day, last_day + 1)
                old_start_day = self.find_start_day_of_request(request_id, first_day, last_day)

                #print("new start day vs old start day:", new_start_day, old_start_day)

                if new_start_day != old_start_day: # change the startday and endday of the request
                    self.day_list[new_start_day]           [request_id] = 'deliver'
                    self.day_list[new_start_day + num_days][request_id] = 'fetch'
                    self.day_list[old_start_day]           .pop(request_id, None)
                    self.day_list[old_start_day + num_days].pop(request_id, None)
                    break

            #print(self.day_list)

    def find_start_day_of_request(self, request_id, first_day, last_day):
        """Find the chosen start day of the request for this candidate.

        :param request_id: The ID of the request whose chosen start day to find
        :param first_day: The first possible start day of the request as per problem instance
        :param last_day: The last possible start day of the request as per problem instance
        :return: The index of the day on which the start was fixed or -1
        """
        for day_idx in range(first_day, last_day + 1):
            if request_id in self.day_list:
                return day_idx

        return -1

    def get_extended_daylist(self):
        """Create the extended day-list of the candidate.

        Creates a list of length NUMBER_DAYS, where every element is a dictionary {REQUEST_ID: REQUEST_STATE}.
        This extends the normal day-list by adding {REQUEST_ID: "running"} entries between start and end days.
        :return: The extended day-list
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

    def repair(self):
        """Repair the Candidate's request schedule.

        Checks if there are any violations of the maximum AVAILABLE number of tools due to peaks in requests.
        If that is the case, it tries to move the requests around, such that there are no longer any violations
        of the maximum available number.

        If this is possible or there haven't been any violations in the first place, the valid field of the
        Candidate is set to True.
        Otherwise, the valid field of the Candidate is set to False.
        :return: nothing
        """
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
                #print("max_depth:", max_depth)
                repair_result = self.rec_repair(start_day_dict, extended_day_list, 0, max_depth)

                if repair_result is None:
                    if max_depth < PARAMETERS['max_depth']:
                        max_depth += PARAMETERS['max_depth_increase']
                        continue
                    else:
                        #print("WE ARE SORRY BUT YOUR PROBLEM CANNOT GET FIXED.")
                        self.valid = False
                        return
                else:
                    #print("WE FIXED YOUR PROBLEM FOR YOU MATE")
                    self.valid = True
                    # to create a "normal" day-list from the extended day-list,
                    # we only need to delete the "running" entries from the latter

                    new_day_list = []
                    for requests_per_day in repair_result:
                        new_day_list.append({req_id: state for req_id, state in requests_per_day.items() if state != "running"})

                    # make the result stick
                    self.day_list = new_day_list
                    break

    def rec_repair(self, move_dict, current_extended_daylist, depth, max_depth):
        """The recursive part of the repair.

        This function keeps track of the recursion depth used and will return None, if the maximum depth has been
        exceeded.
        :param move_dict: The dictionary containing the not-yet-tried moves per request
        :param current_extended_daylist: The extended day-list on which to base the movements
        :param depth: The current depth of the iteration
        :param max_depth: The maximum depth of the iteration
        :return: The extended day-list representing a fix, or None if no such day-list could be found
        """

        chosen_request = None
        max_impact = 0
        next_move_dict = move_dict.copy()
        tool_id = None
        tool_availability = None

        for req_id in move_dict:
            # if the list of possible start days is not empty...
            if move_dict[req_id]:
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

            # if this move fixed the peak, let's return the extended day list that fixed the problem
            if new_peak <= tool_availability:
                return tmp_ext_daylist

            # if we haven't repaired the problem at this stage, let's try to go deeper
            if depth < max_depth:
                deeper_result = self.rec_repair(next_move_dict, tmp_ext_daylist, depth + 1, max_depth)
                if deeper_result is not None:
                    return deeper_result

        # at this point, we have exhausted all possibilities and still not found a solution
        return None


def translate(value, left_min, left_max, right_min, right_max):
    """

    :param value:
    :param left_min:
    :param left_max:
    :param right_min:
    :param right_max:
    :return:
    """
    # Figure out how 'wide' each range is
    left_span = left_max - left_min
    right_span = right_max - right_min

    # if left_min == left_max, we can pick an arbitrary value for
    # what we return
    left_span = float(left_span)
    if left_span == 0:
        return right_max

    # Convert the left range into a 0-1 range (float)
    value_scaled = float(value - left_min) / left_span

    # Convert the 0-1 range into a value in the right range.
    return right_min + (value_scaled * right_span)


def is_route_valid(route, tool_id):
    """Check if the route is valid.

    Check the supplied route against several limits, such as maximum driving distance and vehicle capacity.
    It is assumed that the first and last StopOver in the route are the depot.
    The first and last StopOver's num_tools fields may be altered in order to reflect if the route
    requires some tools to be picked up from the depot at the beginning or some tools are dropped off
    at the depot at the end of the trip.
    :param route: The route (i.e. list of StopOvers) to check
    :return: True if the route is valid, False otherwise
    """
    sum_distance = 0
    loaded = 0
    max_load = 0
    tool_size = problem_instance["tools"][tool_id].size

    for (idx, stopover) in enumerate(route):
        customer_id   = stopover.customer_id
        request_id    = stopover.request_id
        change_amount = stopover.num_tools

        if idx == 0:
            continue

        last_customer_id = route[idx-1].customer_id
        sum_distance += problem_instance['distance'][last_customer_id][customer_id]

        # change amount is subtracted because we use negative numbers to
        # indicate FETCH requests (which is where tools get loaded)
        # and positive numbers to indicate DELIVER requests (which is where
        # we lower the amount of loaded tools)
        loaded -= change_amount

        if (loaded * tool_size) > problem_instance["capacity"]:
            #print("CAPACITY.")
            return False
        elif sum_distance > problem_instance["max_trip_distance"]:
            #print("SUM DISTANCE.", sum_distance, problem_instance["max_trip_distance"])
            return False

        max_load = max(max_load, loaded)

    if loaded < 0:
        depot_load = loaded

        # if we need to fetch something at the depot already,
        # we have to take into account that we are
        if ((max_load + abs(depot_load)) * tool_size) > problem_instance["capacity"]:
            #print("CAPACITY THROUGH DEPOT LOADING FUCKED")
            return False

        route[0].num_tools = depot_load

    elif loaded > 0:
        route[-1].num_tools = loaded

    return True


def tool_usages_from_extended_daylist(ext_day_list):
    """Calculate the tool usages from the given extended day list.

    The result will be a dictionary with Tool IDs as keys and a list as value.
    The value list has one entry per day of the problem and the entry's value equals to the amount of tools
    required at this day as per optimistic maximum
    (i.e. tools still at a customer's place + tools requested - tools returned)
    :param ext_day_list: The extended day-list to calculate the daily uses from
    :return: The usage dictionary in form of {TOOL_ID: [LIST_OF_USES_PER_DAY]}
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
        candidate.repair()
        if not candidate.valid:  # we need to create an additional candidate
            continue

        fit_ = candidate.fitness_heuristic()
        if fit_ == -1:
            continue # candidate is not valid

        #print("Fitness is: ", fit_)
        candidate.fit = fit_
        # print(candidate.get_extended_daylist())
        population.append(candidate)
        i += 1
        print("Found the {}. candidate!".format(i))
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
    new_candidate.repair()  # repair the candidate
    fit_ = new_candidate.fitness_heuristic()
    new_candidate.fit = fit_
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
            or ((val_0, val_1) in blocked_values) or ((val_1, val_0) in blocked_values):
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


def make_fitness_range(values, highest_fitness, lowest_fitness):
    """Create a list containing triples of the form (LOWER, UPPER, ELEMENT)

    :param values:
    :return:
    """
    great_range = []
    upper = 0

    for elem in values:
        # we want that elems with a smaller fitness have a higher chance to be chosen for combination!
        inverted_fitness = lowest_fitness + (highest_fitness - elem.fit)
        lower = upper
        upper = lower + inverted_fitness
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

    for i in range(0, PARAMETERS['number_of_generations']):
        debug_print('\nIteration: =======' + str(i) + '=======')

        population_sorted = sorted(population, key=lambda p: p.fit)
        highest_fitness = population_sorted[-1:][0].fit
        lowest_fitness  = population_sorted[0].fit

        fitness_range = make_fitness_range(population, highest_fitness, lowest_fitness)
        #debug_print("fitness range:", fitness_range)
        sum_fitness_values = fitness_range[-1][1] + 1 # the upper bound of the last entry.
        debug_print("sum fitness values:", sum_fitness_values)

        # create new population through crossover
        new_population = []
        num_new_candidates = 0
        blocked_values = []
        while num_new_candidates < PARAMETERS['population_size'] - PARAMETERS['survivor_size']:

            # select crossover candidates (candidates with higher fitness have a higher chance to get reproduced)
            (one, two) = find_mating_pair(fitness_range, sum_fitness_values, blocked_values)
            new_candidate = combine(one, two)

            if not new_candidate.valid:  # we need to generate an additional candidate
                continue

            # mutate (happens randomly)
            new_candidate.mutate()

            # TODO can this still happen often enough?
            if new_candidate in population:  # we need to generate an additional candidate
                debug_print('COMBINATION YIELDED CANDIDATE ALREADY IN POPULATION, IGNORING THIS NEW CANDIDATE')
                continue

            # debug_print('1: ', str(one))
            # debug_print('2: ', str(two))
            # debug_print('Combined: ', new_candidate)
            new_population.append(new_candidate)
            blocked_values.append((one, two))
            num_new_candidates += 1

        # select survivors (the best ones survive => the ones with the lowest fitness)
        population = sorted(population, key=lambda p: p.fit)
        population = population[:PARAMETERS['survivor_size']]

        new_population.extend(population)
        population = new_population

        # debug_print('Population after mutation: ' + str([str(p) for p in population]))
        population = sorted(population, key=lambda p: p.fit)
        debug_print('Best  fitness: ', new_population[-1].fit)
        debug_print('Worst fitness: ', new_population[0] .fit)

    end = datetime.datetime.now()
    print('Done: ' + end.isoformat())
    print('Took me: ' + str((end - start).seconds) + 's')
    return population
