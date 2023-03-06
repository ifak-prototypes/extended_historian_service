# -*- coding: utf-8 -*-

"""The EHS specific module containing also gRPC specific stuff for accessing adapters and user applications.
"""

import ehs
from ehs import RETRY_TIME
from ehs.api import ExtendedHistorianService_pb2, ExtendedHistorianService_pb2_grpc, DataSourceAdapter_pb2, DataSourceAdapter_pb2_grpc, Commons_pb2
from ehs import GRPCServer
import grpc
import logging
import os
import os.path
import sqlite3
import time
from typing import Dict, List, Tuple
import yaml
import apscheduler.events
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler


ADAPTER_CONF = """
type: object
properties:
    adapters:
        type: array
        items:
            type: object
            properties:
                client:
                    type: object
                    properties:
                        name:
                            type: string
                        description:
                            type: string
                        address:
                            type: string
                        port:
                            type: string
                    required:
                    - name
                    - address
                    - port
            required:
            - client
required:
- adapters
"""


def read_file(script_dir, rel_file_path):
    file_path = os.path.join(script_dir, rel_file_path)
    with open(file_path, "rb") as file:
        retval = file.read()
        return retval


def get_ehs_proxy(script_dir, config) -> ExtendedHistorianService_pb2_grpc.ExtendedHistorianServiceStub:
    address = config["client"]["address"]
    port = int(config["client"]["port"])

    ca_cert = read_file(script_dir, config["client"]["ca_cert"])
    client_cert = read_file(script_dir, config["client"]["client_cert"])
    client_key = read_file(script_dir, config["client"]["client_key"])
    credentials = grpc.ssl_channel_credentials(ca_cert, client_key, client_cert)
    
    channel = grpc.secure_channel(f"{address}:{port}", credentials)
    ehs_proxy = ExtendedHistorianService_pb2_grpc.ExtendedHistorianServiceStub(channel)
    return ehs_proxy

def get_adapter_proxy(script_dir, config, server_config) -> DataSourceAdapter_pb2_grpc.DataSourceAdapterStub:
    """Used by the EHS to get a prox"""
    address = config["client"]["address"]
    port = int(config["client"]["port"])

    ca_cert = read_file(script_dir, server_config["server"]["ca_cert"])
    server_cert = read_file(script_dir, server_config["server"]["server_cert"])
    server_key = read_file(script_dir, server_config["server"]["server_key"])
    credentials = grpc.ssl_channel_credentials(ca_cert, server_key, server_cert)
    
    channel = grpc.secure_channel(f"{address}:{port}", credentials)
    adapter_proxy = DataSourceAdapter_pb2_grpc.DataSourceAdapterStub(channel)
    return adapter_proxy


def get_config(script_dir):
    config_file = os.path.join(script_dir, "config.yaml")
    with open(config_file, "r") as file:
        configuration = yaml.safe_load(file)
        return configuration


class ChannelAddress:

    def __init__(self, adapter_name, channel_name, channel_type):
        self.adapter_name = adapter_name
        self.channel_name = channel_name
        self.channel_type = channel_type
    
    def __str__(self):
        return f"{self.adapter_name}.{self.channel_name}: {self.channel_type}"

class EHSClient():
    """This class is to be used by data analytics applications to easily access the EHS.
    """

    def __init__(self, script_dir) -> None:
        self.script_dir = script_dir
        self.configuration = get_config(self.script_dir)
        self.ehs_proxy = get_ehs_proxy(self.script_dir, self.configuration)

    def ping(self):
        logging.debug(f"ping()")
        request = Commons_pb2.PingRequest()  # ----- HIER WEITER: ping request <- Commons
        return self.ehs_proxy.ping(request).value

    def get_configuration(self) -> str:
        logging.debug(f"get_configuration()")
        request = Commons_pb2.GetConfigurationRequest()
        return self.ehs_proxy.get_configuration(request).value

    def set_configuration(self, configuration: str) -> None:
        logging.debug(f"set_configuration(configuration=\n{configuration}\n)")
        request = ExtendedHistorianService_pb2.SetConfigurationRequest(configuration=configuration)
        return self.ehs_proxy.set_configuration(request)

    def get_channels(self) -> List[ChannelAddress]:
        logging.debug(f"get_channels()")
        request = ExtendedHistorianService_pb2.GetChannelsRequest()
        cal = self.ehs_proxy.get_channels(request).value  # cal ... channel address list
        retval = []
        for ca in cal:
            channel_address = ChannelAddress(ca.adapter_name, ca.channel_name, ca.channel_type)
            retval.append(channel_address)
        return retval

    def get_values(self, channel_addresses: List[ChannelAddress]) -> List[Tuple[bool | int | float | str, int]]:
        logging.debug(f"get_values(channel_addresses={channel_addresses})")
        request = ExtendedHistorianService_pb2.GetValuesRequest()
        for a in channel_addresses:
            ca = request.channel_addresses.add()
            ca.adapter_name = a.adapter_name
            ca.channel_name = a.channel_name
            ca.channel_type = a.channel_type
        vl = self.ehs_proxy.get_values(request).value
        retval = []
        counter = 0
        for v in vl:
            if channel_addresses[counter].channel_type == "bool":
                retval.append((v.value.bool_value, v.status))
            elif channel_addresses[counter].channel_type == "int64":
                retval.append((v.value.int64_value, v.status))
            elif channel_addresses[counter].channel_type == "double":
                retval.append((v.value.double_value, v.status))
            elif channel_addresses[counter].channel_type == "string":
                retval.append((v.value.string_value, v.status))
            else:
                logging.error(f"Bad channel data type: {channel_addresses[counter].channel_type}")
            counter += 1
        return retval

    def get_histories(self, channel_addresses: List[ChannelAddress], begin_inclusive: int, end_exclusive: int) -> list[list[list[int, bool | int | float | str]]]:
        """Return value ist a list of time series, while each time series is a list of tuples, with a time stamp and a value."""
        logging.debug(f"get_histories(channel_addresses={channel_addresses}, begin_inclusive={begin_inclusive}, end_exclusive={end_exclusive})")
        request = ExtendedHistorianService_pb2.GetHistoriesRequest(begin_inclusive=begin_inclusive, end_exclusive=end_exclusive)
        for a in channel_addresses:
            ca = request.channel_addresses.add()
            ca.adapter_name = a.adapter_name
            ca.channel_name = a.channel_name
            ca.channel_type = a.channel_type
        tsvl = self.ehs_proxy.get_histories(request).value
        retval = []
        counter = 0

        for ts in tsvl:
            if channel_addresses[counter].channel_type == "bool":
                vl = []
                for tv in ts.value:
                    # value = TimeSeriesValue(tv.time, tv.value.bool_value)
                    value = [tv.time, tv.value.bool_value]
                    vl.append(value)
                retval.append(vl)
            elif channel_addresses[counter].channel_type == "int64":
                vl = []
                for tv in ts.value:
                    value = [tv.time, tv.value.int64_value]
                    vl.append(value)
                retval.append(vl)
            elif channel_addresses[counter].channel_type == "double":
                vl = []
                for tv in ts.value:
                    value = [tv.time, tv.value.double_value]
                    vl.append(value)
                retval.append(vl)
            elif channel_addresses[counter].channel_type == "string":
                vl = []
                for tv in ts.value:
                    value = [tv.time, tv.value.string_value]
                    vl.append(value)
                retval.append(vl)
            else:
                logging.error(f"Bad channel data type: {channel_addresses[counter].channel_type}")
            counter += 1
        return retval

    # deprecated:
    def get_adapter_list(self):
        logging.debug(f"get_adapter_list()")
        request = ExtendedHistorianService_pb2.GetAdapterListRequest()
        return self.ehs_proxy.get_adapter_list(request).value


class EHSGRPCInterface(ExtendedHistorianService_pb2_grpc.ExtendedHistorianServiceServicer):
    """This is the gRPC server-side implementation of the EHS functionality used by e.g. data analytics and configuration software.

    Args:
        ExtendedHistorianService_pb2_grpc: the server-side skeletons generated from the ExtendedHistorianService.proto file
    """

    def __init__(self, ehs):
        self.ehs: EHS = ehs
        self.configuration = self.ehs.configuration
        self.add_model_to_server = ExtendedHistorianService_pb2_grpc.add_ExtendedHistorianServiceServicer_to_server

    def ping(self, request, context):
        logging.debug(f"ExtendedHistorianService.ping(..)")

        response = Commons_pb2.PingResponse(value=True, status=Commons_pb2.SUCCESS)

        return response
    
    def get_configuration(self, request, context):
        logging.debug(f"ExtendedHistorianService.get_configuration(..)")

        response = Commons_pb2.GetConfigurationResponse()

        try:
            response.value = yaml.dump(self.configuration, default_flow_style=False)
            response.status = Commons_pb2.SUCCESS

        except Exception as e:
            logging.error(e)
            response.status = Commons_pb2.UNKNOWN

        return response

    def set_configuration(self, request, context):
        logging.debug(f"ExtendedHistorianService.set_configuration(..)")

        response = ExtendedHistorianService_pb2.SetConfigurationResponse()

        try:
            with open(self.ehs.config_file, "w") as f:
                f.write(request.configuration)

            response.status = Commons_pb2.SUCCESS

        except Exception as e:
            logging.error(e)
            
            response.status = Commons_pb2.UNKNOWN

        return response
    
    def get_channels(self, request, context):
        logging.debug(f"ExtendedHistorianService.get_channels(..)")

        response = ExtendedHistorianService_pb2.GetChannelsResponse()

        try:
            for c in self.configuration['adapters']:
                for v in c['client']['variables']:
                    channel = response.value.add()
                    channel.adapter_name = c['client']['name']
                    channel.channel_name = v['name']
                    channel.channel_type = v['type']

        except Exception as e:
            logging.error(e)
            
            response.status = Commons_pb2.UNKNOWN

        return response

    def get_values(self, request, context):
        logging.debug(f"ExtendedHistorianService.get_channels(..)")

        response = ExtendedHistorianService_pb2.GetValuesResponse()

        try:

            channel_addresses = request.channel_addresses

            for channel_address in channel_addresses:

                adapter_name = channel_address.adapter_name
                channel_name = channel_address.channel_name
                channel_type = channel_address.channel_type
                adapter = self.ehs.adapters[adapter_name]
                read_request = DataSourceAdapter_pb2.ReadRequest(address=channel_name)
                response_value = response.value.add()

                try:
                    read_response = adapter.read(read_request)
                    response_value.status = read_response.status

                    if channel_type == 'bool':
                        response_value.value.bool_value = read_response.value.bool_value
                    
                    elif channel_type == 'int64':
                        response_value.value.int64_value = read_response.value.int64_value
                    
                    elif channel_type == 'double':
                        response_value.value.double_value = read_response.value.double_value
                    
                    elif channel_type == 'string':
                        response_value.value.string_value = read_response.value.string_value
                    
                    else:
                        logging.error(f"Bad data type request in get_channels({channel_address}).")
                            
                        response_value.status = Commons_pb2.TYPE_MISMATCH

                except Exception as e:
                    logging.error(e)

                    response_value.status = Commons_pb2.ADAPTER_NOT_RESPONDING

        except Exception as e:
            logging.error(e)
            
            response.status = Commons_pb2.UNKNOWN

        return response

    # def get_histories(self, channel_addresses: List[ChannelAddress], begin_inclusive: int, end_exclusive: int) -> List[List[TimeSeriesValue]]:
    def get_histories(self, request, context):
        logging.debug(f"ExtendedHistorianService.get_channels(..)")

        response = ExtendedHistorianService_pb2.GetHistoriesResponse()

        try:
            channel_addresses = request.channel_addresses
            begin_inclusive = request.begin_inclusive
            end_exclusive = request.end_exclusive

            for channel_address in channel_addresses:
                adapter_name = channel_address.adapter_name
                channel_name = channel_address.channel_name
                channel_type = channel_address.channel_type
                list_of_time_series_values = response.value.add()
                db_time_series = self.ehs.db.get_time_series(adapter_name, channel_name, begin_inclusive, end_exclusive)

                for time_stamp, value in db_time_series:
                    time_series_value = list_of_time_series_values.value.add()
                    time_series_value.time = int(time_stamp)
                    
                    if channel_type == 'bool':
                        time_series_value.value.bool_value = value
                    
                    elif channel_type == 'int64':
                        time_series_value.value.int64_value = value
                    
                    elif channel_type == 'double':
                        time_series_value.value.double_value = value
                    
                    elif channel_type == 'string':
                        time_series_value.value.string_value = value
                    
                    else:
                        logging.error(f"Bad requestet data type '{channel_type}' in get_histories for {channel_address}.")

                        response.status = Commons_pb2.TYPE_MISMATCH

        except Exception as e:
            logging.error(e)
            
            response.status = Commons_pb2.UNKNOWN

        return response

    # deprecated:
    def get_adapter_list(self, request, context):
        response = ExtendedHistorianService_pb2.GetAdapterListResponse()
        for adapter_configuration in self.configuration['adapters']:
            adapter_info = response.value.add()
            adapter_info.name = adapter_configuration['client']['name']
            adapter_info.description = adapter_configuration['client']['description']
            adapter_info.address = adapter_configuration['client']['address']
            adapter_info.port = adapter_configuration['client']['port']
            adapter = self.ehs.adapters[adapter_configuration['client']['name']]
            try:
                request = Commons_pb2.PingRequest()
                adapter_info.can_provide_data = adapter.ping(request).value
            except Exception as e:
                logging.error(f"{adapter_configuration['client']['name']}: {e}")
                adapter_info.can_provide_data = False
        return response


class Database:


    def __init__(self, root_dir):
        """root_dir should be ehs.logging_dir"""
        self.data_dir = os.path.join(root_dir, 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.data_file = os.path.join(self.data_dir, 'data.db')
        # TODO sqlite3 check_same_thread is possibly dangerous. use a pykka actor instead.
        self.db_con = sqlite3.connect(self.data_file, check_same_thread=False)
        self.db_cur = self.db_con.cursor()
        self.channel_types = {'bool': 'INTEGER', 'int64': 'INTEGER', 'double': 'REAL', 'string': 'TEXT'}

    def channel_table_name(self, channel_ref):
        """Double underlines are forbidden for Adapter names!"""
        return channel_ref['adapter'] + '__' + channel_ref['variable']

    def contains_table(self, channel_table_name) -> bool:
        # cur = self.db_con.cursor()
        res = self.db_cur.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        table_names = []
        for row in res:
            table_names.append(row[0])
        return  channel_table_name in table_names

    def create_table(self, channel_table_name, channel_type):
        # cur = self.db_con.cursor()
        sqlcmd = "CREATE TABLE {tn} (time REAL, value {ct});".format(tn=channel_table_name, ct=self.channel_types[channel_type])
        if not self.contains_table(channel_table_name):
            self.db_cur.execute(sqlcmd)
            self.db_con.commit()

    def save(self, channel_ref, t, value):
        # cur = self.db_con.cursor()
        sqlcmd = "INSERT INTO {tn} VALUES ({t}, {v});"

        # make an exception for strings and bools
        if type(value) is str:
            sqlcmd = "INSERT INTO {tn} VALUES ({t}, \"{v}\");"
        if type(value) is bool:
            value = int(value)

        sqlcmd = sqlcmd.format(
            tn=self.channel_table_name(channel_ref),
            t=t,
            v=value
        )

        # whether type(value) fits the table datatype is currently unchecked

        try:
            self.db_con.execute(sqlcmd)
        except Exception as e:
            print(e)
        self.db_con.commit()

    def get_time_series(self, adapter_name, channel_name, begin_inclusive, end_exclusive):
        sqlcmd = "SELECT * FROM {tab} WHERE time>={beg} AND time<{end};"
        table_name = self.channel_table_name({'adapter': adapter_name, 'variable': channel_name})
        sqlcmd = sqlcmd.format(
            tab=table_name,
            beg=begin_inclusive,
            end=end_exclusive
        )
        res = self.db_cur.execute(sqlcmd)
        time_series = []
        for row in res:
            time_series.append((row[0], row[1]))
        return time_series


class EHS(ehs.Application):

    def __init__(self):
        ehs.Application.__init__(self)
        self.configuration_schemas = [ehs.HEADER_CONF, ehs.SERVER_CONF, ADAPTER_CONF]
        self.adapters: Dict[str, DataSourceAdapter_pb2_grpc.DataSourceAdapterStub] = None
        self.scheduler = None

    def start(self):
        self.adapters = {}
        for adapter_config in self.configuration['adapters']:
            proxy = get_adapter_proxy(self.logging_dir, adapter_config, self.configuration)
            self.adapters[adapter_config['client']['name']] = proxy
        ehs_grpc_interface = EHSGRPCInterface(self)


        # set the defaults for the scheduler
        self.db = Database(self.logging_dir)
        self.ensure_tables()

        #self.db_path = os.path.join(self.data_dir, 'jobs.sqlite')
        #db_url = ''.join(['sqlite:///', self.db_path])
        jobstores = {
            #'default': SQLAlchemyJobStore(url=db_url)
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }

        # initialize the scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores, executors=executors, job_defaults=job_defaults)
        
        # uncomment the following line for starting without scheduler
        self.init_scheduling_rules()

        # channel_ref = {'adapter': 'XmlRpcAdapter', 'variable': 'CurrentTime'}
        # t = time.time_ns()
        # self.save_channel_value(channel_ref, t)

        self.server = GRPCServer(self, ehs_grpc_interface)
        self.server.start_up()

    def dummy_action(self):
        pass

    def save_data(self, event):
        current_job_name = event.job_id
        t = time.time_ns()
        for job_name in self.configuration['jobs']:
            if job_name == current_job_name:
                i = 0
                for channel_ref in self.configuration['jobs'][job_name]['channels']:
                    self.save_channel_value(channel_ref, t)

    def save_channel_value(self, channel_ref, t):
        channel_type = self.channel_type(channel_ref)
        proxy = self.adapters[channel_ref['adapter']]
        request = DataSourceAdapter_pb2.ReadRequest(address=channel_ref['variable'])
        channel_value = None
        v = proxy.read(request)

        if channel_type == 'bool':
            channel_value = v.value.bool_value
        elif channel_type == 'int64':
            channel_value = v.value.int64_value
        elif channel_type == 'double':
            channel_value = v.value.double_value
        elif channel_type == 'string':
            channel_value = v.value.string_value
        else:
            logging.error(f"Bad type '{channel_type}' requested. Search in EHS configuration for this type.")
        self.db.save(channel_ref, t, channel_value)

    def ensure_tables(self):
        for adapter in self.configuration['adapters']:
            adapter_name = adapter['client']['name']
            for variable in adapter['client']['variables']:
                variable_name = variable['name']
                variable_type = variable['type']
                table_name = self.db.channel_table_name({'adapter': adapter_name, 'variable': variable_name})
                self.db.create_table(table_name, variable_type)

    def channel_type(self, channel_ref):
        """channel_ref is a combination of adapter and varible definition as specified in ehs/configuration.yaml"""
        print(channel_ref)
        for adapter in self.configuration['adapters']:
            # print(f"x={}, y={}")
            if adapter['client']['name'] == channel_ref['adapter']:
                for variable in adapter['client']['variables']:
                    if variable['name'] == channel_ref['variable']:
                        return variable['type']
        return None

    def init_scheduling_rules(self):
        logging.getLogger('apscheduler').setLevel(logging.CRITICAL)
        if 'jobs' in self.configuration:
            for job_name in self.configuration['jobs']:
                job = self.configuration['jobs'][job_name]
                if job['type'] == 'interval':
                    seconds = int(job['seconds'])
                    self.scheduler.add_job(self.dummy_action, 'interval', seconds=seconds, id=job_name)
        self.scheduler.add_listener(self.save_data, apscheduler.events.EVENT_JOB_EXECUTED)
        self.scheduler.start()

    def stop(self):
        # stop the server
        self.server.shut_down()
        # disconnect from all adapters

    def run(self):
        try:
            while True:
                try:
                    self.show_start_message()
                    self.start()
                    # now start the scheduler
                    while True:
                        print("hi")
                        time.sleep(3)
                except Exception as e:
                    logging.error(e)
                    time.sleep(RETRY_TIME)
        except KeyboardInterrupt:
            self.show_stop_message()
            self.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ehs = EHS()
    if ehs.configure():
        ehs.run()
