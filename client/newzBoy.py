import xml.dom.minidom, time, re, select, nntp, socket
import os, sys, string, ConfigParser, codecs, utils, time
import downloader, verifier, extractor, bookmarks, nntplib

# check nzb files
nfiles = []
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if utils.fileExists(arg):
            if arg.split(".")[-1].lower() == "nzb":
                nfiles.append({"path": arg, "isBookmark": False})
                if arg[0] == "/":
                    # unix style
                    print "added [%s] to the queue" % string.split(arg, "/")[-1]
                else:
                    # win32 style
                    print "added [%s] to the queue" % string.split(arg, "\\")[-1]
            else:
                print "not an nzb file: %s" % arg

# change the cwd
# NOTE: with py2exe use sys.executable instead of __file__
approot = os.path.dirname(__file__)
if approot != '':
    os.chdir(approot)

# load settings
cfg = ConfigParser.ConfigParser()
cfg.read("settings.conf")

# load gui
guiInfo = {}
if cfg.get("extras","useGui") == "true":
    try:
        import downloadgui
        gui = downloadgui.DownloadInfoThread(guiInfo)
        gui.start()
    except:
    	print "error: Couldn't load gui. Did you install wxPython?"
    	pass

# check default directorys
try:
    if not os.path.exists("./cache/"):
        os.mkdir("./cache/")
    if not os.path.exists("./watch/"):
        os.mkdir("./watch/")
    if not os.path.exists("./tools/"):
        os.mkdir("./tools/")
except Exception, e:
    print e
    sys.exit(-1)

# start the process
while 1:
    if len(nfiles) > 0:
        if len(nfiles) == 1:
            print "1 job in the queue"
        else:
            print "%d jobs in the queue" % len(nfiles)

        # vars
        downloadPath = ""
        conns = []
        
        # build connections
        print "\nconnecting to usenet..."
        # TODO: add support for more then 1 server
        for x in range(0,cfg.getint("conn","connections")):
            try:
                conn = nntp.News(cfg.get("conn","host"), cfg.getint("conn","port"), cfg.get("conn","username"), cfg.get("conn","password"))
            except socket.gaierror:
                print "error connecting to %s on port %d..." % (cfg.get("conn","host"), cfg.getint("conn","port"))
                sys.exit(-1)
            except nntplib.NNTPPermanentError, msg:
                print "error connecting to %s on port %d..." % (cfg.get("conn","host"), cfg.getint("conn","port"))
                print "\n%s\n" % msg
                sys.exit(-1)
            conns.append(conn)
        if len(conns) == 1:
            print "connected to %s (1 connection)..." % cfg.get("conn","host")
        else:
            print "connected to %s (%d connections)..." % (cfg.get("conn","host"), len(conns))
        
        counter = 0
        for nfile in nfiles:
            counter += 1
            folderName = None
            if string.find(nfile["path"], "\\") != -1:
                folderName = string.split(nfile["path"], "\\")[-1][:-4]
            elif string.find(nfile["path"], "/") != -1:
                folderName = string.split(nfile["path"], "/")[-1][:-4]
            else:
                folderName = nfile["path"]
            if nfile["isBookmark"]:
                folderName = folderName.replace("_$bookmark-","")
            print "\nprocessing job %d of %d - [%s]\n" % (counter, len(nfiles), folderName)
            # update gui stats
            guiInfo["tjobs"] = len(nfiles)
            guiInfo["jnum"] = counter
            # parse nbz
            files = []
            pars = []
            nzb = xml.dom.minidom.parse(nfile["path"])
            for file in nzb.getElementsByTagName("file"):
                # solves xml encoding error
                codecs.register_error('xml', codecs.xmlcharrefreplace_errors)
                fsubject = codecs.getencoder('ascii')(file.attributes["subject"].value, 'xml')[0]
                fsegments = []
                fsize = 0
                for segments in file.getElementsByTagName("segments"):
                    for segment in segments.getElementsByTagName("segment"):
                        fsize += int(codecs.getencoder('ascii')(segment.attributes["bytes"].value, 'xml')[0])
                        fsegments.append(segment.childNodes[0].nodeValue.encode('ascii'))
                # is it a par file w/ blocks?
                p = re.compile("vol[0-9]+\+([0-9]+)")
                result = p.search(fsubject)
                if result:
                    blocks = int(result.groups()[0])
                    pars.append({"subject":fsubject, "segments":fsegments, "downloaded":False, "decoded":False, "size" : fsize, "blocks":blocks})
                # no its not
                else:
                    files.append({"subject":fsubject, "segments":fsegments, "downloaded":False, "decoded":False, "size" : fsize})

            # create subfolder?
            if cfg.get("misc","subfolders") == "true":
                # rename subfolder?
                if cfg.get("misc","renameFolders") == "true":
                    # TODO: msgidlist_
                    # it has an ugly name?
                    if re.compile("msgid_[0-9]+_*").search(folderName):
                        # lets fix it
                        folderName = string.join(folderName.split("_")[2:], " ")
                # check for trailing slash
                downloadPath = cfg.get("misc","downloadPath") + folderName + "/"
            else:
                # save downloads to the root download folder
                downloadPath = cfg.get("misc","downloadPath")

            # make the folder if its not already there
            try:
                if not os.path.exists(downloadPath):
                    os.mkdir(downloadPath)
            except:
                pass

            # download
            dret = None
            if len(files) == 0:
                downloader.download(conns, downloadPath, pars, False, guiInfo)
            else:
                dret = downloader.download(conns, downloadPath, files, False, guiInfo)
        
            # verify / extract
            vret = None
            if not len(files) == 0:
                if cfg.get("automation","verify") == "true":
                    vret = verifier.verify(conns, downloadPath, pars)
                # TODO: extract download
                if cfg.get("automation","extract") == "true":
                    if vret != -1:
                        extractor.extract(downloadPath)
                        
            # generate nfo file
            if dret:
                vresult = ""
                if vret == None or vret == 2:
                    vresult = "???"
                elif vret == 1:
                    vresult = "Passed"
                elif vret == 3:
                    vresult = "Repaired"
                else:
                    vresult = "Failed"

                f = open(downloadPath + "newzBoy.nfo", "w")
                f.write(utils.nfo(folderName, dret["size"], dret["files"], dret["speed"], dret["time"],vresult))
                f.close()

            # remove nzb file
            if vret == 1 or vret == 3:
                if (cfg.get("extras","autoloadPath") in nfile["path"]) or cfg.get("misc","removeNZB") == "true":
                    os.remove(nfile["path"])
            else:
                if (cfg.get("extras","autoloadPath") in nfile["path"]):
                    os.rename(nfile["path"],nfile["path"]+".x")

        # TODO: handle unfinished session here, delete it
        # clean up
        nfiles = []
        # close connections
        for x in range(0,len(conns)):
            conns[x].quit()
    elif cfg.get("extras","fetchBookmarks") == "true" or cfg.get("extras","autoload") == "true":
        print "\nstanding by..."
        lastBookmarksCheck = -1
        while len(nfiles) == 0:
            # get bookmarks
            if cfg.get("extras","fetchBookmarks") == "true" and cfg.get("extras","autoload") == "true":
                try:
                    b = bookmarks.Bookmarks(cfg.get("extras","newzbinUsername"), cfg.get("extras","newzbinPassword"))
                    posts = b.getBookmarks()
                    if len(posts) > 0:
                        print "fetching bookmarks..."
                        for p in posts:
                            print "  \"%s\"" % p["name"]
                            f = open(cfg.get("extras","autoloadPath") + "_$bookmark-" + p["name"] + ".nzb", "w")
                            f.write(b.getBookmark(p["id"]))
                            f.close()
                            b.removeBookmark(p["id"])
                except IOError:
                    print "error connecting to newzbin..."
                    time.sleep(10)
                except RuntimeError:
                    print "could not login to newzbin (incorrect username/password)..."
                    time.sleep(10)

            # check autoload folder, add to queue
            if cfg.get("extras","autoload") == "true":
                files = utils.listFilesByLastUpdated(cfg.get("extras","autoloadPath"),"nzb")
                if len(files) > 0:
                    if len(files) == 1:
                        print "found 1 nzb file..."
                    else:
                        print "found %s nzb files..." % (len(files))
                    for file in files:
                        if "_$bookmark-" in file:
                            nfiles.append({"path": cfg.get("extras","autoloadPath") + file, "isBookmark": True})
                        else:
                            nfiles.append({"path": cfg.get("extras","autoloadPath") + file, "isBookmark": False})
                    break
            # wait 10 minutes
            time.sleep(60*10)
    else:
        print "\nexiting (nothing to do)..."
        sys.exit(1)
