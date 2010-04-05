from mpdobjects.playlist import MPDPlaylist
from mpdobjects.song import MPDSong
import threading, time, sys

class MPDLibrary(object):
    def __init__(self, client, credentials, server, music_path):
        self.client = client
        self.creds = credentials
        self.webserver = server
        self.music_path = music_path
        self.connected = False
        self.num_connects = 0
        self.ever_updated = False
        self.clear()

        self.updater = threading.Thread(target=self.update_library,
                                        name="Library Updater")
        
    def clear(self):
        self.playlists = []
        self.songs = []
        self.songs_by_file = {}
        self.id_inc = 0
        self.items_by_id = {}
        self.items_by_file = {}
    def connect(self):
        self.client.connect()
        
    def disconnect(self):
        self.client.disconnect()

    def song_from_dict(self, song):
        return  MPDSong(song['file'], song.get('artist', 'Unknown'),
                        song.get('album', 'Unknown'),
                        song.get('title', 'Unknown')
                        )


    def start_updating(self):
        self.stop_running = False
        if not self.updater.isAlive():
            self.updater.start()

    def stop_updating(self):
        self.stop_running = True

    def update_library(self):
        time.sleep(1)
        while True:           
            self.refresh()
            
            time_slept = 0
            while time_slept < (5 * 60):
                if self.stop_running:
                    return
                
                time.sleep(1)
                time_slept += 1

    def refresh(self):
        self.connect()
        self.clear()

        sys.stdout.write("Downloading MPD Playlists / Library... ")
        sys.stdout.flush()
        playlists = self.client.listplaylists() or []
        pos = 1
        last_length = 0
        for p in playlists:
            # Silly stuff to make terminal output pretty                
            output = "%s/%s" % (pos, len(playlists))
            sys.stdout.write("\b" * last_length + output)
            sys.stdout.flush()
            last_length = len(output)
            pos += 1
            
            
            songs = self.client.listplaylistinfo(p['playlist'])
            mpdsongs = []
            for song in songs:
                if not song['file'] in self.songs_by_file:
                    self.songs_by_file[song['file']] = self.song_from_dict(song)
                    self.register_song(self.songs_by_file[song['file']])
                    
                mpdsongs.append(self.songs_by_file[song['file']])
                
            playlist = MPDPlaylist(p['playlist'], mpdsongs)
            self.register_playlist(playlist)

        cursongs = self.client.playlistinfo() or []
        self.disconnect()

        curmpdsongs = []
        for song in cursongs:
            if not song['file'] in self.songs_by_file:
                self.songs_by_file[song['file']] = self.song_from_dict(song)
                self.register_song(self.songs_by_file[song['file']])
            curmpdsongs.append(self.songs_by_file[song['file']])
        
        self.register_playlist(MPDPlaylist('Current Playlist', curmpdsongs))
        self.register_playlist(MPDPlaylist('All Songs', self.songs))
        self.playlists.reverse()
        self.ever_updated = True
        
        print "\nDone"

    def get_by_id(self, id):
        return self.items_by_id.get(id, None)
                     
        
    def next_id(self):
        self.id_inc += 1
        return self.id_inc

    def register_item(self, obj, list):
        obj.set_id(self.next_id())
        self.items_by_id[obj.get_id()] = obj
        self.items_by_file[obj.get_file()] = obj
        list.append(obj)
        return obj.get_id()
        
    def register_playlist(self, playlist):
        return self.register_item(playlist, self.playlists)
        
    def register_song(self, song):
        self.register_item(song, self.songs)

        local_file = self.music_path + "/" + song.file
        remote_loc = "/file/%s" % song.id
        
        self.webserver.host_path(local_file, remote_loc)

        song.url = "http://%s:%s/file/%s" % (
            self.webserver.get_host_ip(),
            self.webserver.get_port(),
            song.id)
        
        song.set_resource(song.url)
        return song.id
        
