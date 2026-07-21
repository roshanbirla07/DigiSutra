
from abc import ABCMeta, abstractmethod, abstractproperty
from v1.routers.routes import v1

class AbstractVersion(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_blueprint(self):
        raise NotImplementedError
    
    @abstractproperty   
    def VERSION(self):
        raise NotImplementedError

class V1Version(AbstractVersion):
    VERSION = 'v1'

    def get_blueprint(self):
        return v1