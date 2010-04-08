import mpd, time

MPDCLIENT = None

def get_client():
    return MPDCLIENT

class MPDClient(object):

    def __init__(self, con_id):
        self.client = mpd.MPDClient()
        self.creds = con_id
        self.connected = False
        self.num_connects = 0
        self.queue = []

    def connect(self):
        self.num_connects += 1
        if not self.connected:
            try:
              self.client.connect(**self.creds)
            except:
	      return None
            self.connected = True

        self.run_cmd(self.client.status, [], {})

    def disconnect(self):
        self.num_connects -= 1
        if self.connected and self.num_connects == 0:
            self.client.disconnect()
            self.connected = False

    def run_cmd(self, func, args, kwargs):
        self.queue.append((func, args, kwargs))
        while self.queue[0] != (func, args, kwargs):
            time.sleep(0.1)

        val = None                
        try:
            val = func(*args, **kwargs)
        except ConnectionError:
            import traceback
            traceback.print_exc()
	    raise

        self.queue.remove(self.queue[0])
        return val


    def __getattr__(self, attr):
        try:
            retval = getattr(self.client, attr)
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

        return lambda *args, **kwargs: self.run_cmd(retval, args, kwargs)
