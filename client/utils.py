import os, htmlentitydefs, string

def run(cmd):
    pipe = os.popen(cmd + ' 2>&1', 'r')
    text = pipe.read()
    sts = pipe.close()
    if sts is None: sts = 0
    if text[-1:] == '\n': text = text[:-1]
    return sts,text

def htmlEncode(str):
    entitydefs = {}
    for k, v in htmlentitydefs.entitydefs.items():
        entitydefs[v] = '&' + k + ';'
    str = string.replace(str, '&', '&amp;')
    str = string.replace(str, chr(0x81), 'u')
    for k, v in entitydefs.items():
        if k in "<>\"'":
            continue
        if v != '&amp;':
            str = string.replace(str, k, v)
    return str

def htmlDecode(str):
    entitydefs = {}
    for k, v in htmlentitydefs.entitydefs.items():
        entitydefs[v] = '&' + k + ';'
    for k, v in entitydefs.items():
        if v != '&amp;':
            str = string.replace(str, v, k)
    str = string.replace(str, '&amp;', '&')
    return str

def fileExists(fn):
    try:
        fp = open(fn)
        fp.close()
        return True
    except IOError:
        return False
        
def nfo(title, size, files, speed, time, vresult):
    f = open("newzBoy.nfo","r")
    data = f.read()
    f.close()
    data = data % (title, size, files, speed, time, vresult)
    return data

def nsize(bytes):
	bytes = float(bytes)
	if bytes < 1024:
		return '<1KB'
	elif bytes < (1024 * 1024):
		return '%dKB' % (bytes / 1024)
	else:
		return '%.1fMB' % (bytes / 1024.0 / 1024.0)
		
def ntime(tsecs):
    # < minute
    if tsecs < 60:
        return "%.1fs" % tsecs
    # < hour
    elif tsecs < 3600:
        minutes = int(tsecs/60)
        seconds = tsecs-(minutes*60)
        return "%dm %ds" % (minutes, seconds)
    # > hour
    else:
        hours = int(tsecs/60/60)
        minutes = (tsecs-(hours*60*60))/60
        seconds = tsecs-(hours*60*60)-(minutes*60)
        return "%dh %dm %ds" % (hours, minutes, seconds)

def fdToConn(fd, conns):
    c = 0
    for conn in conns:
        if conn.fd() == fd:
            return conn
        else:
            c += 1

def listFiles(path, ext):
    files = os.listdir(path)
    temp = []
    for f in files:
        if f.split(".")[-1].lower() == ext.lower():
            temp.append(f)
    return temp

def listFilesByLastUpdated(path, ext):
    files = os.listdir(path)
    temp = []
    for f in files:
        if f.split(".")[-1].lower() == ext.lower():
            mtime = os.stat(path+f).st_mtime
            temp.append([mtime,f])
    temp.sort()
    temp2 = []
    for f in temp:
        temp2.append(f[1])
    return temp2
