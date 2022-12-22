from otp.clientagent.ClientAgent import ClientAgent


services = {
    'clientagent': ClientAgent
}


def createService(serviceName, serviceConfig):
    serviceCtor = services[serviceName]
    serviceCtor.createFromConfig(serviceConfig)
