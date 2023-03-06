# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import Commons_pb2 as Commons__pb2
from . import DataSourceAdapter_pb2 as DataSourceAdapter__pb2


class DataSourceAdapterStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ping = channel.unary_unary(
                '/eu.ifak.ehs.DataSourceAdapter/ping',
                request_serializer=Commons__pb2.PingRequest.SerializeToString,
                response_deserializer=Commons__pb2.PingResponse.FromString,
                )
        self.read = channel.unary_unary(
                '/eu.ifak.ehs.DataSourceAdapter/read',
                request_serializer=DataSourceAdapter__pb2.ReadRequest.SerializeToString,
                response_deserializer=DataSourceAdapter__pb2.ReadResponse.FromString,
                )
        self.write = channel.unary_unary(
                '/eu.ifak.ehs.DataSourceAdapter/write',
                request_serializer=DataSourceAdapter__pb2.WriteRequest.SerializeToString,
                response_deserializer=DataSourceAdapter__pb2.WriteResponse.FromString,
                )
        self.get_configuration = channel.unary_unary(
                '/eu.ifak.ehs.DataSourceAdapter/get_configuration',
                request_serializer=Commons__pb2.GetConfigurationRequest.SerializeToString,
                response_deserializer=Commons__pb2.GetConfigurationResponse.FromString,
                )


class DataSourceAdapterServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ping(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def read(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def write(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_configuration(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DataSourceAdapterServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ping': grpc.unary_unary_rpc_method_handler(
                    servicer.ping,
                    request_deserializer=Commons__pb2.PingRequest.FromString,
                    response_serializer=Commons__pb2.PingResponse.SerializeToString,
            ),
            'read': grpc.unary_unary_rpc_method_handler(
                    servicer.read,
                    request_deserializer=DataSourceAdapter__pb2.ReadRequest.FromString,
                    response_serializer=DataSourceAdapter__pb2.ReadResponse.SerializeToString,
            ),
            'write': grpc.unary_unary_rpc_method_handler(
                    servicer.write,
                    request_deserializer=DataSourceAdapter__pb2.WriteRequest.FromString,
                    response_serializer=DataSourceAdapter__pb2.WriteResponse.SerializeToString,
            ),
            'get_configuration': grpc.unary_unary_rpc_method_handler(
                    servicer.get_configuration,
                    request_deserializer=Commons__pb2.GetConfigurationRequest.FromString,
                    response_serializer=Commons__pb2.GetConfigurationResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'eu.ifak.ehs.DataSourceAdapter', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class DataSourceAdapter(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ping(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/eu.ifak.ehs.DataSourceAdapter/ping',
            Commons__pb2.PingRequest.SerializeToString,
            Commons__pb2.PingResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def read(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/eu.ifak.ehs.DataSourceAdapter/read',
            DataSourceAdapter__pb2.ReadRequest.SerializeToString,
            DataSourceAdapter__pb2.ReadResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def write(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/eu.ifak.ehs.DataSourceAdapter/write',
            DataSourceAdapter__pb2.WriteRequest.SerializeToString,
            DataSourceAdapter__pb2.WriteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def get_configuration(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/eu.ifak.ehs.DataSourceAdapter/get_configuration',
            Commons__pb2.GetConfigurationRequest.SerializeToString,
            Commons__pb2.GetConfigurationResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)