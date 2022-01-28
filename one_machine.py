import salabim as sim
import time


class RealTimeEnvironment(sim.Environment):

    def animation_pre_tick(self, t):
        cycle_time = env.now() - my_machine_1.cycle_time_start(t)
        print(str(t) + "_", str(my_machine_1.parts(t)) + "_" + str())
        time.sleep(1)


class Machine(sim.Component):
    def __init__(self, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)
        self.parts = sim.Monitor(name='parts', level=True, initial_tally=0)
        self.cycle_time_start = sim.Monitor(name='cycle_time_start', level=True, type='float', initial_tally=0.0)
        self.cycle_time_end = sim.Monitor(name='cycle_time_end', level=True, type='float', initial_tally=0.0)

    def process(self):
        while True:
            self.cycle_time_start.tally(env.now())
            yield self.hold(5)
            self.parts.tally(self.parts() + 1)


env = RealTimeEnvironment()

env.animation_parameters(animate=True, width=1, height=1)

my_machine_1 = Machine()
#my_machine_2 = Machine()

env.run(till=10)
