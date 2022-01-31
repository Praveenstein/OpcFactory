import salabim as sim
import time


class RealTimeEnvironment(sim.Environment):

    def animation_pre_tick(self, t):

        cycle_time = my_machine_1.cycle_time(t)
        operating_time = my_machine_1.operating_time(t)
        if my_machine_1.machine_status(t) == 1:
            cycle_time = t - my_machine_1.cycle_time_start(t)
            my_machine_1.cycle_time.tally(cycle_time)
            operating_time += cycle_time
        message = "|TIMESTAMP|" + str(round(t, 2)) + "|PART_COUNT|" + str(my_machine_1.parts(t)) + "|CYCLE_TIME|" + \
                  str(round(cycle_time, 2)) + "|OPERATING_TIME|" + str(round(operating_time, 2)) + "|"
        print(message)
        time.sleep(1)


class Machine(sim.Component):
    def __init__(self, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)
        self.parts = sim.Monitor(name='parts', level=True, initial_tally=0)
        self.cycle_time_start = sim.Monitor(name='cycle_time_start', level=True, type='float', initial_tally=0.0)
        self.cycle_time = sim.Monitor(name='cycle_time', level=True, type='float', initial_tally=0.0)
        self.operating_time = sim.Monitor(name='operating_time', level=True, type='float', initial_tally=0.0)
        self.machine_status = sim.Monitor(name='machine_status', level=True, type='uint8', initial_tally=0)

    def process(self):
        while True:
            self.machine_status.tally(1)
            self.cycle_time_start.tally(env.now())
            self.cycle_time.tally(0)

            # The hold below is to represent the actual processing time of a part
            yield self.hold(10)

            # After processing, the machine status is set to idel
            self.machine_status.tally(0)

            # Increasing the part count by 1
            self.parts.tally(self.parts() + 1)

            # Increasing the operating time by an amount equal to the last cycle time
            self.operating_time.tally(self.operating_time() + self.cycle_time())
            # The hold below is to represent the time gap for another part to arrive
            yield self.hold(3)


env = RealTimeEnvironment()

env.animate(True)
env.root.withdraw()
#env.animation_parameters(animate=True, width=1, height=1)

my_machine_1 = Machine()
# my_machine_2 = Machine()

env.run(till=40)
