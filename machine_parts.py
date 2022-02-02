# Standard Built_In Packages
import sys

# Importing external packages
import keyboard
from prettytable import PrettyTable
import salabim as sim
from asyncua.sync import Server


class RealTimeEnvironment(sim.Environment):

    def __init__(self, animation=True, animation_fps=1,
                 animation_synced=True, animation_visibility=False, number_of_machines=4,
                 production_plan=(("Part 0", 100000, 10, [[0, 2]]), ("Part 1", 200000, 10, [[1, 4]])),
                 *args, **kwargs):
        """
        New class for simulating real time environment, i.e the simulation will happen real time rather than
        completing the whole simulation in few seconds, every second data will be updated

        :param animation: Parameter to set whether animation has be set, default is true, which is essential for
        real time simulation
        :type animation: bool
        :param animation_fps: The frames per second of the animation window, has to set to 1 for real time simulation
        :type animation_fps: int
        :param animation_synced: Parameter to set whether animation time (device's local clock) has to be synced with
        simulated environment's time/clock,default is true, which is essential for real time simulation
        :type animation_synced: bool
        :param animation_visibility: Parameter to set whether the animation window has to be visible or not,
        default is false since we're using animation only to get realtime data and not to show anything else
        :type animation_visibility: bool
        :param number_of_machines: The number of machine in the factory
        :type number_of_machines: int
        :param production_plan: The master production plan consisting of part details and production task sequence
        :type production_plan:Union[tuple, list]
        """
        # Attributes from the given arguments.
        self.number_of_machines = number_of_machines
        print(number_of_machines)
        self.production_plan = production_plan
        self.opc_server = None
        self.opc_namespace = None

        # Default factory environment attributes
        self.units_of_factory = {"machines": None, "part_generator": [], "opc_server": []}

        sim.Environment.__init__(self, *args, **kwargs)

        # Setting up animation parameters
        self.animate(animation)

        # In order to make the simulation real time, synced must be set to true (which makes sure that the animation
        # time is synced with the real time, and fps should be set to 1, so that the animation_pre_tick function of
        # the RealTimeEnvironment class is called at most once per second (again makes sure that the simulation is
        # synced with real time.
        self.animation_parameters(fps=animation_fps, synced=animation_synced)

        # This makes the animation window invisible
        if not animation_visibility:
            self.root.withdraw()

    def setup(self):
        self.units_of_factory["machines"] = create_machining_units(self.number_of_machines, self)
        self.units_of_factory["part_generator"].append(PartGenerator(self.production_plan, self))

        self.opc_server, self.opc_namespace = create_opc_server()
        self.units_of_factory["opc_server"].append(OpcServer(self, self.opc_server, self.opc_namespace))

    def animation_pre_tick(self, current_time):
        if keyboard.is_pressed("q"):
            self.opc_server.stop()
            print("System Interrupted")
            sys.exit()
        print("Current Animation Time: ", current_time)

    def run(self, *args, **kwargs):
        """
        Overwriting the existing run function so that after simulation a clean up function can be called
        :return: Nothing
        :rtype: None
        """
        super().run(*args, **kwargs)
        self._post_simulation()

    def _post_simulation(self):
        """
        This is a clean up function which stop the actual opc server after the simulation is run
        :return: Nothing
        :rtype: None
        """
        self.opc_server.stop()


class OpcServer(sim.Component):
    """
    This class is used to represent a centralized data server, through which other 3rd party applications
    can get access to the data. In future this could be implemented as OPC/ MtConnect server.
    """

    def __init__(self, environment, server, namespace, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)

        # Attributes from the given arguments.
        self.environment = environment
        self._opc_server = server
        self.namespace = namespace

        # Derived attributes
        self.simulated_machines = environment.units_of_factory["machines"]
        # List of all opc machine objects
        self._opc_machine_objects = []

        # get Objects node, this is where we should put our nodes
        root_objects = server.nodes.objects
        for index, machine in enumerate(self.simulated_machines):
            # populating our address space
            machine_name = "my_machine_" + str(index)
            current_machine = root_objects.add_object(namespace, machine_name)
            current_machine.add_variable(namespace, "machine_id", index)
            current_part_count = current_machine.add_variable(namespace, "part_count", 0)
            current_cycle_time = current_machine.add_variable(namespace, "cycle_time", 0.0)
            current_operating_time = current_machine.add_variable(namespace, "operating_time", 0.0)

            current_part_count.set_writable()  # Set MyVariable to be writable by clients
            current_cycle_time.set_writable()  # Set MyVariable to be writable by clients
            current_operating_time.set_writable()  # Set MyVariable to be writable by clients
            self._opc_machine_objects.append(current_machine)

        server.start()

    def process(self):
        while True:
            # Creating a pretty table.
            table = PrettyTable(["Machine Id", "Part Count", "Cycle Time", "Operating Time"])

            for index, machine in enumerate(self.simulated_machines):

                cycle_time = machine.cycle_time
                operating_time = machine.operating_time
                if machine.machine_status == 1:
                    # If and only if the machine is currently executing a cycle the following changes will be made.

                    # Every second the cycle time is updated (just like an actual controller)
                    cycle_time = self.environment.now() - machine.cycle_time_start
                    machine.cycle_time = cycle_time
                    operating_time += cycle_time
                machine_data = [machine.machine_id, machine.parts, float(round(cycle_time, 2)),
                                float(round(operating_time, 2))]
                table.add_row(machine_data)
                opc_machine = self._opc_machine_objects[index]
                machine_parameters = opc_machine.get_children()
                for inner_index in range(1, len(machine_parameters)):
                    machine_parameters[inner_index].write_value(machine_data[inner_index])

            print("==========================================================================================")
            print()
            print("Current Simulation Time: " + str(round(self.environment.now(), 2)))
            print(table)
            print()
            print("==========================================================================================")
            yield self.hold(1)


class Machine(sim.Component):

    def __init__(self, machine_name, machine_id, environment, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)

        # Attributes from the given arguments.
        self.environment = environment
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
            self.cycle_time_start = self.environment.now()
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
            self.cycle_time = self.environment.now() - self.cycle_time_start
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

    def __init__(self, name, family_number, number, machining_sequence, environment, *args, **kwargs):
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
        self.environment = environment
        self.current_sequence = None
        self.current_machine = None
        self.current_processing_time = 0

    def process(self):
        # The process keeps looping until there is no more task left in the sequence of operations
        for sequence in self.machining_sequence:

            # sequence gives the list consisting of next task's machine id and processing time
            self.current_sequence = sequence

            # We're taking the simulated machine from environment based on the current sequence's machine id
            self.current_machine = self.environment.units_of_factory["machines"][sequence[0]]
            self.current_processing_time = sequence[1]
            self.enter(self.current_machine.machine_queue)
            if self.current_machine.ispassive():
                self.current_machine.activate()
            yield self.passivate()


class PartGenerator(sim.Component):
    """
    This class is used for creating new parts according to schedule.
    """

    def __init__(self, part_details, environment, *args, **kwargs):
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
        self.environment = environment

    def process(self):
        print(self.environment.main().scheduled_time())
        for part_family in self.part_details:
            for part in range(part_family[2]):
                Part(part_family[0], part_family[1], int(str(part_family[1]) + str(part)),
                     part_family[-1], self.environment)
            # yield self.hold(1)


def create_machining_units(number_of_units, environment):
    """
    Function used to create a given number of  machines.

    :param number_of_units: The number of machines to be created
    :type number_of_units: int
    :param environment: The salabim simulation environment object, where these machines are deployed
    :type environment:
    :return: A list containing a given number of machines of type `Machine`
    :rtype: list
    """
    machining_units = [Machine(machine_name="VMC", machine_id=machine, environment=environment)
                       for machine in range(number_of_units)]
    return machining_units


def create_opc_server(server_url="opc.tcp://localhost:4840/freeopcua/server/", name_space="factory_namespace"):
    """
    Function used to create actual opc server to be used by simulated opc server in salabim environment

    :param server_url: This is the string which represents the opc server's endpoint
    :type server_url: str
    :param name_space: it's the name for the address space which contains all the nodes in the server
    :type name_space: str
    :return: the actual opc server and it's returned object from server namespace registration
    :rtype: object
    """
    server = Server()
    server.set_endpoint(server_url)

    # setup our own namespace, not really necessary but should as spec
    server_namespace = server.register_namespace(name_space)
    return server, server_namespace


def main():
    """
    Main function to run the simulation
    :return: Nothing
    :rtype: None
    """

    # The current production plan consist of making 4 parts and the corresponding details are given below
    # Part Name, Part Family Number, Quantity, Machining Sequence [Machine Id, Machining Time]
    production_plan = [["Part 0", 100000, 1, [[0, 2], [1, 4], [2, 3], [3, 5]]],
                       ["Part 1", 200000, 1, [[1, 3], [0, 1], [2, 4], [3, 2]]],
                       ["Part 2", 300000, 1, [[2, 4], [1, 5], [0, 3], [3, 2]]],
                       ["Part 3", 400000, 1, [[3, 5], [2, 1], [0, 4], [1, 4]]]]

    environment = RealTimeEnvironment(production_plan=production_plan)

    try:
        environment.run(till=100)
        print("Simulation Successfully Over")
    except KeyboardInterrupt:
        print("Simulation Interrupted")
    except Exception as error:
        print(error)


if __name__ == "__main__":
    main()
