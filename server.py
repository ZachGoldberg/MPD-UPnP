from gi.repository import GUPnP, GObject, GLib
import mpd

CON_ID = None
MPDCLIENT = None

print GUPnP.ServiceAction

GObject.threads_init()

def setup_server():

    ctx = GUPnP.Context(interface="eth0")

    ctx.host_path("device.xml", "/device.xml")
    ctx.host_path("AVTransport2.xml", "/AVTransport2.xml")

    desc = "device.xml"
    desc_loc = "./"

    rd = GUPnP.RootDevice.new(ctx, desc, desc_loc)
    rd.set_available(True)

    return rd

def setup_mpd():
    global CON_ID, MPDCLIENT
    HOST = 'localhost'
    PORT = '6600'
    CON_ID = {'host':HOST, 'port':PORT}

    MPDCLIENT = mpd.MPDClient()

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

service = rd.get_service("urn:schemas-upnp-org:service:AVTransport:1")
service.connect("action-invoked::Play", mpd_func_generator("Play"))
service.connect("action-invoked::Pause", mpd_func_generator("Pause"))
service.connect("action-invoked::Stop", mpd_func_generator("Stop"))
service.connect("action-invoked::Next", mpd_func_generator("Next"))
service.connect("action-invoked::Previous", mpd_func_generator("Previous"))

print "Awaiting commands..."
GObject.MainLoop().run()

