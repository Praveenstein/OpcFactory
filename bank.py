# Bank, 1 clerk.py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        print(ENV.main().scheduled_time())
        while True:
            Customer()
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        self.enter(WAITING_LINE)
        if clerk.ispassive():
            clerk.activate()
        yield self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(WAITING_LINE) == 0:
                yield self.passivate()
            self.customer = WAITING_LINE.pop()
            yield self.hold(30)
            self.customer.activate()


ENV = sim.Environment(trace=True, time_unit='seconds')

CustomerGenerator()
clerk = Clerk()
WAITING_LINE = sim.Queue("waitingline")

ENV.run(till=10)
print()
WAITING_LINE.print_statistics()
