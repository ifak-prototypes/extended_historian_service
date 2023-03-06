# -*- coding: utf-8 -*-

"""The XML RPC specific module containing device and adapter code.
"""

from distutils.command.config import config
from typing import Any
import ehs
import logging
import sys
import time
import xmlrpc.client
import xmlrpc.server


class XMLRPCServer(ehs.Server):
    """A server, which can start-up and shut-down and internally uses a SimpleXMLRPCServer."""

    def __init__(self, interface_implementation) -> None:
        ehs.Server.__init__(self, interface_implementation)
        self.configuration: dict = None
        self.server: xmlrpc.server.SimpleXMLRPCServer = None

    def start_up(self) -> None:
        address = self.configuration["server"]["address"]
        port = int(self.configuration["server"]["port"])
        self.server = xmlrpc.server.SimpleXMLRPCServer((address, port), allow_none=True, logRequests=False)
        self.server.register_instance(self.model)
        self.server.serve_forever()

    def shut_down(self) -> None:
        self.server.shutdown()
        time.sleep(5)  # still show the message for 5 seconds on a closing terminal
        sys.exit(0)


class XMLRPCClient(ehs.Client):
    """Provides communication protocol agnostic Client and DataSource interfaces, which behind the scenes access an XML-RPC server."""

    def __init__(self) -> None:
        ehs.Client.__init__(self)
        self.proxy: xmlrpc.client.ServerProxy = None

    def connect(self):
        adr = self.configuration['client']['address']
        port = self.configuration['client']['port']
        self.proxy = xmlrpc.client.ServerProxy(f"http://{str(adr)}:{str(port)}")

    def disconnect(self):
        pass

    def read(self, address: str) -> bool | int | float | str:
        logging.debug(f"read(address='{address}')")
        return self.proxy.read(address)

    def write(self, address: str, value: bool | int | float | str) -> None:
        logging.debug(f"write(address:str='{address}', value:{type(value)}='{value}')")
        return self.proxy.write(address, value)

    def ping(self):
        logging.debug(f"ping()")
        return self.proxy.ping()

    def get_configuration(self) -> dict:
        logging.debug(f"get_configuration() = {self.configuration['client']}")
        return self.configuration


class XMLRPCDevice(ehs.Device):

    def __init__(self, interface_implementation) -> None:
        ehs.Device.__init__(self, XMLRPCServer(interface_implementation))
        self.interface_implementation: Any = interface_implementation  # prefered type: ehs.DataPool


class XMLRPCAdapter(ehs.Adapter):
    """An XML RPC Adapter is an Adapter with an XML RPC client interface."""
    pass


if __name__ == "__main__":
    # Start the XMLRPCAdapter, since Devices need anyway an extra module implementing a Model
    logging.basicConfig(level=logging.INFO)
    adapter = XMLRPCAdapter(XMLRPCClient())
    if adapter.configure():
        adapter.client.client.configuration = adapter.configuration
        adapter.run()
