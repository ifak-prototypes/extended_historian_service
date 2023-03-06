#!/usr/bin/env bash

# This script generates certificates for the EHS and Adapters.
# They are used in scope of the gRPC SSL/TLS encryption.
#
# Preconditions:
#  - installed cfssl toolkit, see https://cfssl.org/ and https://github.com/cloudflare/cfssl


abs () {
    # returns the absolute path by a given relative path
    echo "$(cd $1; pwd)"
}

create_ca_cert () {
    ca_dir=$(abs $1)/

    pushd $ca_dir
    rm -f *.pem
    rm -f *.crt
    cfssl gencert -initca ca-csr.json | cfssljson -bare ca
    popd
}

create_server_cert () {
    ca_dir=$(abs $1)/
    server_dir=$(abs $2)/
    
    pushd $server_dir
    rm -f *.pem
    rm -f *.crt
    cfssl gencert -ca="${ca_dir}ca.pem" -ca-key="${ca_dir}ca-key.pem" -config="${ca_dir}ca-config.json" -hostname='192.168.178.85,127.0.0.1,localhost' "${server_dir}server-csr.json" | cfssljson -bare server
    popd
}

create_client_cert () {
    ca_dir=$(abs $1)/
    client_dir=$(abs $2)/
    
    pushd $client_dir
    rm -f *.pem
    rm -f *.crt
    cfssl gencert -ca="${ca_dir}ca.pem" -ca-key="${ca_dir}ca-key.pem" -config="${ca_dir}ca-config.json" "${client_dir}client-csr.json" | cfssljson -bare client
    popd
}


create_ca_cert ./test/ca/cert/grpc/

create_server_cert ./test/ca/cert/grpc/ ./test/ehs/configuration_01/cert/grpc/
create_server_cert ./test/ca/cert/grpc/ ./test/adapter/arrowhead_01/cert/grpc/
create_server_cert ./test/ca/cert/grpc/ ./test/adapter/xmlrpc_01/cert/grpc/

create_client_cert ./test/ca/cert/grpc/ ./test/application/app_01/cert/grpc/
