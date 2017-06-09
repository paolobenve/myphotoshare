from CachePath import message
import os
import subprocess

class VideoToolWrapper(object):
	def call(self, *args):
		path = args[-1]
		for tool in self.wrappers:
			try:    
                                if self.check_output:
                                        p = subprocess.check_output((tool,) + args)
                                else:
                                        p = subprocess.call((tool,) + args)
                                        if p > 0:
                                                return False
                                        else:
                                                return "SUCCESS"
			except KeyboardInterrupt:
				if self.cleanup:
					self.remove(path)
				raise
			except OSError:
				continue
			except:
				if self.cleanup:
					self.remove(path)
				continue
			return p
		return False

	def remove(self, path):
		try:
			os.unlink(path)
		except:
			pass

class VideoTranscodeWrapper(VideoToolWrapper):
	def __init__(self):
		self.wrappers = ['avconv', 'ffmpeg']
                self.check_output = False
		self.cleanup = True

class VideoProbeWrapper(VideoToolWrapper):
	def __init__(self):
		self.wrappers = ['avprobe', 'ffprobe']
                self.check_output = True
		self.cleanup = False
