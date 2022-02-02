import time
from asyncua.sync import Server

if __name__ == "__main__":

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "sample_namespace"
    server_namespace = server.register_namespace(uri)

    # get Objects node, this is where we should put our nodes
    root_objects = server.nodes.objects

    # populating our address space
    my_object = root_objects.add_object(server_namespace, "MyObject")
    my_variable = my_object.add_variable(server_namespace, "MyVariable", 6.7)
    my_variable_2 = my_object.add_variable(server_namespace, "MyVariable_2", 7.6)
    my_variable.set_writable()  # Set MyVariable to be writable by clients

    # starting!
    server.start()

    try:
        count = 0
        while True:
            print(my_object.get_children()[0].get_value())
            #print(my_object.get_children()[1].get_value())
            time.sleep(1)
            count += 1.0
            my_variable.write_value(count)
    except KeyboardInterrupt:
        print('Interrupted')
    finally:
        # close connection, remove subcsriptions, etc
        server.stop()
