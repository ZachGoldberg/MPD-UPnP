from gi.repository import GUPnP, GUPnPAV, GObject, GLib
import mpd

CON_ID = None
MPDCLIENT = None

GObject.threads_init()

PLAYLISTS = []

def setup_server():

    ctx = GUPnP.Context(interface="eth0")

    ctx.host_path("device.xml", "/device.xml")
    ctx.host_path("AVTransport2.xml", "/AVTransport2.xml")
    ctx.host_path("ContentDirectory.xml", "/ContentDirectory.xml")

    desc = "device.xml"
    desc_loc = "./"

    rd = GUPnP.RootDevice.new(ctx, desc, desc_loc)
    rd.set_available(True)

    return rd

def setup_mpd():
    global CON_ID, MPDCLIENT, PLAYLISTS
    HOST = 'localhost'
    PORT = '6600'
    CON_ID = {'host':HOST, 'port':PORT}

    MPDCLIENT = mpd.MPDClient()
    MPDCLIENT.connect(**CON_ID)
    
    print "Downloading MPD Playlists / Library"
    PLAYLISTS = MPDCLIENT.listplaylists()
    
    MPDCLIENT.disconnect()

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
    print action.get_value_type("CurrentURI", GObject.TYPE_STRING)
    import pdb
    pdb.set_trace()


def browse_action(service, action):
    w = GUPnPAV.GUPnPDIDLLiteWriter.new("English")

    container = w.add_container()
    container.set_title("All Songs")

    container = w.add_container()
    container.set_title("Current Playlist")
    
    for p in PLAYLISTS:
        container = w.add_container()
        container.set_title(p["playlist"])
     
    
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

