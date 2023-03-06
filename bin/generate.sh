#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
API="../src/ehs/api"

cd $SCRIPTPATH

python -m grpc_tools.protoc -I$API --python_out=$API --grpc_python_out=$API $API/DataSourceAdapter.proto
sed 's/^import DataSourceAdapter_pb2 as DataSourceAdapter__pb2/from . import DataSourceAdapter_pb2 as DataSourceAdapter__pb2/g' -i $API/DataSourceAdapter_pb2_grpc.py

python -m grpc_tools.protoc -I$API --python_out=$API --grpc_python_out=$API $API/ExtendedHistorianService.proto
sed 's/^import ExtendedHistorianService_pb2 as ExtendedHistorianService__pb2/from . import ExtendedHistorianService_pb2 as ExtendedHistorianService__pb2/g' -i $API/ExtendedHistorianService_pb2_grpc.py

python -m grpc_tools.protoc -I$API --python_out=$API --grpc_python_out=$API $API/Commons.proto
sed 's/^import Commons_pb2 as Commons__pb2/from . import Commons_pb2 as Commons__pb2/g' -i $API/Commons_pb2_grpc.py
sed 's/^import Commons_pb2 as Commons__pb2/from . import Commons_pb2 as Commons__pb2/g' -i $API/ExtendedHistorianService_pb2.py
sed 's/^import Commons_pb2 as Commons__pb2/from . import Commons_pb2 as Commons__pb2/g' -i $API/ExtendedHistorianService_pb2_grpc.py
sed 's/^import Commons_pb2 as Commons__pb2/from . import Commons_pb2 as Commons__pb2/g' -i $API/DataSourceAdapter_pb2.py
sed 's/^import Commons_pb2 as Commons__pb2/from . import Commons_pb2 as Commons__pb2/g' -i $API/DataSourceAdapter_pb2_grpc.py
