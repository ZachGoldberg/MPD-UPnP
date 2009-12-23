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


def on_play_action(service, action):
  print "Play"
  MPDCLIENT.connect(**CON_ID)
  MPDCLIENT.play()
  MPDCLIENT.disconnect()

def on_pause_action(service, action):
  print "Pause"
  MPDCLIENT.connect(**CON_ID)
  MPDCLIENT.pause()
  MPDCLIENT.disconnect()
  print action, action.__class__
  print dir(action)
#  print dir(service)
#  import pdb
#  pdb.set_trace()
#  getattr(action, "return")()
  
rd = setup_server()
print "UPnP MediaRenderer Service Exported"

setup_mpd()
print "MPD Client Setup"



service = rd.get_service("urn:schemas-upnp-org:service:AVTransport:1")
service.connect("action-invoked::Play", on_play_action)
service.connect("action-invoked::Pause", on_pause_action)

print "Awaiting commands..."
GObject.MainLoop().run()

