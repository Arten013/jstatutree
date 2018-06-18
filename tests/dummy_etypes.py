import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatutree.etypes import get_etypes_core

def get_etypes():
    return get_etypes_core(globals())

class Law(object):
    PARENT_CANDIDATES = ()

    @classmethod
    def is_root(cls):
        return True
    @property
    def etype(self):
        return self.__class__


class LawBody(object):
    PARENT_CANDIDATES = (Law,)

    @classmethod
    def is_root(cls):
        return False
    @property
    def etype(self):
        return self.__class__


class MainProvision(object):
    PARENT_CANDIDATES = (LawBody,)

    @classmethod
    def is_root(cls):
        return False
    @property
    def etype(self):
        return self.__class__


class Part(object):
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"    
    @classmethod
    def is_root(cls):
        return False
    @property
    def etype(self):
        return self.__class__
