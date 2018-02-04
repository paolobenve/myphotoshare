# -*- coding: utf-8 -*-

import os
import subprocess


class VideoToolWrapper(object):
	def __init__(self):
		self.wrappers = []
		self.check_output = False
		self.cleanup = True


	def call(self, *args):
		path = args[-1]
		for tool in self.wrappers:
			try:
				if self.check_output:
					returncode = subprocess.check_output((tool, ) + args)
				else:
					returncode = subprocess.call((tool, ) + args)
					if returncode > 0:
						return False
					else:
						return "SUCCESS"
			except KeyboardInterrupt:
				if self.cleanup:
					VideoToolWrapper.remove(path)
				raise
			except OSError:
				continue
			except subprocess.CalledProcessError:
				if self.cleanup:
					VideoToolWrapper.remove(path)
				continue
			return returncode
		return False


	@staticmethod
	def remove(path):
		try:
			os.unlink(path)
		except OSError:
			pass


class VideoTranscodeWrapper(VideoToolWrapper):
	def __init__(self):
		VideoToolWrapper.__init__(self)
		self.wrappers = ['avconv', 'ffmpeg']
		self.check_output = False
		self.cleanup = True


class VideoProbeWrapper(VideoToolWrapper):
	def __init__(self):
		VideoToolWrapper.__init__(self)
		self.wrappers = ['avprobe', 'ffprobe']
		self.check_output = True
		self.cleanup = False
