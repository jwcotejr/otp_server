from otp.clientagent.ClientAgent import ClientAgent
from otp.database.DatabaseServer import DatabaseServer


services = {
    'clientagent': ClientAgent,
    'database': DatabaseServer
}


def createService(serviceName, serviceConfig):
    serviceCtor = services[serviceName]
    serviceCtor.createFromConfig(serviceConfig)
