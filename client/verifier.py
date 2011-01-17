import utils, downloader, re, sys, os

def verify(conns, download_dir, pars):
    print "\n  verifying files...",
    # what type of check are we doing
    initialCheck = ""
    if len(utils.listFiles(download_dir, "par2")) > 0:
        initialCheck = ".par2"
    elif len(utils.listFiles(download_dir, "sfv")) > 0: # TODO: check sfv file internally
        initialCheck = ".sfv"
    elif len(pars) > 0:
        initialCheck = "none"
    if initialCheck != "":
        # we don't have any initial par/par2 files, but there are some in the list, lets download one
        if initialCheck == "none":
            downloader.download(conns, download_dir, [pars[0]], inBackground = True)
            # now recheck the download dir
            if len(utils.listFiles(download_dir, "par2")) > 0:
                initialCheck = ".par2"
        # error?
        if initialCheck == "none":
            print "error 5"
            return -1
        # we have an sfv file, but no more pars
        if initialCheck == ".sfv":
            # parse sfv file, check download
            print "sfv %s" % pars
        else:
            os.chdir("tools")
            sts, text = utils.run("par2 v \"%s*%s\"" % (download_dir, initialCheck))
            os.chdir("..")
            if sts == 0:
                if "repair is not required" in text:
                    print "ok"
                else:
                    print "error 1"
                    print text
                    return -1
            else:
                if "Repair is required" in text:
                    print "failed"
                    blocks = int(re.compile("You need ([0-9]+) more").search(text).groups()[0])
                    queue = []
                    qblocks = 0
                    # queue only what we need
                    for par in pars:
                        if qblocks < blocks:
                            qblocks += par["blocks"]
                            queue.append(par)
                        else:
                            break
                    if qblocks < blocks:
                        print "     - repair is impossible (access to %d out of %d blocks needed)" % (qblocks, blocks)
                        return -1
                    else:
                        if blocks == 1:
                            print "     - downloading 1 more recovery block...",
                        else:
                            print "     - downloading " + str(blocks) + " more recovery blocks...",
                        # download
                        downloader.download(conns, download_dir, queue, inBackground = True)
                        print "ok"
                        # repair
                        print "     - repairing...",
                        par2Files = utils.listFiles(download_dir, "par2")
                        os.chdir("tools")
                        sts, text = utils.run("par2 r \"%s%s\"" % (download_dir, par2Files[0]))
                        os.chdir("..")
                        if sts == 0:
                            print "ok"
                            return 3
                        else:
                            print "failed"
                            if " - missing" in text:
                                print "     - conflict, more then one par2 file (each of a different download)"
                                return -1
                            else:
                                print text
                            return -1
                else:
                    print "error 3"
                    print text
                    return -1
    else:
        print "error"
        print "     - no (par2, sfv) file found"
        return 2
    return 1
        
#def par2check(directory, capitals):
#    sts, text = utils.run("tools\\par2 v \"%s*%s\"" % (download_dir, initialCheck))

