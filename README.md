# PSSAI, Summer Term 2017
VeRoLog challenge for Problem Solving and Search in Artificial Intelligence, Summer 2017

## Information about the lecture:
http://www.dbai.tuwien.ac.at/staff/musliu/ProblemSolvingAI/

## Information about the challenge:
https://verolog.ortec.com/

## Requirements

Python 3

## Usage

```
python3 input_parser.py TEST_INSTANCE.TXT
```

The program will generate the solution file in the same directory as the input
file, with a naming like "TEST_INSTANCE.sol.genetic.TXT" after running through.

The program requires the three files "input_parser.py", "genetic_solver.py" and
"output_parser.py" to be in the same directory, since all of them contain parts
of the entire script.

To change the parameters of the genetic algorithm (e.g. mutation likelihood),
you have to edit the dictionary at the top of the file "genetic_solver.py".

## Contributors:
Maximilian Moser, 1326252
Wolfgang Weintritt, 1327191
