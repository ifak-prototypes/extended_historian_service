# -*- coding: utf-8 -*-

"""User interface for starting, stopping and restarting services.

Each EHS, device, adapter, application ... service needs to be started in the integration test.
Here we provide convenient functions for starting them.

This application is driven by the CONFIG data structure, which contains the architecture
of the complete system and references to start and stop scripts.

It is a tree of nodes, while each node can contain following elements:
  - start: the start script
  - stop: the stop script
  - cwd: current working directory
  - further branch nodes, which start with an uppercase letter

Scripts are evaluated in sub-processes. They are considered to be unix shell scripts.
"""


import yaml
import manage
import sys


CONFIG = yaml.safe_load('''
    System:
        Infrastructure:
            Arrowhead System:
                start: python cloud_setup.py
                stop: docker -f ./test/arrowhead/core_services_01/docker-compose.yml compose down
                cwd: ./test/arrowhead/core_services_01
        Devices:
            XML RPC Device:
                start: python -m device.xmlrpc_device
                cwd: test/device/xmlrpc_01
            Arrowhead Device:
                start: python -m device.arrowhead_device -c test/device/arrowhead_01/config.yaml -l DEBUG
                cwd: .
        Adapters:
            XML RPC Adapter:
                start: python -m ehs.xmlrpc
                cwd: test/adapter/xmlrpc_01
            Arrowhead Adapter:
                start: python -m ehs.arrowhead -c test/adapter/arrowhead_01/config.yaml -l DEBUG
                cwd: .
        EHS:
            start: python -m ehs.ehsx
            cwd: test/ehs/configuration_01
        Application:
            start: python test/application/app_01/application.py
            cwd: .
    ''')


class Manager(manage.AppManager):

    def __init__(self):
        manage.AppManager.__init__(self, prompt="EHS-Manager$ ", config=CONFIG, font="xos4 Terminus")

    def do_start_Infrastructure(self, args):
        self.do_start_Arrowhead_System(None)

    def do_start_System(self, args):
        self.do_start_Infrastructure(None)
        self.do_start_Devices(None)
        self.do_start_Adapters(None)
        self.do_start_EHS(None)
        self.do_start_Application(None)
    
    def do_start_Infrastructure(self, args):
        self.do_start_Arrowhead_System(None)
    
    def do_start_Devices(self, args):
        self.do_start_XML_RPC_Device(None)
        self.do_start_Arrowhead_Device(None)
    
    def do_start_Adapters(self, args):
        self.do_start_XML_RPC_Adapter(None)
        self.do_start_Arrowhead_Adapter(None)

    def do_stop_System(self, args):
        self.do_stop_Devices(None)
        self.do_stop_Adapters(None)
        self.do_stop_EHS(None)
        self.do_stop_Application(None)
        self.do_stop_Infrastructure(None)
    
    def do_stop_Infrastructure(self, args):
        self.do_stop_Arrowhead_System(None)
    
    def do_stop_Devices(self, args):
        self.do_stop_Arrowhead_Device(None)
        self.do_stop_XML_RPC_Device(None)
    
    def do_stop_Adapters(self, args):
        self.do_stop_Arrowhead_Adapter(None)
        self.do_stop_XML_RPC_Adapter(None)


if __name__ == '__main__':
    print("Arrowhead Extended Historian Service - integration test management tool")
    print("  HINT: The tool should run from the root of the repository")
    print("  HINT: for KDE konsole: Konsole -> Settings -> Configure Konsole: disable 'show window title on titlebar'\n")

    manage.extend_manager(CONFIG, "xxx")
    manager = Manager()
    manager.do_print_architecture(None)
    sys.exit(manager.cmdloop())
