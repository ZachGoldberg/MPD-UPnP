import pygtk
pygtk.require('2.0')
from gi.repository import GUPnP
from library import MPDLibrary
from client import MPDClient
from services import *

import atexit, sys, library, client

CON_ID = None
GObject.threads_init()
HOST = 'localhost'
PORT = '6600'
MUSIC_PATH = "/mnt/nixsys/Music/all"
CONTEXT = None

def get_context():
    return CONTEXT

def kill_library():
    library.get_library().stop_updating()

def setup_server():
    global CONTEXT
    
    ctx = GUPnP.Context(interface="wlan0")

    ctx.host_path("xml/device.xml", "device.xml")
    ctx.host_path("xml/AVTransport2.xml", "AVTransport2.xml")
    ctx.host_path("xml/ContentDirectory.xml", "ContentDirectory.xml")
    ctx.host_path("xml/RenderingControl.xml", "RenderingControl2.xml")

    ctx.host_path("/mnt/nixsys/Music/all/Seether/Seether featuring Amy Lee - Broken.mp3", "/file/test.mp3")

    desc = "device.xml"
    desc_loc = "./xml/"

    rd = GUPnP.RootDevice.new(ctx, desc, desc_loc)
    rd.set_available(True)
    
    import server
    server.CONTEXT = ctx
    return rd

def setup_mpd():
    global CON_ID, MPDCLIENT, HOST, PORT
    CON_ID = {'host':HOST, 'port':PORT}

    client.MPDCLIENT = MPDClient(CON_ID)
    
    import server
    library.LIBRARY = MPDLibrary(client.get_client(),
                                 CON_ID, server.get_context(),
                                 MUSIC_PATH)

    library.LIBRARY.start_updating()
    
    print "Scheduling MPD Database refresh every 60 seconds..."
    
if __name__ == '__main__':
    rd = setup_server()
    print "UPnP MediaRenderer Service Exported"
    
    setup_mpd()
    print "MPD Client Setup"

    
    transport = rd.get_service("urn:schemas-upnp-org:service:AVTransport:1")
    transport.connect("action-invoked::Play", mpd_func_generator("Play"))
    transport.connect("action-invoked::Pause", mpd_func_generator("Pause"))
    transport.connect("action-invoked::Stop", mpd_func_generator("Stop"))
    transport.connect("action-invoked::Next", mpd_func_generator("Next"))
    transport.connect("action-invoked::Previous", 
                      mpd_func_generator("Previous"))
    transport.connect("action-invoked::SetAVTransportURI", handle_uri_change)
    transport.connect("action-invoked::GetTransportInfo", handle_state_request)
    transport.connect("action-invoked::GetPositionInfo",  
                      handle_position_request)
    transport.connect("action-invoked::Seek", handle_seek_request)
    
    directory = rd.get_service(
        "urn:schemas-upnp-org:service:ContentDirectory:1")
    directory.connect("action-invoked::Browse", browse_action)
    
    control = rd.get_service("urn:schemas-upnp-org:service:RenderingControl:1")
    control.connect("action-invoked::GetVolume", get_volume)
    control.connect("action-invoked::SetVolume", set_volume)

    
    atexit.register(kill_library)
    
    print "Awaiting commands..."
    try:
        GObject.MainLoop().run()
    except KeyboardInterrupt:    
        print "Done"
        sys.exit(0)
