# Car.py
import salabim as sim


class RealTimeEnvironment(sim.Environment):

    def __init__(self, counter, *args, **kwargs):
        sim.Environment.__init__(self, *args, **kwargs)
        self.counter = counter

    def animation_pre_tick(self, current_time):
        self.counter += 1
        print(self.counter)
        print("===============================================")
        print("Current Animation Time", current_time)
        print("===============================================")


class Car(sim.Component):

    def process(self):
        while True:

            print("********************************************")
            print("Current Environment Time: ", ENVIRONMENT.now())
            print("********************************************")
            yield self.hold(1)


ENVIRONMENT = RealTimeEnvironment(counter=0)
ENVIRONMENT.animate(True)
ENVIRONMENT.animation_parameters(fps=1, synced=True)

# This makes the animation window invisible
ENVIRONMENT.root.withdraw()

Car()

ENVIRONMENT.run(till=30)

