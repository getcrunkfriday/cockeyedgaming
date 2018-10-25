import os
import signal
import subprocess


class PlaylistProcess:
	def __init__(self):
		self.pid=None
		# If ices is already running, grab the current pid.
		# Otherwise, create a new ices process.
		try:
			self.pid=int(subprocess.check_output(["pidof","-s","ices"]))
		except:
			self.pid=None
		if not self.pid:
			self.pro = subprocess.Popen("/usr/local/bin/ices -c /etc/ices/ices.conf -v",shell=True, preexec_fn=os.setsid)
			self.pid = os.getpgid(self.pro.pid)
	def skip(self):
		os.killpg(os.getpgid(self.pid), signal.SIGUSR1)


if __name__ == "__main__":
	pro=PlaylistProcess()
	while True:
	    cmd = raw_input('>>>')
	    if cmd == "N" or cmd == "NEXT":
	        pro.skip()
	    elif cmd == "R" or cmd == "RELOAD":
	        os.killpg(os.getpgid(pro.pro.pid), signal.SIGHUP)
	    elif cmd == "E" or cmd == "END":
	        os.killpg(os.getpgid(pro.pro.pid), signal.SIGINT)
	        break

    
