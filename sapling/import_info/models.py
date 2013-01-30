from django.db import models

class ProtoAttribute(object):
    """
    Attribute that is being imported, not necessarily in its final form.
    """
    def __init__(self, name):
        self.name = name
        self.type = None
        self.values = {}

    def get_type(self):
        return self.type

    def set_type(self, type):
        self.type = type

    def add_value_for_page(self, page, value):
        self.values[page] = value

    def get_count(self):
        return len(self.values)
    count = property(get_count)


