import arrowhead_client.client.implementations
import ehs.arrowhead
import logging
import math
import random
import time


class MyDevice(ehs.arrowhead.ArrowheadDevice):
    def __init__(self) -> None:
        ehs.arrowhead.ArrowheadDevice.__init__(self)
        self.values = {
            "CurrentTime":       ["int"  , int(time.time())],
            "Workload_AHDev123": ["float", 3.1415926],
            "AHMyBool":          ["bool" , False],
            "AHMyStr":           ["str"  , "I am an Arrowhead device."],
        }

    def update(self):
        self.values['CurrentTime'][1] = int(time.time())
        self.values['Workload_AHDev123'][1] = (4 * math.cos(time.time()/10)) + random.uniform(-0.8, 0.8)

    def run(self):

        server_config = self.configuration['server']

        provider = arrowhead_client.client.implementations.SyncClient.create(
                system_name=server_config['system_name'],
                address=server_config['address'],
                port=server_config['port'],
                keyfile=server_config['server_key'],
                certfile=server_config['server_cert'],
                cafile=server_config['ca_cert'],
        )


        @provider.provided_service(
                service_definition='hello-arrowhead',
                service_uri='hello',
                protocol='HTTP',
                method='GET',
                payload_format='JSON',
                access_policy='TOKEN', )
        def hello_arrowhead(request):
            return {"msg": "Hello, Arrowhead!"}


        @provider.provided_service(
                service_definition='echo',
                service_uri='echo',
                protocol='HTTP',
                method='PUT',
                payload_format='JSON',
                access_policy='CERTIFICATE', )
        def echo(request):
            body = request.read_json()
            return body

        @provider.provided_service(
                service_definition='read',
                service_uri='read',
                protocol='HTTP',
                method='PUT',
                payload_format='JSON',
                access_policy='CERTIFICATE', )
        def read(request):
            body = request.read_json()
            print(body)
            self.update()
            address = body["address"]
            if address in self.values:
                body["type"] = self.values[address][0]
                body["value"] = self.values[address][1]
            else:
                body["value"] = "undefined"
                body["type"] = "str"
            return body

        @provider.provided_service(
                service_definition='write',
                service_uri='write',
                protocol='HTTP',
                method='PUT',
                payload_format='JSON',
                access_policy='CERTIFICATE', )
        def write(request):
            body = request.read_json()
            print(body)
            #body['time'] = time.time()
            retval = {}
            retval['status'] = 'OK'
            return retval

        provider.run_forever()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    device = MyDevice()
    if device.configure():
        print(device.configuration)
        device.run()
    else:
        input("Press any key ...")
