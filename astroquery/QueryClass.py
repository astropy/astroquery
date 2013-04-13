
class TimeoutError(Exception):
    pass

class InvalidQueryError(Exception):
    pass

class QueryClass(object):

    def login(self, *args):
        pass

    def __call__(self):
        raise Exception("All classes must override this!")

class DelayedQueryClass(QueryClass):

    def check_for_update(self, time_min=5):
        """
        Check the "result" URL for existence or the presence of useful data
        """
        pass
