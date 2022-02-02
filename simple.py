# Car.py
import salabim as sim
import time


class Car(sim.Component):
    def process(self):
        while True:
            time.sleep(1)
            yield self.hold(1)


env = sim.Environment(trace=True)
Car()
try:
    env.run(till=5)
except KeyboardInterrupt:
    print("NOT OK")
