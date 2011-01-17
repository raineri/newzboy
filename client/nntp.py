import nntplib
import socket

# Need to override __init__ to allow us to bind(), ugh :(
class NNTP(nntplib.NNTP):
	def __init__(self, host, port=nntplib.NNTP_PORT, user=None, password=None,
				readermode=None, bindto=None):
		self.host = host
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if bindto:
			self.sock.bind((bindto, 0))
		self.sock.connect((self.host, self.port))
		self.file = self.sock.makefile('rb')
		self.debugging = 0
		self.welcome = self.getresp()
		
		# 'mode reader' is sometimes necessary to enable 'reader' mode.
		# However, the order in which 'mode reader' and 'authinfo' need to
		# arrive differs between some NNTP servers. Try to send
		# 'mode reader', and if it fails with an authorization failed
		# error, try again after sending authinfo.
		readermode_afterauth = 0
		if readermode:
			try:
				self.welcome = self.shortcmd('mode reader')
			except nntplib.NNTPPermanentError:
				# error 500, probably 'not implemented'
				pass
			except nntplib.NNTPTemporaryError, e:
				if user and e.response[:3] == '480':
					# Need authorization before 'mode reader'
					readermode_afterauth = 1
				else:
					raise
		# Perform NNRP authentication if needed.
		if user:
			resp = self.shortcmd('authinfo user '+user)
			if resp[:3] == '381':
				if not password:
					raise nntplib.NNTPReplyError(resp)
				else:
					resp = self.shortcmd('authinfo pass '+password)
					if resp[:3] != '281':
						raise nntplib.NNTPPermanentError(resp)
			if readermode_afterauth:
				try:
					self.welcome = self.shortcmd('mode reader')
				except nntplib.NNTPPermanentError:
					# error 500, probably 'not implemented'
					pass

# ---------------------------------------------------------------------------

class News:
    """A class to wrap an nntp connection into something useful, yeargh!"""

    def __init__(self, host, port, username, password, bindto=None):
        self.nntp = NNTP(host=host, port=port, user=username, password=password, readermode=1)
        self.setblocking = self.nntp.sock.setblocking
        self.recv = self.nntp.sock.recv
        self.data = ''
        self.lines = []

    def body(self, article):
        command = 'BODY %s\r\n' % (article)
        self.nntp.sock.send(command)

    # recv() a chunk of data and split it into lines. Returns 0 if there's
    # probably some more data coming, and 1 if we got a dot line.
    def recv_chunk(self):
        chunk = self.recv(4096)

        # split the data into lines now
        self.data += chunk
        new_lines = self.data.split('\r\n')

        # last line is leftover junk, keep it for later
        self.data = new_lines.pop()
        
        # fix "dot dot" error
        c = 0
        for line in new_lines:
            if line[:2] == '..':
                new_lines[c] = line[1:]
            c += 1

        self.lines.extend(new_lines)

        # if we got a dot line, we're finished
        if self.lines and self.lines[-1] == '.':
            # the first line is the response, and the last line is '.'
            self.resp = self.lines[0]
            self.lines = self.lines[1:-1]
            return (len(chunk), 1)
        # or not
        else:
            return (len(chunk), 0)

    def reset(self):
        self.data = ''
        self.resp = ''
        self.lines = []
        
    def fd(self):
        return self.nntp.sock.fileno()

    def close(self):
        self.nntp.sock.close()
        
    def quit(self):
        self.nntp.quit()
