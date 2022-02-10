#!/usr/bin/python
import sys
import clingo
import theory
import time
from clingo import Function

NUM_OF_TIME_WINDOWS = 2
MAX_TIMEOUT = 4

class Application:
    def __init__(self, name):
        self.program_name = name
        self.version = "1.0"
        self.__theory = theory.Theory("clingodl", "clingo-dl")

    def __on_model(self, model):
        self.__theory.on_model(model)
        #print( model.optimality_proven)

    def register_options(self, options):
        self.__theory.register_options(options)

    def validate_options(self):
        self.__theory.validate_options()
        return True

    def __on_statistics(self, step, accu):
        self.__theory.on_statistics(step, accu)
        pass
    
    # get the timeout per each Window
    def get_timeout(self):
        return MAX_TIMEOUT/NUM_OF_TIME_WINDOWS
    # ************************************************

    # get the assignment of the operations in a string format to be sent as facts for the next Time Window
    def get_total_facts(self, assignment, i):
        total_facts = ''
        to_join = []
        for name, value in assignment:
            if str(name) != "makespan":
                facts_format = "start({}, {}, {}). ".format(name, value, i)
                to_join.append(facts_format)
            else:
                makespan = int(value)
        total_facts = ''.join(to_join)
        return total_facts, makespan
    # ****************************************************************************************************

    # get the part that should be grounded and solved
    def step_to_ground(self, prg, step, total_facts):
        parts = []
        if step > 0:
            parts.append(("step", [step]))
            if step > 1:
                parts.append(("solutionTimeWindow", []))
                prg.add("solutionTimeWindow", [], total_facts)
        else:
            parts.append(("base", []))
        return parts
    # ***********************************************

    def main(self, prg, files):
        self.__theory.configure("propagate", "full,1")
        self.__theory.register(prg)
        if not files:
            files.append("-")
        for f in files:
            prg.load(f)
        timeout_for_window = self.get_timeout()
        i, ret = 0, None
        total_facts = ''
        interrupted_calls = 0
        non_interrupted_calls = 0
        makespan_time_window = []
        while i <= NUM_OF_TIME_WINDOWS:
            optimum = True
            prg.configuration.solve.models = 1
            prg.configuration.solve.opt_mode = "optN"
            parts = self.step_to_ground(prg, i, total_facts)
            prg.cleanup()
            prg.ground(parts)
            self.__theory.prepare(prg)
            makespan = 0
            with prg.solve(on_model=self.__on_model, on_statistics=self.__on_statistics, async_=True, yield_=True) as handle:
                wait = handle.wait(1)
                print("Wait" + str(wait))
                if not wait:
                    interrupted_calls += 1
                    optimum = False
                for model in handle:
                    if i != 0:
                        a = self.__theory.assignment(model.thread_id)
                        total_facts, makespan = self.get_total_facts(a, i)
                        break
                    
                if optimum:
                    non_interrupted_calls += 1
                    # sys.stdout.write("Optimum Found of the current window\n")
            if i != 0:
                makespan_time_window.append(makespan)
            i = i + 1      # Go to the next Time Window
            print("Makespan {} : {}".format(makespan, total_facts))
            print("**************************************************************")
        for x in range(NUM_OF_TIME_WINDOWS):
            print("Completion Time for Window {} : {} ".format(x+1, makespan_time_window[x]))
        print("Number of Interrupted Calls : {} ".format(interrupted_calls))
        print("Number of UnInterrupted Calls : {} ".format(non_interrupted_calls-1))

sys.exit(int(clingo.clingo_main(Application("test"), sys.argv[1:])))
