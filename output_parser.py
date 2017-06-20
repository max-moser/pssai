import sys


def create_output_file(problem_instance, best_solution, filename):
    output_str = ""

    output_str += 'DATASET = {}\n'.format(problem_instance['dataset'])
    output_str += 'NAME = {}\n\n' .format(problem_instance['name'])

    for (day_idx, cars_day) in enumerate(best_solution.cars_on_day):
        output_str += 'DAY = {}\n'.format(day_idx)
        output_str += 'NUMBER_OF_VEHICLES = {}\n'.format(len(cars_day))
        for (car_idx, car) in enumerate(cars_day):
            output_str += '{}\tR\t'.format(car_idx)

            for (trip_idx, trip) in enumerate(car):
                for (stopover_idx, stopover) in enumerate(trip.stopovers):
                    if stopover_idx == 0 and trip_idx != 0:  # ignore the depot if this is not the first trip
                        continue
                    if stopover.num_tools < 0:
                        output_str += "-"
                    output_str += '{}\t'.format(stopover.request_id)

            output_str += "\n"
        output_str += "\n"

    print(output_str)

    f = open(filename, 'w')
    f.write(output_str)
    f.close()
