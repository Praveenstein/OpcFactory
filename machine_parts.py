# Importing external packages
from prettytable import PrettyTable
import salabim as sim
from opcua import ua, Server


class RealTimeEnvironment(sim.Environment):

    def animation_pre_tick(self, current_time):

        print("Current Animation Time: ", current_time)


class OpcServer(sim.Component):
    """
    This class is used to represent a centralized data server, through which other 3rd party applications
    can get access to the data. In future this could be implemented as OPC/ MtConnect server.
    """
    def __init__(self, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)
        server = Server()
        server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")

        # setup our own namespace, not really necessary but should as spec
        uri = "factory_namespace"
        server_namespace = server.register_namespace(uri)

        self._opc_server = server

        # get Objects node, this is where we should put our nodes
        objects = server.get_objects_node()
        self._opc_machine_objects = []
        for index, machine in enumerate(UNITS_OF_FACTORY):

            # populating our address space
            machine_name = "my_machine_" + str(index)
            current_machine = objects.add_object(server_namespace, machine_name)
            current_machine.add_variable(server_namespace, "machine_id", index)
            current_part_count = current_machine.add_variable(server_namespace, "part_count", 0)
            current_cycle_time = current_machine.add_variable(server_namespace, "cycle_time", 0.0)
            current_operating_time = current_machine.add_variable(server_namespace, "operating_time", 0.0)

            current_part_count.set_writable()  # Set MyVariable to be writable by clients
            current_cycle_time.set_writable()  # Set MyVariable to be writable by clients
            current_operating_time.set_writable()  # Set MyVariable to be writable by clients
            self._opc_machine_objects.append(current_machine)

        server.start()

    def process(self):
        while True:
            # Creating a pretty table.
            table = PrettyTable(["Machine Id", "Part Count", "Cycle Time", "Operating Time"])

            for index, machine in enumerate(UNITS_OF_FACTORY):

                cycle_time = machine.cycle_time
                operating_time = machine.operating_time
                if machine.machine_status == 1:
                    # If and only if the machine is currently executing a cycle the following changes will be made.

                    # Every second the cycle time is updated (just like an actual controller)
                    cycle_time = ENVIRONMENT.now() - machine.cycle_time_start
                    machine.cycle_time = cycle_time
                    operating_time += cycle_time
                machine_data = [machine.machine_id, machine.parts, round(cycle_time, 2),
                                round(operating_time, 2)]
                table.add_row(machine_data)
                opc_machine = self._opc_machine_objects[index]
                machine_parameters = opc_machine.get_children()
                for inner_index in range(1, len(machine_parameters)):
                    machine_parameters[inner_index].set_value(machine_data[inner_index])

            print("==========================================================================================")
            print()
            print(str(round(ENVIRONMENT.now(), 2)))
            print(table)
            print()
            print("==========================================================================================")
            yield self.hold(1)
            if ENVIRONMENT.now() == 299:
                self._opc_server.stop()


class Machine(sim.Component):

    def __init__(self, machine_name, machine_id, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)

        # Attributes from the given arguments.
        self.machine_name = machine_name
        self.machine_id = machine_id

        # Attributes created using (Other) sim objects.
        self.machine_queue = sim.Queue(f"queue_{machine_id}")

        # Important parameters of a machine for Performance Metric calculation
        self.parts = 0
        self.cycle_time_start = 0.0
        self.cycle_time = 0.0
        self.operating_time = 0.0
        self.machine_status = 0
        self.current_part = None

    def process(self):
        while True:

            while len(self.machine_queue) == 0:
                # If the machine's queue is empty, it will be made passive.
                yield self.passivate()

            # Taking the first part from the queue (as soon as it is activated by a part).
            # And making it as the machine's current part in progress.
            self.current_part = self.machine_queue.pop()

            # Setting the machine status as 1, meaning it is currently executing a cycle.
            self.machine_status = 1

            # Setting the current cycle's start time as the current time in the simulation environment.
            self.cycle_time_start = ENVIRONMENT.now()
            # Setting the live-real-time cycle as 0 (as it does in an actual machine controller {like fanuc}).
            self.cycle_time = 0.0

            # The machine is held for a time equivalent to the current part's processing time.
            # self.current_part.remaining_sequence[0] gives the first task left in the remaining set of tasks.
            yield self.hold(self.current_part.current_processing_time)

            # After processing, setting the machine status as 0, meaning it is currently idle.
            self.machine_status = 0
            # Increasing the part count by 1.
            self.parts += 1

            # There is a loss of one second (Maybe some problem with the Server Class) hence
            # We're calculating cycle time again by using the below formula, to get exact values
            self.cycle_time = ENVIRONMENT.now() - self.cycle_time_start
            # Increasing the operating time by an amount equal to the last cycle time.
            self.operating_time += self.cycle_time

            # Activating the current part.
            self.current_part.activate()

            # Setting the current part for the machine to None
            self.current_part = None

            # The hold below is to represent the time delay to remove the current part and place the next one.
            yield self.hold(3)


class Part(sim.Component):
    """
    This class is used for representing a Part that needs to be manufactured.
    """
    def __init__(self, name, family_number, number, machining_sequence, *args, **kwargs):
        """
        :param name: Name of the part
        :type name: str
        :param family_number: Family number of the part, many parts of one family will be manufactured
        :type family_number: int
        :param number: part number, which also includes the family number
        :type number: int
        :param machining_sequence: An array describing the sequence of task, with the corresponding machine and
        machining time on that machine. For instance

                                    [[0, 300], [2, 400], [1, 500]]

        This denotes, the first task has to be done on Machine 0, with a processing time of 300s,
        the second task has to be done on Machine 2, with a processing time of 400s,
        the third task has to be done on Machine 1, with a processing time of 500s.

        :type machining_sequence: list
        :param args: Other positional arguments required for the sim.Component class
        :type args: object
        :param kwargs: Other keyword arguments required for the sim.Component class
        :type kwargs: object
        """
        sim.Component.__init__(self, *args, **kwargs)
        self.part_name = name
        self.part_family_number = family_number
        self.part_number = number
        self.machining_sequence = machining_sequence
        self.current_sequence = None
        self.current_machine = None
        self.current_processing_time = 0

    def process(self):
        # The process keeps looping until there is no more task left in the sequence of operations
        for sequence in self.machining_sequence:
            self.current_sequence = sequence
            self.current_machine = UNITS_OF_FACTORY[sequence[0]]
            self.current_processing_time = sequence[1]
            self.enter(self.current_machine.machine_queue)
            if self.current_machine.ispassive():
                self.current_machine.activate()
            yield self.passivate()


class PartGenerator(sim.Component):
    """
    This class is used for creating new parts according to schedule.
    """
    def __init__(self, part_details, *args, **kwargs):
        """

        :param part_details: It is an array consisting of part name, part family number, quantity to be
        produced, it's sequence of task, which is an array describing the sequence of task, with the
        corresponding machine and machining time on that machine. For instance

                                    [[0, 300], [2, 400], [1, 500]]

        This denotes, the first task has to be done on Machine 0, with a processing time of 300s,
        the second task has to be done on Machine 2, with a processing time of 400s,
        the third task has to be done on Machine 1, with a processing time of 500s.

                            [Part Name, Part Family Number, Quantity, Production Plan]

        :type part_details: list
        """
        sim.Component.__init__(self, *args, **kwargs)
        self.part_details = part_details

    def process(self):
        print(ENVIRONMENT.main().scheduled_time())
        for part_family in self.part_details:
            for part in range(part_family[2]):
                Part(part_family[0], part_family[1], int(str(part_family[1]) + str(part)), part_family[-1])
            #yield self.hold(1)


def create_machining_units(number_of_units):
    """
    Function used to create a given number of  machines.

    :param number_of_units: The number of machines to be created
    :type number_of_units: int
    :return: A list containing a given number of machines of type `Machine`
    :rtype: list
    """
    machining_units = [Machine(machine_name="VMC", machine_id=machine) for machine in range(number_of_units)]
    return machining_units


# The current production plan consist of making 4 parts and the corresponding details are given below
# Part Name, Part Family Number, Quantity, Machining Sequence [Machine Id, Machining Time]
PRODUCTION_PLAN = [["Part 0", 100000, 10, [[0, 2], [1, 4], [2, 3], [3, 5]]],
                   ["Part 1", 200000, 11, [[1, 3], [0, 1], [2, 4], [3, 2]]],
                   ["Part 2", 300000, 12, [[2, 4], [1, 5], [0, 3], [3, 2]]],
                   ["Part 3", 400000, 13, [[3, 5], [2, 1], [0, 4], [1, 4]]]]

ENVIRONMENT = RealTimeEnvironment()
ENVIRONMENT.animate(True)

# In order to make the simulation real time, synced must be set to true (which makes sure that the animation time
# is synced with the real time, and fps should be set to 1, so that the animation_pre_tick function of the
# RealTimeEnvironment class is called at most once per second (again makes sure that the simulation is synced with
# real time.
ENVIRONMENT.animation_parameters(fps=1, synced=True)

# This makes the animation window invisible
ENVIRONMENT.root.withdraw()

UNITS_OF_FACTORY = create_machining_units(4)
PartGenerator(PRODUCTION_PLAN)
OpcServer()

ENVIRONMENT.run(till=300)
