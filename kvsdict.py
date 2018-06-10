import plyvel
import pickle
from collections import UserDict
class KVSDict(object):
    DEFAULT_DBNAME = "kvsdict.ldb"
    ENCODING = "utf8"
    PREFIX = b"example-"

    def __init__(self, path, create_if_missing=True _called_by_classmethod=False, *args, **kwargs):
        if _called_by_classmethod:
            return self
        self.path = path
        self.db = plyvel.DB(self.path, create_if_missing=create_if_missing)

    @classmethod
    def init_as_prefixed_db(cls, db, prefix=None, *args, **kwargs):
        instance = cls(path="", _called_by_classmethod=True, *args, **kwargs)
        self.PREFIX = self.__class__.PREFIX if prefix is None else prefix
        instance.db = db.prefixed_db(self.PREFIX)
        return instance

    @property
    def path(self):
        if "_path" not in self.__dict__:
            self._path = None
        return self._path

    @path.setter
    def path(self, path):
        if os.path.is_dir(path):
            os.path.makedirs(path, exist_ok=True)
            path = os.path.join(path, self.DEFAULT_DBNAME)
        else:
            os.path.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.splitext(path)[1] == "":
                path += ".ldb"
        self._path = path

    def _encode_key(self, key):
        return key.encode(self.ENCODING)

    def _decode_key(self, key):
        return key.decode(self.ENCODING)

    def __setitem__(self, key, val):
        self.db.put(self._encode_key(key), pickle.dump(val))

    def __getitem__(self, key):
        return pickle.load(self.db.get(self._encode_key(key)))

    def __delitem__(self, key):
        self.db.delete(self._encode_key(key))

    def items(self):
        return (self._decode_key(k), pickle.load(v) for k, v in self.db.iterator(include_key=True, include_value=True))

    def values(self):
        return (self._decode_key(k) for k in self.db.iterator(include_key=True, include_value=False))

    def keys(self):
        return (pickle.load(v) for v in self.db.iterator(include_key=False, include_value=True))

    def __len__(self):
        return len(self.keys())

class KVSPrefixDict(KVSDict):
    def __init__(self, _called_by_classmethod=False, *args, **kwargs):
        assert not _called_by_classmethod, "{} has to be prefixed-db".format(self.__class__.__name__)
