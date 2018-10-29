try:
    import cPickle as pickle
except ImportError:
    import pickle


class PickleSerializer:
    @staticmethod
    def dumps(obj):
        return pickle.dumps(obj, protocol=1)

    @staticmethod
    def loads(data):
        return pickle.loads(data)


class RawSerializer:
    @staticmethod
    def dumps(obj):
        return obj

    @staticmethod
    def loads(data):
        return data
