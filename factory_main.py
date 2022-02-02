# -*- coding: utf-8 -*-
"""
Virtual Factory Main
====================
Main script which calls the necessary modules to run a simulated factory
"""
# User imports
from simulated_factory import RealTimeEnvironment


def main():
    """
    Main function to run the simulation
    :return: Nothing
    :rtype: None
    """

    # The current production plan consist of making 4 parts and the corresponding details are given below
    # Part Name, Part Family Number, Quantity, Machining Sequence [Machine Id, Machining Time]
    production_plan = [["Part 0", 100000, 100, [[0, 2], [1, 4], [2, 3], [3, 5]]],
                       ["Part 1", 200000, 100, [[1, 3], [0, 1], [2, 4], [3, 2]]],
                       ["Part 2", 300000, 100, [[2, 4], [1, 5], [0, 3], [3, 2]]],
                       ["Part 3", 400000, 100, [[3, 5], [2, 1], [0, 4], [1, 4]]]]

    environment = RealTimeEnvironment(production_plan=production_plan)

    try:
        environment.run()
        print("Simulation Successfully Over")
    except KeyboardInterrupt:
        print("Simulation Interrupted")
    except Exception as error:
        print(error)


if __name__ == "__main__":
    main()
