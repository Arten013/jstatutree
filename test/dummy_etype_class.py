class Law(object):
    PARENT_CANDIDATES = ()

class LawBody(object):
    PARENT_CANDIDATES = (Law,)

class MainProvision(object):
    PARENT_CANDIDATES = (LawBody,)

class Part(object):
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"
