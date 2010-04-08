from gi.repository import GObject
from client import get_client

def get_volume(service, action):
    MPDCLIENT = get_client()
    
    MPDCLIENT.connect()

    status = MPDCLIENT.status()
    action.set_value("ChannelVolume", str(status.get('volume', '0')))
    MPDCLIENT.disconnect()

    print "Get Volume %s" % status.get('volume', 0)

    getattr(action, "return")()

    
def set_volume(service, action):
    MPDCLIENT = get_client()
    volume = action.get_value("DesiredVolume", GObject.TYPE_INT)
    print "Set Volume", volume

    try:    
      MPDCLIENT.connect()
      MPDCLIENT.setvol(volume)
      MPDCLIENT.disconnect()
    except:
      MPDCLIENT.disconnect()
      action.return_error(32, "Couldn't set volume (possible that MPD is paused?)")
      return

    getattr(action, "return")()

    
