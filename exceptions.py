class NoSubjectCalander(Exception):
    def __init__(self, message):
        self.message = message


class ItemNotFound(Exception):
    def __init__(self, message):
        self.message = message


class ClassIdNotFound(Exception):
    def __init__(self, message):
        self.message = message
