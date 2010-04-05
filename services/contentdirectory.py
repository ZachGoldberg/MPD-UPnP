from gi.repository import GObject, GUPnPAV
from mpdobjects.playlist import MPDPlaylist
import time, library

def browse_action(service, action):
    itemid = action.get_value('ObjectID', GObject.TYPE_INT)
    LIBRARY = library.get_library()

    while not getattr(LIBRARY, "ever_updated", ""):
        print "Library never updated.  Waiting for update to finish..."
        time.sleep(1)
    
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
