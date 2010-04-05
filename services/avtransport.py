import os, re
from gi.repository import GObject, GUPnPAV
from mpdobjects.song import MPDSong
from client import get_client
from library import get_library

def mpd_func_generator(function_name, args=None):
  if not args:
    args=[]

  def wrapper(service, action):
      MPDCLIENT = get_client()
      print function_name
      MPDCLIENT.connect()
      getattr(MPDCLIENT, function_name.lower())(*args)
      MPDCLIENT.disconnect()
      getattr(action, "return")()

  return wrapper

def set_mpd_uri(service, action, uri):
    MPDCLIENT = get_client()
    LIBRARY = get_library()

    print "Playing %s" % uri
    match = re.search("/file\/(.*)$", uri)
    if not match:
        action.return_error(0, "Invalid URI")
        
    itemid = int(match.groups()[0])
    
    song = LIBRARY.get_by_id(itemid)

    if not isinstance(song, MPDSong):
        action.return_error()
        return
    
    MPDCLIENT.connect()
    songdata = MPDCLIENT.playlistfind('file', song.file)
    
    if songdata:        
        # If the song is in the current playlist move to it and play it
        MPDCLIENT.seek(songdata[0]['pos'], 0)
    else:
        # Else add it to the playlist then play it
        MPDCLIENT.add(song.file)
        songdata = MPDCLIENT.playlistfind('file', song.file)
        if not songdata:
            action.return_error()
            return
        MPDCLIENT.seek(songdata[0]['pos'], 0)

    MPDCLIENT.disconnect()
    getattr(action, "return")()


def set_http_uri(service, action, uri):
    """
    This is a bit tricker.  We need to download the file from the local network
    (hopefully its quick), add the file to MPD (the file has to be 100% downloaded first)
    then add the file to the playlist and seek to it.

    1) Download file
    2) Add file to DB
    3) Load file to local library
    4) Generate an MPD uri and then call set_mpd_uri
    """
    LIBRARY = get_library()
    MPDCLIENT = get_client()
    from server import get_context, MUSIC_PATH
    CONTEXT = get_context()

    path = uri.replace("http:/", "")
    filename = os.path.basename(path)

    if not "." in filename:
        filename += ".mp3" # assume mp3 for now
    
    os.system("wget %s -O %s/%s" % (uri, MUSIC_PATH, filename))
    
    LIBRARY.connect()
    MPDCLIENT.update(filename)
    
    songdata = MPDCLIENT.find('file', filename)
    if not songdata:
        action.return_error(0, "Couldn't add file to MPD database")
        return
    
    song_id = LIBRARY.register_song(LIBRARY.song_from_dict(songdata[0]))

    LIBRARY.disconnect()
    set_mpd_uri(service, action, "http://%s:%s/file/%s" % (
        CONTEXT.get_host_ip(),
        CONTEXT.get_port(),
        song_id)
                )
    
def handle_uri_change(service, action):
    from server import get_context
    CONTEXT = get_context()
    uri = action.get_value("CurrentURI", GObject.TYPE_STRING)
    if not uri:
      return None
    
    print uri, CONTEXT.get_host_ip(), CONTEXT.get_port()
    if CONTEXT.get_host_ip() in uri and str(CONTEXT.get_port()) in uri:
        return set_mpd_uri(service, action, uri)
    else:
        return set_http_uri(service, action, uri)


def int_to_time(timevalue):
    timevalue = int(timevalue)
    return "%.2d:%.2d:%.2d" % (int(timevalue / 3600),
                               int(timevalue / 60),
                               timevalue % 60)

def time_to_int(time):
    (hour, min, sec) = time.split(":")
    return (int(hour) * 3600) + (int(min) * 60) + int(sec)
    
        
def handle_position_request(service, action):
    LIBRARY = get_library()
    MPDCLIENT = get_client()

    print "Position"

    MPDCLIENT.connect()
    status = MPDCLIENT.status()
    songinfo = MPDCLIENT.playlistid(status['songid'])
    MPDCLIENT.disconnect()
    
    w = GUPnPAV.GUPnPDIDLLiteWriter.new("English")   
    song = LIBRARY.songs_by_file.get(songinfo[0]['file'], None)

    song_id = "0"
    if song:
      song.writeself(w)
      song_id = str(song.id)
    
    action.set_values(["Track", "TrackMetaData", "TrackURI"],
                      [song_id, w.get_string(), getattr(song, "url", "")])

    action.set_value("TrackDuration",
                     int_to_time(status.get("time", "0:0").split(":")[1]))
    
    curtime = int_to_time(status.get("time", "0:0").split(":")[0])
    action.set_value("RelTime", curtime)
    action.set_value("AbsTime", curtime)
    
    getattr(action, "return")()

def handle_state_request(service, action):
    MPDCLIENT = get_client()
    LIBRARY = get_library()
    print "Status"
    
    MPDCLIENT.connect()
    status = MPDCLIENT.status()
    MPDCLIENT.disconnect()

    if status and status['state'] == "pause":
        state = "PAUSED_PLAYBACK"
    elif status and status['state'] == "play":
        state = "PLAYING"
    else:
        state = "STOPPED"

    action.set_value("CurrentTransportState", state)
    action.set_value("CurrentTransportStatus", "OK")
    action.set_value("CurrentSpeed", "1")
    
    getattr(action, "return")()


def handle_seek_request(service, action):
    MPDCLIENT = get_client()

    seek_time = action.get_value('Target', GObject.TYPE_STRING)
    MPDCLIENT.connect()
    status = MPDCLIENT.status()
    print "id: %s" % status["songid"], seek_time
    MPDCLIENT.seek(status["songid"], time_to_int(seek_time))
    MPDCLIENT.disconnect()

    getattr(action, "return")()
