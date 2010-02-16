from mpdobjects.mpdobject import MPDObject

class MPDPlaylist(MPDObject):
    def __init__(self, name, songs):
        self.name = name
        self.songs = songs

    def writeself(self, writer):
        container = writer.add_container()
        container.set_title(self.name)
        container.set_child_count(len(self.songs))
        container.set_id(str(self.get_id()))

    def writeall(self, writer):
        for song in self.songs:
            song.writeself(writer)
