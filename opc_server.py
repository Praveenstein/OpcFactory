import time

from opcua import ua, Server

if __name__ == "__main__":

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "sample_namespace"
    server_namespace = server.register_namespace(uri)

    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()

    # populating our address space
    myobj = objects.add_object(server_namespace, "MyObject")
    myvar = myobj.add_variable(server_namespace, "MyVariable", 6.7)
    myvar_2 = myobj.add_variable(server_namespace, "MyVariable_2", 7.6)
    myvar.set_writable()  # Set MyVariable to be writable by clients

    # starting!
    server.start()

    print(myobj.get_children()[0].get_value())
    print(myobj.get_children()[1].get_value())
    try:
        count = 0
        while True:
            time.sleep(1)
            count += 0.1
            myvar.set_value(count)
    except KeyboardInterrupt:
        print('Interrupted')
    finally:
        # close connection, remove subcsriptions, etc
        server.stop()
