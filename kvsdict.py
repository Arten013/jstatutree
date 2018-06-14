import plyvel
import pickle
from collections import UserDict
import os
class KVSDict(object):
    DEFAULT_DBNAME = "kvsdict.ldb"
    ENCODING = "utf8"
    PREFIX = "example-"

    def __init__(self, path, create_if_missing=True, _called_by_classmethod=False, *args, **kwargs):
        if _called_by_classmethod:
            return self
        self.path = path
        self.db = plyvel.DB(self.path, create_if_missing=create_if_missing)

    @property
    def prefix(self):
        if "_prefix" not in self.__dict__ or self._prefix is None:
            self._prefix = self.__class__.PREFIX
            if isinstance(self.prefix, str):
                self.prefix = self.prefix.encode(self.ENCODING)
        return self._prefix

    @prefix.setter
    def prefix(self, val):
        if isinstance(val, bytes):
            self._prefix = val
        elif isinstance(val, str):
            self._prefix = val.encode(self.ENCODING)
        elif val is None:
            self._prefix = None
        else:
            raise Exception("{} is invalid value for prefix".format(val))

    @classmethod
    def init_as_prefixed_db(cls, db, prefix=None, *args, **kwargs):
        instance = cls(path="", _called_by_classmethod=True, *args, **kwargs)
        instance.prefix = prefix
        instance.db = db.prefixed_db(instance.prefix)
        return instance

    @property
    def path(self):
        if "_path" not in self.__dict__:
            self._path = None
        return self._path

    @path.setter
    def path(self, path):
        if os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            path = os.path.join(path, self.DEFAULT_DBNAME)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.splitext(path)[1] == "":
                path += ".ldb"
        self._path = path

    def _encode_key(self, key):
        return key.encode(self.ENCODING)

    def _decode_key(self, key):
        return key.decode(self.ENCODING)

    def write_batch_mapping(self, mapping, *args, **kwargs):
        with self.write_batch(*args, **kwargs) as wb:
            for k, v in mapping.items():
                wb[k] = v

    def write_batch(self, *args, **kwargs): 
        return BatchWriter(self, *args, **kwargs)

    def __setitem__(self, key, val):
        self.db.put(self._encode_key(key), pickle.dumps(val))

    def __getitem__(self, key):
        return pickle.loads(self.db.get(self._encode_key(key)))

    def __delitem__(self, key):
        self.db.delete(self._encode_key(key))

    def items(self):
        return ((self._decode_key(k), pickle.loads(v)) for k, v in self.db.iterator(include_key=True, include_value=True))

    def keys(self):
        return (self._decode_key(k) for k in self.db.iterator(include_key=True, include_value=False))

    def values(self):
        return (pickle.loads(v) for v in self.db.iterator(include_key=False, include_value=True))

    def __len__(self):
        l = 0
        for _ in self.keys():
            l += 1
        return l

    def is_prefixed_db(self):
        return isinstance(self.db, plyvel._plyvel.PrefixedDB)

    def close(self):
        if "db" in self.__dict__ and not self.is_prefixed_db():
            self.db.close()

    def __del__(self):
        self.close()

class BatchWriter(object):
    def __init__(self, kvsdict, *args, **kwargs):
        self.wb = kvsdict.db.write_batch(*args, **kwargs)
        self._encode_key = kvsdict._encode_key
        self.ENCODING = kvsdict.ENCODING

    def __setitem__(self, key, val):
        self.wb.put(self._encode_key(key), pickle.dumps(val))

    def __delitem__(self, key):
        self.wb.delete(self._encode_key(key))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            return False
        self.write()
        return True

    def write(self):
        self.wb.write()

class KVSPrefixDict(KVSDict):
    def __init__(self, db, prefix=None, *args, **kwargs):
        self.prefix = prefix
        self.db = db.prefixed_db(self.prefix)

class KVSValuesCounter(KVSPrefixDict):
    PREFIX = "Count-"
    def __init__(self, kvsdict, prefix=None, *args, **kwargs):
        super().__init__(db=kvsdict.db, prefix=prefix, *args, **kwargs)
        with kvsdict.db.snapshot() as snapshot:
            with kvsdict.write_batch(transaction=True) as wb:
                for k, v in snapshot.values():
                    v = wb[v]
                    wb[v] = 0 if v is None else v + 1


