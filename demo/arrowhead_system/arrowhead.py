import subprocess
import requests
import time
from typing import List

from arrowhead_client import constants
from arrowhead_client.dto import DTOMixin
from arrowhead_client.rules import OrchestrationRule
from arrowhead_client.service import ServiceInterface
from arrowhead_client.system import ArrowheadSystem
from arrowhead_client.service import Service
from arrowhead_client.client.core_system_defaults import default_config
from arrowhead_client.client.core_service_forms.client import ServiceRegistrationForm
from arrowhead_client.client.implementations import SyncClient


class AHSystem:

    def __init__(self, cloud, name, address, port, public_key=''):
        self.cloud = cloud
        self.services = {}

        ahs = ArrowheadSystem(
            system_name=name,
            address=address,
            port=port,
            authentication_info=public_key
        )

        data = self.cloud.setup_client.consume_service('mgmt_register_system', json=ahs.dto()).read_json()

        self.sys = ArrowheadSystem.from_dto(data)
        self.id = data['id']

    
    def add_service(
        self,
        service_definition: str = None,
        service_uri: str = None,
        interface: ServiceInterface = ServiceInterface('HTTP', 'SECURE', 'JSON'),
        access_policy: str = constants.AccessPolicy.CERTIFICATE
        ):

        service = AHService(
            ahsystem=self,
            cloud=self.cloud,
            service_definition=service_definition,
            service_uri=service_uri,
            interface=interface,
            access_policy=access_policy
        )
        self.services[service_definition] = service

    def service(self, service_uri):
        return self.services[service_uri]


class AHService:
    def __init__(
        self,
        cloud,
        ahsystem: AHSystem,
        service_definition: str,
        service_uri: str = None,
        interface: ServiceInterface = ServiceInterface('HTTP', 'SECURE', 'JSON'),
        access_policy: str = constants.AccessPolicy.CERTIFICATE
        ):

        service_registration_form = ServiceRegistrationForm.make(
            Service(service_definition, service_uri, interface, access_policy),
            ahsystem.sys
        )

        res = cloud.setup_client.consume_service(
            'mgmt_register_service',
            json=service_registration_form.dto()
        ).read_json()

        self.id = res['serviceDefinition']['id']


class ArrowheadCloud:

    def __init__(self,
        system_name: str = 'sysop',
        address: str = '127.0.0.1',
        port: int = 1337,
        keyfile: str = 'certificates/crypto/sysop.key',
        certfile: str = 'certificates/crypto/sysop.crt',
        cafile: str = 'certificates/crypto/sysop.ca'
        ):

        self.system_name = system_name
        self.address = address
        self.port = port
        self.keyfile = keyfile
        self.certfile = certfile
        self.cafile = cafile

        self.setup_client = SyncClient.create(
            system_name=self.system_name,
            address=self.address,
            port=self.port,
            keyfile=self.keyfile,
            certfile=self.certfile,
            cafile=self.cafile
        )
        self.systems = {}  # system_name -> AHSystem

    def system(self, name):
        return self.systems[name]

    def restart_core_services(self):
        """Starts or restarts the mandatory Arrowhead Core Services
        """
        subprocess.run(['docker-compose', 'down'])
        subprocess.run(['docker', 'volume', 'rm', 'mysql.quickstart'])
        subprocess.run(['docker', 'volume', 'create', '--name', 'mysql.quickstart'])
        subprocess.run(['docker-compose', 'up', '-d'])
        self.wait_until_coreservices_are_running()
        self.orchestrate_core_services()

    def wait_until_coreservices_are_running(self):
        """Waits for the Registry, Orchestrator and Authorization systems to be up and running.
        """
        with requests.Session() as session:
            session.verify = self.cafile
            session.cert = (self.certfile, self.keyfile)
            is_online = [False, False, False]
            print('Waiting for core systems to get online (might take a few minutes...)')
            while True:
                try:
                    if not is_online[0]:
                        session.get('https://127.0.0.1:8443/serviceregistry/echo')
                        is_online[0] = True
                        print('Service Registry is online')
                    if not is_online[1]:
                        session.get('https://127.0.0.1:8441/orchestrator/echo')
                        is_online[1] = True
                        print('Orchestrator is online')
                    if not is_online[2]:
                        session.get('https://127.0.0.1:8445/authorization/echo')
                        is_online[2] = True
                        print('Authorization is online')
                except Exception:
                    time.sleep(2)
                else:
                    print('All core systems are online\n')
                    break

    def orchestrate_core_services(self):
        """Orchestrates all core services.
        """
        def orchestrate(
            default_service_configuration: str,
            service_definition: str,
            http_method: str,
            service_uri: str,
            service_interface: ServiceInterface = ServiceInterface('HTTP', 'SECURE', 'JSON')
            ):
            
            self.setup_client.orchestration_rules.store(
                OrchestrationRule(
                    Service(service_definition, service_uri, service_interface),
                    ArrowheadSystem(**default_config[default_service_configuration]),
                    http_method,
                )
            )
        print('Setting up local cloud')
        orchestrate('service_registry',  'mgmt_register_service',    'POST',  'serviceregistry/mgmt')
        orchestrate('service_registry',  'mgmt_get_systems',         'GET',   'serviceregistry/mgmt/systems')
        orchestrate('service_registry',  'mgmt_register_system',     'POST',  'serviceregistry/mgmt/systems')
        orchestrate('orchestrator',      'mgmt_orchestration_store', 'POST',  'orchestrator/mgmt/store')
        orchestrate('authorization',     'mgmt_authorization_store', 'POST',  'authorization/mgmt/intracloud')
        self.setup_client.setup()

    def add_system(self, name, address, port, public_key=''):
        system = AHSystem(self, name, address, port, public_key)
        self.systems[name] = system
        return system

    def route(self, provider: AHSystem, service_definition: str, consumer: AHSystem, service_interface_name: str = 'HTTP-SECURE-JSON'):

        class OrchestrationMgmtStoreForm(DTOMixin):
            service_definition_name: str
            consumer_system_id: str
            provider_system: ArrowheadSystem
            service_interface_name: str
            priority: int = 1

        class AuthorizationIntracloudForm(DTOMixin):
            consumer_id: int
            provider_ids: List[int]
            interface_ids: List[int]
            service_definition_ids: List[int]

        orchestration_form = OrchestrationMgmtStoreForm(
            service_definition_name=service_definition,
            consumer_system_id=consumer.id,
            provider_system=provider.sys,
            service_interface_name=service_interface_name,
        )
        self.setup_client.consume_service(
            'mgmt_orchestration_store',
            json=orchestration_form.dto()
        )

        # TODO: since providers and consumers are given as lists, we could assume in the function signature 'providers' and 'service_definitions' ...
        authorization_form = AuthorizationIntracloudForm(
            consumer_id=consumer.id,
            provider_ids=[provider.id],
            interface_ids=[1],
            service_definition_ids=[provider.service(service_definition).id],
        )
        self.setup_client.consume_service(
            'mgmt_authorization_store',
            json=authorization_form.dto()
        )
