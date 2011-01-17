import decoder, select, utils, time, os

def download(conns, download_dir, files, inBackground = False, guiInfo = None):
    # some stats
    leech_start = time.time()
    leech_raw_bytes = 0
    leech_files = 0
    leech_speeds = []
    totalFiles  = len(files)

    # download + decode files
    fileNumber = 0
    for file in files:
        fileNumber += 1
        # TODO: skip file if already downloaded
        #if file["downloaded"] == True:
        #    continue

        if not inBackground:
            print "  %s" % file["subject"]
            print "  + downloading"

        # prepare connections
        active = []
        ready = []
        for conn in conns:
            conn.setblocking(0)
            ready.append(conn.fd())
    
        # stats
        file_start = time.time()
        file_speeds = []
        file_raw_bytes = 0

        # vars
        skipfile = False
        segments = file["segments"]
        decodeList = segments[:]
        lastSegment = ''

        if not inBackground:
            # update gui stats
            guiInfo["subject"]        = file["subject"]
            guiInfo["tsegments"]      = len(file["segments"])
            guiInfo["segments"]       = file["segments"]
            guiInfo["tfiles"]         = totalFiles
            guiInfo["fnum"]           = fileNumber
            guiInfo["file_raw_bytes"] = 0
            guiInfo["file_start"]     = file_start
            guiInfo["file_size"]      = file["size"]
            guiInfo["transfering"]    = True
            guiInfo["hide"]           = False

        while 1:
            if ready:
                # theres stuff left to do
                if segments and not skipfile:
                    segment = segments.pop()
                    fd = ready.pop()
                    active.append(fd)
                    nwrap = utils.fdToConn(fd, conns)
                    nwrap.body("<%s>" % segment)
                    lastSegment = segment
                # lets get out of here
                elif not active:
                    break
            # lets dance
            read = select.select(active, [], [], 0)[0]
            if read:
                for fd in read:
                    nwrap = utils.fdToConn(fd, conns)
                    # update stats
                    read_bytes, done = nwrap.recv_chunk()
                    file_raw_bytes += read_bytes
                    leech_raw_bytes += read_bytes
                    if not inBackground:
                        # update gui
                        guiInfo["file_raw_bytes"] = file_raw_bytes
                    if done:
                        speed = file_raw_bytes / 1024.0 / (time.time() - file_start)
                        file_speeds.append(speed)
                        # write to disk
                        fn = nwrap.resp.split(" ")[2][1:-1]
                        f = open("cache/%s" % fn,"wb")
                        for line in nwrap.lines:
                            f.write(line + "\r\n")
                        f.close()
                        nwrap.reset()
                        active.remove(fd)
                        ready.append(fd)
                        break
                    else:
                        # check for error
                        if len(nwrap.lines) == 1:
                            if nwrap.lines[0][:3] in ('423', '430'):
                                if not inBackground:
                                    print "      * error: file segment missing, file is corrupt"
                                nwrap.reset()
                                active.remove(fd)
                                ready.append(fd)
                                break
                            elif not nwrap.lines[0].startswith('2'):
                                print "      * error: %s" % nwrap.lines[0]
                                nwrap.reset()
                                active.remove(fd)
                                ready.append(fd)
                                skipfile = True
                                break
            # this lessens the cpu load
            time.sleep(0.01)
            # are we skipping this file?
            if skipfile:
                break

        if not inBackground:
            # clear gui info
            guiInfo["transfering"] = False

        # skip!
        if skipfile:
            continue

        # spit out some nice info
        dur = time.time() - file_start
        # TODO: reconnect to servers if lag in speed
        #print file_speeds
        speed = 0
        try:
            speed = int(sum(file_speeds)/len(file_speeds))
        except:
            pass
        size = utils.nsize(file_raw_bytes)
        if not inBackground:
            # no files transfered?
            if speed == 0:
                print "      * error: percentage of missing segments is 100%, skipping file"
            print "      * transferred %s in %s at %dKB/s" % (size, utils.ntime(dur), speed)

        # no files transfered?
        if speed == 0:
            continue
        # global stats
        leech_files += 1
        leech_speeds.append(speed)
    
        # clean up
        for conn in conns:
            conn.setblocking(1)

        # decode
        if not inBackground:
            print "  + decoding"
        dec_start = time.time()
        decoder.decode(decodeList, download_dir)
        dur = time.time() - dec_start
        if not inBackground:
            print "      * decoded %s in %s" % (size, utils.ntime(dur))

        # TODO: after we decode, pickle out to unfinished.tmp the remaining files
        file["downloaded"] = True
        file["decoded"] = True

    if not inBackground:
        # update gui info
        guiInfo["hide"] = True

    # summary of session
    dur = time.time() - leech_start
    speed = 0
    try:
        speed = sum(leech_speeds)/len(leech_speeds)
    except:
        pass
    size = utils.nsize(leech_raw_bytes)
    if not inBackground:
        if leech_files == 1:
            print "\n  received %s file (%s) in %s at %dKB/s" % (leech_files, size, utils.ntime(dur), int(speed))
        else:
            print "\n  received %s files (a total of %s) in %s at %dKB/s" % (leech_files, size, utils.ntime(dur), int(speed))

    # remove leftover junk
    segfiles = os.listdir("./cache/")
    for segfile in segfiles:
        try:
            os.remove("./cache/%s" % segfile)
        except:
            pass
        
    return { "files" : leech_files, "size" : size, "time" : utils.ntime(dur), "speed" : int(speed) }
