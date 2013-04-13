
class TimeoutError(Exception):
    pass

class InvalidQueryError(Exception):
    pass

class QueryClass(object):

    def login(self, *args):
        pass

    def __call__(self):
        raise Exception("All classes must override this!")
