# -*- coding: utf-8 -*-

"""The Arrowhead specific module containing device and adapter code.
"""

import arrowhead_client.client.implementations
import ehs
import logging


class ArrowheadServer(ehs.Server):
    pass


class ArrowheadClient(ehs.Client):
    """Provides communication protocol agnostic Client and DataSource interfaces, which behind the scenes access an Arrowhead provider."""

    def __init__(self) -> None:
        ehs.Client.__init__(self)
        self.consumer = None

    def connect(self):
        config = self.configuration["client"]
        self.consumer = arrowhead_client.client.implementations.SyncClient.create(
                system_name=config["system_name"],
                address=config["address"],
                port=int(config["port"]),
                keyfile=config["keyfile"],
                certfile=config["certfile"],
                cafile=config["cafile"],
        )
        self.consumer.setup()
        #adr = self.configuration['client']['address']
        #port = self.configuration['client']['port']
        #self.proxy = xmlrpc.client.ServerProxy(f"http://{str(adr)}:{str(port)}")

        self.consumer.add_orchestration_rule('read', 'PUT')
        self.consumer.add_orchestration_rule('write', 'PUT')
        self.consumer.add_orchestration_rule('hello-arrowhead', 'GET')
        self.consumer.add_orchestration_rule('echo', 'PUT')


    def disconnect(self):
        pass

    def read(self, address: str) -> bool | int | float | str:
        logging.debug(f"read(address='{address}')")
        read_response = self.consumer.consume_service('read', json={'msg': 'READ', 'address': address})
        print(read_response.read_json())
        response = read_response.read_json()
        t = response["type"]
        v = response["value"]
        if t == "int":
            return int(v)
        elif t == "float":
            return float(v)
        elif t == "bool":
            return bool(v)
        elif t == "str":
            return str(v)
        else:
            return None

    def write(self, address: str, value: bool | int | float | str) -> None:
        logging.debug(f"write(address:str='{address}', value:{type(value)}='{value}')")
        write_response = self.consumer.consume_service('write', json={'address': 'MW23', 'value': '13'})
        print(write_response.read_json())

    def ping(self):
        logging.debug(f"ping()")
        response = self.consumer.consume_service('hello-arrowhead')
        print(response.read_json()['msg'])

    def get_configuration(self) -> dict:
        logging.debug(f"get_configuration() = {self.configuration['client']}")
        return self.configuration

    def echo(self):
        logging.debug(f"echo()")
        echo_response = self.consumer.consume_service('echo', json={'msg': 'ECHO'})
        print(echo_response.read_json()['msg'])


class ArrowheadDevice(ehs.Device):

    def __init__(self) -> None:
        ehs.Device.__init__(self, server=None)  # instantiates an Application with a configuration


class ArrowheadAdapter(ehs.Adapter):
    pass


if __name__ == "__main__":
    # Start the ArrowheadAdapter
    logging.basicConfig(level=logging.INFO)
    adapter = ArrowheadAdapter(ArrowheadClient())
    if adapter.configure():
        adapter.client.client.configuration = adapter.configuration
        adapter.run()
        adapter.read("dummy")
