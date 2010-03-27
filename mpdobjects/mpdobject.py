class MPDObject(object):
    def __init__(self):
        self.id = None

    def set_id(self, id):
        self.id = id
        
    def get_id(self):
        return self.id

    def get_file(self):
        return getattr(self, "file", None)
