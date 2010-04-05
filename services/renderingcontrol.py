from client import get_client

def get_volume(service, action):
    MPDCLIENT = get_client()
    print "Get Volume"
    
    MPDCLIENT.connect()

    status = MPDCLIENT.status()
    action.set_value("ChannelVolume", str(status.get('volume', '0')))
    MPDCLIENT.disconnect()

    getattr(action, "return")()

    
