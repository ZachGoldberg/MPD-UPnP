from gi.repository import GUPnP, GUPnPAV, GObject, GLib
from library import MPDLibrary
from mpdobjects.playlist import MPDPlaylist
from mpdobjects.song import MPDSong
from client import MPDClient

import mpd, os, re, atexit, sys, time

CON_ID = None
MPDCLIENT = None
LIBRARY = None
GObject.threads_init()
HOST = 'localhost'
PORT = '6600'
MUSIC_PATH = "/mnt/nixsys/Music/all"
CONTEXT = None


def kill_library():
    LIBRARY.stop_updating()
    
atexit.register(kill_library)

def setup_server():
    global CONTEXT
    
    ctx = GUPnP.Context(interface="eth0")

    ctx.host_path("xml/device.xml", "device.xml")
    ctx.host_path("xml/AVTransport2.xml", "AVTransport2.xml")
    ctx.host_path("xml/ContentDirectory.xml", "ContentDirectory.xml")

    ctx.host_path("/mnt/nixsys/Music/all/Seether/Seether featuring Amy Lee - Broken.mp3", "/file/test.mp3")

    desc = "device.xml"
    desc_loc = "./xml/"

    rd = GUPnP.RootDevice.new(ctx, desc, desc_loc)
    rd.set_available(True)

    CONTEXT = ctx
    return rd

def setup_mpd():
    global CON_ID, MPDCLIENT, LIBRARY, HOST, PORT
    CON_ID = {'host':HOST, 'port':PORT}

    MPDCLIENT = MPDClient(CON_ID)

    LIBRARY = MPDLibrary(MPDCLIENT, CON_ID, CONTEXT, MUSIC_PATH)
    LIBRARY.start_updating()
    
    print "Scheduling MPD Database refresh every 60 seconds..."
    

rd = setup_server()
print "UPnP MediaRenderer Service Exported"

setup_mpd()
print "MPD Client Setup"


def mpd_func_generator(function_name, args=None):
  if not args:
    args=[]

  def wrapper(service, action):
     print function_name
     MPDCLIENT.connect()
     getattr(MPDCLIENT, function_name.lower())(*args)
     MPDCLIENT.disconnect()
     getattr(action, "return")()

  return wrapper

def set_mpd_uri(service, action, uri):
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
    set_mpd_uri(service, action, "http://%s:%s/file/%s" % (CONTEXT.get_host_ip(),
                                                           CONTEXT.get_port(),
                                                           song_id)
                )
    
def handle_uri_change(service, action):
    uri = action.get_value_type("CurrentURI", GObject.TYPE_STRING)
    if CONTEXT.get_host_ip() in uri and str(CONTEXT.get_port()) in uri:
        return set_mpd_uri(service, action, uri)
    else:
        return set_http_uri(service, action, uri)

def handle_state_request(service, action):
    print "Status"
    
    MPDCLIENT.connect()
    status = MPDCLIENT.status()
    MPDCLIENT.disconnect()

    if status['state'] == "pause":
        state = "PAUSED_PLAYBACK"
    elif status['state'] == "play":
        state = "PLAYING"
    
    action.set_value("CurrentTransportState", state)
    action.set_value("CurrentTransportStatus", "OK")
    action.set_value("CurrentSpeed", "1")
    
    getattr(action, "return")()
    
def browse_action(service, action):
    global LIBRARY
    itemid = action.get_value_type('ObjectID', GObject.TYPE_INT)


    while not LIBRARY.ever_updated:
        print "Library never updated.  Waiting for update to finish..."
        time.sleep(1)
    
    w = GUPnPAV.GUPnPDIDLLiteWriter.new("English")
    if itemid == 0:        
        for playlist in LIBRARY.playlists:
            playlist.writeself(w)
    else:
        obj = LIBRARY.get_by_id(itemid)
        if not isinstance(obj, MPDPlaylist):
            action.return_error()
            return
        obj.writeall(w)
    
    action.set_value("Result", w.get_string())
    action.set_value("NumberReturned", 1)
    action.set_value("TotalMatches", 1)
    action.set_value("UpdateID", "0")
    getattr(action, "return")()


service = rd.get_service("urn:schemas-upnp-org:service:AVTransport:1")
service.connect("action-invoked::Play", mpd_func_generator("Play"))
service.connect("action-invoked::Pause", mpd_func_generator("Pause"))
service.connect("action-invoked::Stop", mpd_func_generator("Stop"))
service.connect("action-invoked::Next", mpd_func_generator("Next"))
service.connect("action-invoked::Previous", mpd_func_generator("Previous"))
service.connect("action-invoked::SetAVTransportURI", handle_uri_change)
service.connect("action-invoked::GetTransportInfo", handle_state_request)

directory = rd.get_service("urn:schemas-upnp-org:service:ContentDirectory:1")
directory.connect("action-invoked::Browse", browse_action)

print "Awaiting commands..."
try:
    GObject.MainLoop().run()
except KeyboardInterrupt:    
    print "Done"
    sys.exit(0)
