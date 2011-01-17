import time, os, array, binascii

def decode(files, dest):
    outfile = None
    decoder = ""
    for file in files:
        try:
            for line in open("./cache/%s" % file, "rb"):
                # fix appended newline
                line = line.rstrip("\r\n")
                line = line.rstrip("\n")
                # if theres nothing in this line, skip
                if len(line) == 0: continue
                # what decoder are we using?
                if decoder == "":
                    # yenc
                    if line[0:8] == "=ybegin ":
                        decoder = "yenc"
                        if "name=" in line:
                            b = line.index("name=")
                            outfileName = line[b+5:]
                            outfile = open(dest + outfileName, "wb")
                    # uudecode
                    elif line[0:10] == "begin 644 ":
                        decoder = "uudecode"
                        outfileName = line[10:]
                        outfile = open(dest + outfileName, "wb")
                        continue
                # yenc
                if decoder == "yenc":
                    if "=ypart" in line:
                        # seek?
                        params = line.split(' ')
                        for param in params:
                            if "begin" in param:
                                pos = long(param.split('=')[1])-1
                                outfile.seek(pos)
                    else:
                        if "=yend" in line:
                            # TODO: end of the yenc part, do crc check
                            break
                        else:
                            # decode + write to disk
                            outfile.write(yenc_process_ln(line))
                # uudecode
                if decoder == "uudecode":
                    if "end" in line:
                        pass
                    else:
                        # decode + write to disk
                        outfile.write(uu_process_ln(line))
        except IOError:
            pass
    if outfile is None:
        raise Exception, "Error decoding the file. Maybe the encoding isn't supported?"
    else:
        outfile.close()
    # remove files
    for file in files:
        try:
            os.remove("./cache/%s" % file)
        except OSError:
            pass

def yenc_process_ln(s,  array_array = array.array,
  escEantixlat =  ''.join([ chr((nc-64) & 0xff)  for nc in xrange(256) ]),
  xlat = ''.join([ chr((nc-42) & 0xff)  for nc in xrange(256) ])):
	a = array_array('c',s); ToLi = -1; FromLi = 0; Ri = len(s)
	try:
		while FromLi < Ri:
			ToLi += 1
			if a[FromLi] == "=":   a[ToLi] = escEantixlat[ord(a[FromLi+1])];  FromLi+=2
			else:                  a[ToLi] = a[FromLi];                       FromLi+=1
	except IndexError: pass # line ended with the escape-character
	return a.tostring()[:ToLi+1].translate(xlat)

def uu_process_ln(s):
    try:
        data = binascii.a2b_uu(s)
    except binascii.Error, v:
        nbytes = (((ord(s[0])-32) & 63) * 4 + 5) / 3
        data = binascii.a2b_uu(s[:nbytes])
    return data

try:
    import psyco
    psyco.bind(decode)
    psyco.bind(yenc_process_ln)
    psyco.bind(uu_process_ln)
except ImportError:
    pass
