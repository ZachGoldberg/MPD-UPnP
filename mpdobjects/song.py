from mpdobjects.mpdobject import MPDObject

class MPDSong(MPDObject):
    def __init__(self, file, artist, album, title):
        self.file = file
        self.artist = artist
        self.album = album
        self.title = title
        
    def writeself(self, writer):
        item = writer.add_item()
        item.set_title(self.title)
        item.set_artist(self.artist)
        item.set_album(self.album)        
        item.set_id(str(self.get_id()))

        res = item.add_resource()
        res.set_uri("mpd://%s" % self.get_id())
