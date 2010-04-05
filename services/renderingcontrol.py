from gi.repository import GObject
from client import get_client

def get_volume(service, action):
    MPDCLIENT = get_client()
    print "Get Volume"
    
    MPDCLIENT.connect()

    status = MPDCLIENT.status()
    action.set_value("ChannelVolume", str(status.get('volume', '0')))
    MPDCLIENT.disconnect()

    getattr(action, "return")()

    
def set_volume(service, action):
    MPDCLIENT = get_client()
    volume = action.get_value("DesiredVolume", GObject.TYPE_INT)
    print "Set Volume", volume
    
    MPDCLIENT.connect()
    MPDCLIENT.setvol(volume)
    MPDCLIENT.disconnect()

    getattr(action, "return")()

    
