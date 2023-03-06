# -*- coding: utf-8 -*-

"""The example code for an XML RPC device.
"""

import ehs
import ehs.xmlrpc
import logging
import math
import time
import random


class MyDeviceInterfaceImplementation(ehs.DataSource):
    """Implements all functions of a Device. It is published by an XML-RPC server."""

    def __init__(self) -> None:
        ehs.DataSource.__init__(self)
        self.configuration: dict = None
        self.values = {
            'CurrentTimeSec': int(13),
            'WorkLoadHNA13ZX23': 3.1415926,
            'RpcBool': True,
            'RpcStr': "Hello world!"
        }

    def update(self):
        self.values['CurrentTimeSec'] = int(time.time())
        self.values['WorkLoadHNA13ZX23'] = (4 * math.sin(time.time()/10)) + random.uniform(-0.8, 0.8)


    def read(self, address: str) -> bool | int | float | str:
        logging.debug(f"read(address='{address}')")
        self.update()
        if address in self.values:
            return self.values[address]
        else:
            logging.error(f"Bad address '{address}' for reading.")
            return None

    def write(self, address: str, value: bool | int | float | str) -> None:
        logging.debug(f"write(address:str='{address}', value:{type(value)}='{value}')")
        if address in self.values:
            # danger: here, we don't check the data type
            self.values[address] = value
        else:
            logging.error(f"Bad address '{address}' for writing.")

    def get_configuration(self) -> dict:
        logging.debug(f"get_configuration() = {self.configuration}")
        return self.configuration


class MyDevice(ehs.xmlrpc.XMLRPCDevice):
    def __init__(self) -> None:
        ehs.xmlrpc.XMLRPCDevice.__init__(self, MyDeviceInterfaceImplementation())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    device = MyDevice()
    if device.configure():
        device.server.configuration = device.configuration
        device.interface_implementation.configuration = device.configuration
        device.run()