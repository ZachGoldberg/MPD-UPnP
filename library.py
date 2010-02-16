from mpdobjects.playlist import MPDPlaylist
from mpdobjects.song import MPDSong

class MPDLibrary(object):
    def __init__(self, client, credentials):
        self.client = client
        self.creds = credentials

    def clear(self):
        self.playlists = []
        self.songs = []
        self.songs_by_file = {}
        self.id_inc = 0
        self.items_by_id = {}


    def connect(self):
        self.client.connect(**self.creds)
        
    def disconnect(self):
        self.client.disconnect()

    def refresh(self):
        self.connect()

        self.clear()
    
        print "Downloading MPD Playlists / Library"
        for p in self.client.listplaylists():
            print "Loading %s" % p['playlist']
            songs = self.client.listplaylistinfo(p['playlist'])
            mpdsongs = []
            for song in songs:
                if not song['file'] in self.songs_by_file:
                    self.songs_by_file[song['file']] =  MPDSong(song['file'], song.get('artist', 'Unknown'),
                                                                song.get('album', 'Unknown'), song.get('title', 'Unknown')
                                                                )
                                        
                    self.register_song(self.songs_by_file[song['file']])
                    
                mpdsongs.append(self.songs_by_file[song['file']])
                
            playlist = MPDPlaylist(p['playlist'], mpdsongs)
            self.register_playlist(playlist)

        cursongs = self.client.playlistinfo()
        self.disconnect()

        curmpdsongs = []
        for song in cursongs:
            if not song['file'] in self.songs_by_file:
                self.songs_by_file[song['file']] =  MPDSong(song['file'], song.get('artist', 'Unknown'),
                                                            song.get('album', 'Unknown'), song.get('title', 'Unknown'))
                self.register_song(self.songs_by_file[song['file']])
            curmpdsongs.append(self.songs_by_file[song['file']])
        
        self.register_playlist(MPDPlaylist('Current Playlist', curmpdsongs))
        self.register_playlist(MPDPlaylist('All Songs', self.songs))
        self.playlists.reverse()

    def get_by_id(self, id):
        return self.items_by_id.get(id, None)
                     
        
    def next_id(self):
        self.id_inc += 1
        return self.id_inc

    def register_item(self, obj, list):
        obj.set_id(self.next_id())
        self.items_by_id[obj.get_id()] = obj
        list.append(obj)
        
    def register_playlist(self, playlist):
        self.register_item(playlist, self.playlists)
        
    def register_song(self, song):
        self.register_item(song, self.songs)
        
