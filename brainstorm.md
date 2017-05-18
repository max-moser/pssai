# Ideas
This file is intended for doing some brain-storming about possible solutions/implementations for solving the verolog challenge

## MiniZinc
http://www.minizinc.org/
Complete approach, constraint programming...
perhaps solution will look something like this:
INPUT FILE -> translation script -> MiniZinc input file -> MiniZinc solver -> MiniZinc output file -> translation script -> OUTPUT FILE

## Simulated Annealing
Use of simulated annealing (=metaheuristic) for the scheduling part of the problem + not completely dumb heuristic for determining an assignment of vehicles with preferably low cost
