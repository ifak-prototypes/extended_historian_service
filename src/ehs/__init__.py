# -*- coding: utf-8 -*-

"""The base module of the Extended Historian Service containing several base classes.
"""


import abc
import argparse
import concurrent.futures
from typing import Any
from ehs.api import ExtendedHistorianService_pb2, ExtendedHistorianService_pb2_grpc, DataSourceAdapter_pb2, DataSourceAdapter_pb2_grpc, Commons_pb2
import errno
import grpc
import jsonschema
import logging
import os
import os.path
import sys
import time
import yaml


__title__ = "ehs"
__description__ = "Extended Historian Service"
__version__ = "1.0.0"
__license__ = "not yet defined"
__copyright__ = "Copyright 2022 ifak e.V."


RETRY_TIME = 5  # seconds
HEADER_CONF = """
type: object
properties:
    header:
        type: object
        properties:
            title:
                type: string
            description:
                type: string
        required:
        - title
        - description
required:
- header
"""
SERVER_CONF = """
type: object
properties:
    server:
        type: object
        properties:
            address:
                type: string
            port:
                type: string
        required:
        - address
        - port
required:
- server
"""
CLIENT_CONF = """
type: object
properties:
    client:
        type: object
        properties:
            address:
                type: string
            port:
                type: string
        required:
        - address
        - port
required:
- client
"""
BROKER_CONF = """
type: object
properties:
    broker:
        type: object
        properties:
            address:
                type: string
            port:
                type: string
            client_id:
                type: string
            username:
                type: string
            password:
                type: string
        required:
        - address
        - port
        - client_id
required:
- broker
"""

class DataSource(abc.ABC):
    def ping(self) -> bool:
        logging.debug(f"ping() = True")
        return True
    @abc.abstractmethod
    def read(self, address: str) -> bool | int | float | str:
        pass
    @abc.abstractmethod
    def write(self, address: str, value: bool | int | float | str) -> None:
        pass
    @abc.abstractmethod
    def get_configuration(self) -> dict:
        pass
class Server():
    def __init__(self, model) -> None:
        self.model = model

        # the configuration needs to be set after application configuration
        self.configuration = None
    @abc.abstractmethod
    def start_up(self) -> None:
        pass
    @abc.abstractmethod
    def shut_down(self) -> None:
        pass
class Client(DataSource):
    def __init__(self) -> None:
        DataSource.__init__(self)
        # the configuration needs to be set after application configuration
        self.configuration = None
    @abc.abstractmethod
    def connect(self) -> None:
        logging.info("Client side is connected to server.")
    @abc.abstractmethod
    def disconnect(self) -> None:
        logging.info("Client side is disconnected from server.")


class GRPCServer(Server):

    def __init__(self, application, model) -> None:
        Server.__init__(self, model)
        self.application: Application = application
        self.server = None

    def read_file(self, rel_file_path):
        file_path = os.path.join(self.application.logging_dir, rel_file_path)
        with open(file_path, "rb") as file:
            retval = file.read()
            return retval

    def start_up(self) -> None:
        address = self.application.configuration["server"]["address"]
        port = int(self.application.configuration["server"]["port"])

        ca_cert = self.read_file(self.application.configuration["server"]["ca_cert"])
        server_cert = self.read_file(self.application.configuration["server"]["server_cert"])
        server_key = self.read_file(self.application.configuration["server"]["server_key"])
        credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True)

        self.server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        self.server.add_secure_port(f"{address}:{port}", credentials)

        # in the __init__ method of the model, you need to include a line like
        #     self.add_model_to_server = ExtendedHistorianService_pb2_grpc.add_ExtendedHistorianServiceServicer_to_server
        self.model.add_model_to_server(self.model, self.server)

        self.server.start()
        self.server.wait_for_termination()

    def shut_down(self) -> None:
        self.server.stop(grace=None)
        time.sleep(5)  # still show the message for 5 seconds on a closing terminal
        sys.exit(0)
class GRPCClient(Client):
    
    def __init__(self, app) -> None:
        self.app: Application = app
        self.grpc_channel = None
    
    def read_file(self, rel_file_path):
        file_path = os.path.join(self.app.logging_dir, rel_file_path)
        with open(file_path, "rb") as file:
            retval = file.read()
            return retval

    def connect(self) -> None:
        address = self.app.configuration["client"]["address"]
        port = int(self.app.configuration["client"]["port"])

        ca_cert = self.read_file(self.app.configuration["client"]["ca_cert"])
        client_cert = self.read_file(self.app.configuration["client"]["client_cert"])
        client_key = self.read_file(self.app.configuration["client"]["client_key"])
        credentials = grpc.ssl_channel_credentials(ca_cert, client_key, client_cert)

        self.grpc_channel = grpc.secure_channel(f"{address}:{port}", credentials)

    def disconnect(self) -> None:
        return super().disconnect()



class Application(abc.ABC):
    def __init__(self) -> None:
        # prepare the program argument parser
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "-c",
            "--configuration",
            type=str,
            required=False,
            help="Location of the configuration file. Data and log files will be saved in relative directories."
            )
        self.parser.add_argument(
            "-l",
            "--loglevel",
            type=str,
            required=False,
            help="Defines the logging level out of [DEBUG, INFO, WARNING, ERROR, CRITICAL], while default is INFO."
            )

        self.configuration_schemas: list(str) = []
        self.logging_dir: str = None
        self.config_file: str = None
        self.client: Client = None
        self.server: Server = None
    def configure(self) -> bool:
        """Creates self.parameters and self.configuration dictionaries.
        """
        configured = False

        # initialize the program parameters (self.parameters)
        self.parameters = vars(self.parser.parse_args())

        # define the logging level
        logging_level = "INFO"
        if self.parameters["loglevel"]:
            logging_level = self.parameters["loglevel"]
        
        # initialize the configuration (self.configuration)
        try:
            self.config_file = self.parameters["configuration"]
            self.logging_dir = os.path.dirname(self.config_file)
            
            self.configure_logging(self.logging_dir, logging_level)
            self.load_configuration(self.parameters["configuration"])
            
            configured = True

        except Exception as e:
            self.logging_dir = os.getcwd()
            self.config_file = os.path.join(self.logging_dir, "config.yaml")
            
            self.configure_logging(self.logging_dir, logging_level)
            
            try:
                logging.warning(f"You didn't specify a valid configuration file via the '-c' or '--configuration' option. {str(e)} I try to find a 'conf.yaml' in the current working directory.")
                self.load_configuration(self.config_file)
                logging.debug(f"Loaded successfully the configuration file '{self.config_file}'")
            
                configured = True
            
            except Exception as e:
                logging.error(f"Loading the configuration file '{self.config_file}' also didn't work. {str(e)}")
                logging.error(e)

                configured = False

        return configured
    def configure_logging(self, logging_dir, logging_level):
        log_format = '%(asctime)s.%(msecs)03d %(levelname)-8s : %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # logging level
        numeric_level = getattr(logging, logging_level.upper(), None)
        numeric_level_error = None
        if not isinstance(numeric_level, int):
            numeric_level = getattr(logging, "INFO", None)
            numeric_level_error = f"Invalid log level '{logging_level}'. The software will continue with log level 'INFO'."

        # remove all handlers
        root = logging.getLogger()
        while len(root.handlers) > 0:
            root.removeHandler(root.handlers[0])
        while len(root.filters) > 0:
            root.removeFilter(root.filters[0])

        
        if os.path.isdir(logging_dir):
            # log to a file
            logging.basicConfig(
                filename=os.path.join(logging_dir, 'logfile.txt'),
                level=numeric_level,
                format=log_format,
                datefmt=date_format,
            )

            # additionally log to the screen
            formatter = logging.Formatter(log_format)
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            logging.getLogger().addHandler(stream_handler)

        else:
            # directly log to the screen
            logging.basicConfig(
                level=numeric_level,
                format=log_format,
                datefmt=date_format,
            )
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), logging_dir)

        # now we configured the logger, so we print out possible log level errors
        if numeric_level_error:
            logging.error(numeric_level_error)
    def load_configuration(self, config_file):
        with open(config_file, "r") as stream:
            configuration = yaml.safe_load(stream)

            for schema_str in self.configuration_schemas:
                schema = yaml.safe_load(schema_str)

                # throw an exception, if the file is not valid
                jsonschema.validate(instance=configuration, schema=schema)

            self.configuration: dict = configuration
    def start(self):
        if self.client is not None:
            self.client.connect()
        if self.server is not None:
            self.server.start_up()
    def stop(self):
        if self.server is not None:
            self.server.shut_down()
        if self.client is not None:
            self.client.disconnect()
    def run(self):
        try:
            while True:
                try:
                    self.show_start_message()
                    self.start()
                except Exception as e:
                    logging.error(e)
                    time.sleep(RETRY_TIME)
        except KeyboardInterrupt:
            self.show_stop_message()
            self.stop()
    def show_start_message(self):
        """shows title and description of conf.yaml/header ... and server msg 'listening on port' ... and client msg 'sending to server ...'."""
        print(f"*** {self.configuration['header']['title']} ***")
        logging.info(f"{self.configuration['header']['title']} is starting ...")
        if "server" in self.configuration:
            logging.info(f"Listening on interface '{self.configuration['server']['address']}' and port '{self.configuration['server']['port']}'.")
        if "client" in self.configuration:
            logging.info(f"Calling server on interface '{self.configuration['client']['address']}' and port '{self.configuration['client']['port']}'.")
        if "broker" in self.configuration:
            logging.info(f"Communicating with broker '{self.configuration['broker']['address']}' and port '{self.configuration['broker']['port']}'.")
    def show_stop_message(self):
        """shows 'shut down ... releasing network connections ... have a nice day'"""
        logging.info(f"{self.configuration['header']['title']} shuts down ...")
        if "server" in self.configuration:
            logging.info(f"Releasing interface '{self.configuration['server']['address']}' port '{self.configuration['server']['port']}'.")
        logging.info("-")
        print(f"*** Have a nice day! ***")



class Device(Application):
    """A Device is an Application with a Server, which provides DataPool functionality."""
    def __init__(self, server: Server):
        Application.__init__(self)
        self.server: Server = server

        # TODO: check if self.interface_implementation can be removed
        self.interface_implementation: Any = None


class AdapterGRPCInterface(Client):
    """Implements all functions of a DataSourceAdapter in a gRPC specific manner. It is published by a gRPC server."""
    def __init__(self, client: Client):
        self.client: Client = client
        self.configuration = None
        self.add_model_to_server = DataSourceAdapter_pb2_grpc.add_DataSourceAdapterServicer_to_server
    
    def connect(self):
        self.client.connect()
    def disconnect(self):
        self.client.disconnect()
    
    def ping(self, request, context):
        value = self.client.ping()
        response = Commons_pb2.PingResponse(value=value)
        return response
    def read(self, request, context):
        retval = Commons_pb2.Value()
        status = Commons_pb2.UNKNOWN

        try:
            value = self.client.read(request.address)
            status = Commons_pb2.SUCCESS

            value_type = type(value)
            if value_type is bool:
                retval.bool_value = value
            elif value_type is int:
                retval.int64_value = value
            elif value_type is float:
                retval.double_value = value
            elif value_type is str:
                retval.string_value = value
            else:
                logging.error(f"Read of unallowed data type '{value_type}'.")
                status = Commons_pb2.TYPE_MISMATCH

        except Exception as e:
            logging.error(e)
            status = Commons_pb2.DEVICE_NOT_RESPONDING
        
        response = DataSourceAdapter_pb2.ReadResponse(value=retval, status=status)
        return response
    def write(self, request, context):
        value = self.client.write(request.address, request.value)
        response = DataSourceAdapter_pb2.WriteResponse()
        return response
    def get_configuration(self, request, context):
        # we return the configuration of the Adapter, not that of the device!
        value = yaml.dump(self.configuration, default_flow_style=False)
        response = Commons_pb2.PingResponse(value=value)
        return response

    
class Adapter(Application):
    """An Application with a gRPC interface to a DeviceClient.

    Ideas:
    Adapters should be able to give the permissible address space of the device upwards.
    The device cannot do this itself, that it is configured 'somehow'.
    For an adapter a mandatory section 'device' is to be introduced in the 'config.yaml'.
    With this the channel assignment can be done.
    """
    def __init__(self, client):
        Application.__init__(self)
        self.configuration_schemas = [HEADER_CONF, SERVER_CONF, CLIENT_CONF]
        self.client = AdapterGRPCInterface(client)
        self.server: GRPCServer = GRPCServer(self, self.client)

