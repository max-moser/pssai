This document contains a listing of generated output files and short summaries
  (the parameters used for creating them, the cost of the best generated solution
  and a small remark) regarding each output file



--------------------------------------------------------------------------------
Usage
-----

Usage:
	python3 input_parser.py TEST_INSTANCE.TXT

The program will generate the solution file in the same directory as the input
file, with a naming like "TEST_INSTANCE.sol.genetic.TXT" after running through.

The program requires the three files "input_parser.py", "genetic_solver.py" and
"output_parser.py" to be in the same directory, since all of them contain parts
of the entire script.


--------------------------------------------------------------------------------
General Findings
----------------

We have let our genetic algorithm run over all problem instances at least once
before we even started to document the results
Our findings were in general that we were better at keeping the amount of used
tools low, but were usually worse at anything vehicle-related (especially distances
and vehicle days)
We think that this is because we did not use bin-packing or anything of the sorts
to load the cars, but instead used a Nearest Neighbour approach for finding a valid
route and then simply loaded the car according to the result (in the case that we
*must* re-use tools with the same car, our approach ("Straight Fetch & Deliver")
cares even less about optimizing a car's capacity utilization).


An example for this is the following comparison:

Sample Solution for Problem Instance #2:
  Max number of vehicles: 17
  	Number of vehicle days: 79
  	Distance: 1611332
  	Cost: 9495959
  	Tool count: [132, 55, 97, 68, 71]

vs our generated solution (for the same problem of course):
  Max number of vehicles: 16
  	Number of vehicle days: 123
  	Distance: 2144386
  	Cost: 7372952
  	Tool count: [102, 53, 71, 45, 47]

As can be seen in the above comparison, we have better tool optimization,
but much worse optimization regarding cars (vehicle days are about 50 more)
as well as 1.3x distance.
But since in instance #2, the tools are more expensive than cars and distance,
our generated solution is better than the sample solution.



--------------------------------------------------------------------------------
Input Files
-----------

ORTEC_Test_03.txt
ORTEC_Test_04.txt
  The problem instances #3 and #4 respectively
  We based our problem benchmark primarily upon Test #3 in order to be able
    to compare the results amongst themselves



--------------------------------------------------------------------------------
Output Files
------------

ORTEC_Test_03.sol.genetic_1031.txt:
  PARAMETERS = {'population_size': 100, 'survivor_size': 5, 'mutation_possibility': 0.0015,
                'number_of_generations': 2, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    36911832
  Remarks:
    runtime around 666s (~11m)


ORTEC_Test_03.sol.genetic_1044.txt:
	PARAMETERS = {'population_size': 100, 'survivor_size': 5, 'mutation_possibility': 0.0015,
	              'number_of_generations': 100, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    33402374
  Remarks:
    noticably better than with low number of generations


ORTEC_Test_03.sol.genetic_1057.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 5, 'mutation_possibility': 0.0030,
              'number_of_generations': 100, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    33559672
  Remarks:
    slightly worse than with less mutations


ORTEC_Test_03.sol.genetic_1110.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 10, 'mutation_possibility': 0.0020,
                'number_of_generations': 100, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    33807039
  Remarks:
    again slightly worse


ORTEC_Test_03.sol.genetic_1122.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0020,
                'number_of_generations': 100, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    34128609
  Remarks:
    even worse


ORTEC_Test_03.sol.genetic_1135.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0020,
                'number_of_generations': 100, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    33738712
  Remarks:
    re-run with the same parameters as before, this time better again


ORTEC_Test_04.sol.genetic_1139.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0020,
                'number_of_generations': 100, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    41256295
  Remarks:
    trying a different problem instance; runs way faster


ORTEC_Test_03.sol.genetic_1548.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0020,
                'number_of_generations': 2000, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    29541509
  Remarks:
    trying a vastly increased number of generations (though still far below the usual ~30k)
    yields a noticably better result
    runtime around 14707s (~245m, ~4h)


ORTEC_Test_03.sol.genetic_1730.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0100,
                'number_of_generations': 200, 'max_depth_start': 2, 'max_depth_increase': 3, 'max_depth': 10}
  Cost:
    30233173
  Remarks:
    increased mutation and generation size with respect to the initial configuration
    seems promising


ORTEC_Test_03.sol.genetic_1755.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0300,
                'number_of_generations': 200, 'max_depth_start': 6, 'max_depth_increase': 3, 'max_depth': 15}
  Cost:
    30922967
  Remarks:
    Much higher mutation rate seems to have overdone it a little bit
      although that could also still be the result of a poor initial population
    Setting the max_depth_start to something higher could have resulted in a few less search recursions
      and thus a little less runtime, but should otherwise not have much of an impact


ORTEC_Test_03.sol.genetic_1819.txt
  PARAMETERS = {'population_size': 100, 'survivor_size': 7, 'mutation_possibility': 0.0200,
                'number_of_generations': 200, 'max_depth_start': 6, 'max_depth_increase': 3, 'max_depth': 15}
  Cost:
    29269434
  Remarks:
    20% mutation seems to have hit a sweet spot, as it is very noticably better than what we have
      had so far with 200 generations (though this could also be luck with the initial population of course)
