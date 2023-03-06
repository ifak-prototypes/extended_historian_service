
from arrowhead_client import constants
from arrowhead_client.service import ServiceInterface
from arrowhead import ArrowheadCloud

cloud = ArrowheadCloud(
    system_name='sysop',
    address='127.0.0.1',
    port=1337,
    keyfile='certificates/crypto/sysop.key',
    certfile='certificates/crypto/sysop.crt',
    cafile='certificates/crypto/sysop.ca'
)

cloud.restart_core_services()

consumer = cloud.add_system(
    name='quickstart-consumer',
    address='127.0.0.1',
    port=7656
)

provider = cloud.add_system(
    name='quickstart-provider',
    address='127.0.0.1',
    port=7655,
    public_key='MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnX9Nff38wNj/n/UxktII'
               '/qYiy/z6dZshdnfnjShs+PflQ76LOVQY3vZ/oSCEs9/oRBifoMbCNuMitwCksVHA'
               'vG4hYhzhr7Tk2c4sS3doAAtriH7YpYj14nbLrvYxrPSd8FFnoLPYTfiEfexyCdl7'
               'KoTvh4eIyGiM8ZQeCdb2GygrnmNEaPJRm3ZrM58jKnTRUDJDmqMONd33Kfzwdqzp'
               'vymLLtnKq/eaL6ujkSMyrJdXDFAFnoKMZuP8t2/DONnnNCQSwZDm/4wtzQDskaI0'
               'ds2W0e3wpLC4K3oZQaycTt6eSu/lq7u6WsY0060+ujYlNTm8Zqh2COYWNkIx9K6K'
               'PQIDAQAB',
)

cloud.system('quickstart-provider').add_service(
    service_definition='hello-arrowhead',
    service_uri='hello',
    interface=ServiceInterface('HTTP', 'SECURE', 'JSON'),
    access_policy=constants.AccessPolicy.TOKEN
)
cloud.system('quickstart-provider').add_service(
    service_definition='echo',
    service_uri='echo',
    interface=ServiceInterface('HTTP', 'SECURE', 'JSON'),
    access_policy=constants.AccessPolicy.CERTIFICATE
)
cloud.system('quickstart-provider').add_service(
    service_definition='read',
    service_uri='read',
    interface=ServiceInterface('HTTP', 'SECURE', 'JSON'),
    access_policy=constants.AccessPolicy.CERTIFICATE
)
cloud.system('quickstart-provider').add_service(
    service_definition='write',
    service_uri='write',
    interface=ServiceInterface('HTTP', 'SECURE', 'JSON'),
    access_policy=constants.AccessPolicy.CERTIFICATE
)


cloud.route(provider, 'hello-arrowhead', consumer)
cloud.route(provider, 'echo', consumer)
cloud.route(provider, 'read', consumer)
cloud.route(provider, 'write', consumer)

print('Local cloud setup finished!')
input('Press <ENTER> to complete the procedure.')
