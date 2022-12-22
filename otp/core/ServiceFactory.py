from otp.messagedirector.MessageDirector import MessageDirector


services = {
    'messagedirector': MessageDirector
}


def createService(serviceName, serviceConfig):
    serviceCtor = services[serviceName]
    serviceCtor.createFromConfig(serviceConfig)
