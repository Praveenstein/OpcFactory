from opcua import Client


if __name__ == "__main__":

    client = Client("opc.tcp://localhost:4840/freeopcua/server/")
    # client = Client("opc.tcp://admin@localhost:4840/freeopcua/server/") #connect using a user
    try:
        client.connect()
        print(client.get_node("ns=2;i=2").get_value())

    except KeyboardInterrupt:
        print('Interrupted')

    finally:
        client.disconnect()
