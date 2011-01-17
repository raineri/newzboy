import urllib, string, xml.dom.minidom, os, time, utils

class Bookmarks:
    """ This class wraps the newzbin.com bookmarks feature """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        lastw = 0
        if utils.fileExists("cookie.tmp"):
            lastw = time.time() - os.stat("cookie.tmp").st_mtime
        if not utils.fileExists("cookie.tmp") or lastw > 864000:
            self._getSessionID()
            self._login()
        else:
            f = open("cookie.tmp", "r")
            self.session = f.read()
            f.close()

    def _getSessionID(self):
        """ fetches a session id """
        req = urllib.FancyURLopener()
        f = req.open("http://www.newzbin.com/")
        self.session = f.info()['Set-Cookie'].split(';')[0]
        f.close()

    def _login(self):
        """ logs you in to newzbin.com """
        params = urllib.urlencode({ "username" : self.username, "password" : self.password })
        req = urllib.FancyURLopener()
        req.addheader("Cookie", "%s;" % self.session)
        f = req.open("http://www.newzbin.com/account/login/", params)
        data = f.read()
        f.close()
        if string.find(data,"Log Out") == -1:
            raise RuntimeError, "Could not login to newzbin.com"
        # write session to disk
        f = open("cookie.tmp", "w")
        f.write(self.session)
        f.close()

    def getBookmarks(self):
        """ returns a list of your bookmarked posts """
        req = urllib.FancyURLopener()
        req.addheader("Cookie", "%s;" % self.session)
        f = req.open("http://www.newzbin.com/account/favourites/?sort=fp_date")
        data = f.read()
        f.close()
        data = string.split(data, "\n")
        temp = []
        for line in data:
            if string.find(line, "<td><a href=") != -1:
                line = utils.htmlEncode(line)
                line = line.replace("&eacute;","e")
                bxml = xml.dom.minidom.parseString(line)
                name = bxml.childNodes[0].childNodes[0].childNodes[0].nodeValue.encode('ascii')
                name = name.replace("/"," ").replace("\\"," ").replace(":","").replace("<","").replace(">","").replace("|","")
                postID = int(bxml.childNodes[0].childNodes[0].attributes['href'].nodeValue.encode('ascii').split('/')[3])
                temp.append({"id" : postID, "name" : name})
        return temp

    def getBookmark(self, postID):
        """ gets the specified bookmarked post (nzb file) """
        params = urllib.urlencode({ str(postID) : "on", "msgid" : "Get+Message-IDs" })
        req = urllib.FancyURLopener()
        req.addheader("Cookie", "%s;" % self.session)
        f = req.open("http://www.newzbin.com/account/favourites/action/", params)
        data = f.read()
        f.close()
        return data
        
    def removeBookmark(self, postID):
        """ removes a post from your bookmarks """
        params = urllib.urlencode({ str(postID) : "on", "del" : "Remove" })
        req = urllib.FancyURLopener()
        req.addheader("Cookie", "%s;" % self.session)
        f = req.open("http://www.newzbin.com/account/favourites/action/", params)
        f.close()
