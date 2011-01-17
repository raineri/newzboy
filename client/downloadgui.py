from threading import Event, Thread
import time, utils
from wxPython.wx import *
import wx

class UpdateGuiThread(Thread):
    def __init__(self,frame):
        Thread.__init__(self)
        self.frame = frame
        self.frame.isShown = False
        self.lastFileNum = 0

    def run(self):
        while 1:
            time.sleep(0.1)
            try:
                # update stats
                if self.frame.stats["transfering"] == True:
                    # update speed
                    speed = self.frame.stats["file_raw_bytes"] / 1024.0 / (time.time() - self.frame.stats["file_start"])
                    self.frame.speed.SetTitle('Transfer Rate: %sKB/s' % int(speed))

                    # update eta
                    downloadedBytes = self.frame.stats["file_raw_bytes"]
                    totalBytes = self.frame.stats["file_size"]
                    bytesPerSecond = speed*1024
                    eta = utils.ntime((totalBytes-downloadedBytes)/bytesPerSecond)
                    self.frame.eta.SetTitle('Time Left: %s' % eta)

                    # update progress
                    currPercent = int((float(downloadedBytes)/totalBytes)*100)
                    self.frame.gauge.SetValue(currPercent)
                    self.frame.SetTitle('job %s of %s - file %s of %s (%s%%)' % (self.frame.stats["jnum"],self.frame.stats["tjobs"],self.frame.stats["fnum"], self.frame.stats["tfiles"], currPercent))

                    # update subject/size (these only need to be updated once per file)
                    if not (self.frame.stats["fnum"] == self.lastFileNum):
                        self.frame.subject.SetTitle(self.frame.stats["subject"])
                        self.frame.size.SetTitle('File Size: %s' % utils.nsize(self.frame.stats["file_size"]))
                        self.lastFileNum = self.frame.stats["fnum"]
                else:
                    self.frame.SetTitle("waiting for decoder")
                    self.frame.subject.SetTitle("???"+" "*150)
                    self.frame.size.SetTitle("File Size: ???")
                    self.frame.speed.SetTitle("Transfer Rate: 0KB/s")
                    self.frame.eta.SetTitle("Time Left: ???")
                    self.frame.gauge.SetValue(0)
                # show/hide gui
                if self.frame.stats["hide"] == False and self.frame.isShown == False:
                    self.frame.Show(1)
                    self.frame.isShown = True
                elif self.frame.stats["hide"] == True and self.frame.isShown == True:
                    self.frame.Show(0)
                    self.frame.isShown = False
                    self.lastFileNum = 0
            except ZeroDivisionError:
                pass
            except IndexError:
                pass
            except KeyError:
                pass
            except wx.PyDeadObjectError:
                break

class DownloadInfoFrame(wxFrame):
    def __init__(self, parent, stats):
        wxFrame.__init__(self, None, -1, "newzBoy", size = wxSize(270, 130))
        self.parent = parent
        self.stats = stats

        panel = wxPanel(self, -1)
        colSizer = wxFlexGridSizer(cols = 1, vgap = 4)

        # the progress bar
        self.gauge = wxGauge(panel, -1, range = 100, style = wxGA_SMOOTH)
        colSizer.Add(self.gauge, 0, wxEXPAND)

        # the text
        self.subject = wxStaticText(panel, -1, "???"+" "*150)
        colSizer.Add(self.subject, 0, wx.EXPAND)
        self.size = wxStaticText(panel, -1, "File Size: ???")
        colSizer.Add(self.size, 0, wxEXPAND)
        self.speed = wxStaticText(panel, -1, "Transfer Rate: ???")
        colSizer.Add(self.speed, 0, wxEXPAND)
        self.eta = wxStaticText(panel, -1, "Time Left: ???")
        colSizer.Add(self.eta, 0, wxEXPAND)

        # the border
        border = wxBoxSizer(wxHORIZONTAL)
        border.Add(colSizer, 1, wxEXPAND | wxALL, 4)
        panel.SetSizer(border)
        panel.SetAutoLayout(True)

        # the update gui thread
        t = UpdateGuiThread(self)
        t.start()

class DownloadInfoApp(wxApp):
    def __init__(self, x, stats):
        self.stats = stats
        wxApp.__init__(self, 0)

    def OnInit(self):
        DownloadInfoFrame(self, self.stats)
        return 1

class DownloadInfoThread(Thread):
    def __init__(self, stats):
        Thread.__init__(self)
        self.stats = stats
        self.stats["transfering"] = False
        self.stats["hide"] = True

    def run(self):
        di = DownloadInfoApp(0, self.stats)
        di.MainLoop()

