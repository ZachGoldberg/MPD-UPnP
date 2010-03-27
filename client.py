import mpd, time

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
            self.client.connect(**self.creds)
            self.connected = True

        try:
            self.run_cmd(self.client.status, [], {})
        except:
            self.disconnect()
            return self.connect()

    def disconnect(self):
        self.num_connects -= 1
        if self.connected and self.num_connects == 0:
            self.client.disconnect()
            self.connected = False

    def run_cmd(self, func, args, kwargs):
        self.queue.append((func, args, kwargs))
        while self.queue[0] != (func, args, kwargs):
            time.sleep(0.1)
                
        try:
            val = func(*args, **kwargs)
        except:
            import traceback
            traceback.print_exc()
            self.disconnect()
            self.connect()

        self.queue.remove(self.queue[0])
        return val


    def __getattr__(self, attr):
        try:
            retval = getattr(self.client, attr)
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

        return lambda *args, **kwargs: self.run_cmd(retval, args, kwargs)
