class Law(object):
    PARENT_CANDIDATES = ()

    @classmethod
    def is_root(cls):
        return True

class LawBody(object):
    PARENT_CANDIDATES = (Law,)

    @classmethod
    def is_root(cls):
        return False

class MainProvision(object):
    PARENT_CANDIDATES = (LawBody,)

    @classmethod
    def is_root(cls):
        return False

class Part(object):
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"    
    @classmethod
    def is_root(cls):
        return False