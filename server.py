from gi.repository import GUPnP, GUPnPAV, GObject, GLib
from library import MPDLibrary
from mpdobjects.playlist import MPDPlaylist
from mpdobjects.song import MPDSong
import mpd

CON_ID = None
MPDCLIENT = None
LIBRARY = None
GObject.threads_init()

def setup_server():

    ctx = GUPnP.Context(interface="eth0")

    ctx.host_path("xml/device.xml", "/device.xml")
    ctx.host_path("xml/AVTransport2.xml", "/AVTransport2.xml")
    ctx.host_path("xml/ContentDirectory.xml", "/ContentDirectory.xml")

    desc = "device.xml"
    desc_loc = "./xml/"

    rd = GUPnP.RootDevice.new(ctx, desc, desc_loc)
    rd.set_available(True)

    return rd

def setup_mpd():
    global CON_ID, MPDCLIENT, LIBRARY
    HOST = 'localhost'
    PORT = '6600'
    CON_ID = {'host':HOST, 'port':PORT}

    MPDCLIENT = mpd.MPDClient()

    LIBRARY = MPDLibrary(MPDCLIENT, CON_ID)
    LIBRARY.refresh()
    
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
     MPDCLIENT.connect(**CON_ID)
     getattr(MPDCLIENT, function_name.lower())(*args)
     MPDCLIENT.disconnect()
     getattr(action, "return")()     
     
  return wrapper

def set_mpd_uri(service, action):
    uri = action.get_value_type("CurrentURI", GObject.TYPE_STRING)
    itemid = int(uri.replace("mpd://", ""))
    
    song = LIBRARY.get_by_id(itemid)

    if not isinstance(song, MPDSong):
        action.return_error()
        return
    
    MPDCLIENT.connect(**CON_ID)
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

def browse_action(service, action):
    global LIBRARY
    itemid = action.get_value_type('ObjectID', GObject.TYPE_INT)
    
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
service.connect("action-invoked::SetAVTransportURI", set_mpd_uri)

directory = rd.get_service("urn:schemas-upnp-org:service:ContentDirectory:1")
directory.connect("action-invoked::Browse", browse_action)

print "Awaiting commands..."
GObject.MainLoop().run()

