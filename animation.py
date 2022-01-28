import salabim as sim

'''
This is a demonstration of several ways to show queues dynamically and the corresponding statistics
The model simply generates components that enter a queue and leave after a certain time.

Note that the actual model code (in the process description of X does not contain any reference
to the animation!
'''


class X(sim.Component):
    def setup(self, i):
        self.i = i

    def animation_objects(self, id):
        '''
        the way the component is determined by the id, specified in AnimateQueue
        'text' means just the name
        any other value represents the colour
        '''
        if id == 'text':
            ao0 = sim.AnimateText(text=self.name(), textcolor='fg', text_anchor='nw')
            return 0, 16, ao0
        else:
            ao0 = sim.AnimateRectangle((-20, 0, 20, 20),
                text=self.name(), fillcolor=id, textcolor='white', arg=self)
            return 45, 0, ao0

    def process(self):
        while True:
            yield self.hold(sim.Uniform(0, 20)())
            self.enter(q)
            yield self.hold(sim.Uniform(0, 20)())
            self.leave()


env = sim.Environment(trace=False)
env.background_color('20%gray')

q = sim.Queue('queue')

qa0 = sim.AnimateQueue(q, x=100, y=50, title='queue, normal', direction='e', id='blue')
qa1 = sim.AnimateQueue(q, x=100, y=250, title='queue, maximum 6 components', direction='e', max_length=6, id='red')
qa2 = sim.AnimateQueue(q, x=100, y=150, title='queue, reversed', direction='e', reverse=True, id='green')
qa3 = sim.AnimateQueue(q, x=100, y=440, title='queue, text only', direction='s', id='text')

sim.AnimateMonitor(q.length, x=10, y=450, width=480, height=100, horizontal_scale=5, vertical_scale=5)

sim.AnimateMonitor(q.length_of_stay, x=10, y=570, width=480, height=100, horizontal_scale=5, vertical_scale=5)

sim.AnimateText(text=lambda: q.length.print_histogram(as_str=True), x=500, y=700,
    text_anchor='nw', font='narrow', fontsize=10)

sim.AnimateText(text=lambda: q.print_info(as_str=True), x=500, y=340,
    text_anchor='nw', font='narrow', fontsize=10)

[X(i=i) for i in range(15)]
env.animate(True)
env.modelname('Demo queue animation')
env.run(till=10)
