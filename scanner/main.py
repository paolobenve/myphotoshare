#!/usr/bin/env python2

from TreeWalker import TreeWalker
from CachePath import message
import sys
import os
import os.path
from Options import Options


def main():
	reload(sys)
	sys.setdefaultencoding("UTF-8")
	if len(sys.argv) != 3:
		print "usage: %s ALBUM_PATH CACHE_PATH" % sys.argv[0]
		return
	#~ try:
	Options()
	#~ except TypeError:
		#~ message("Options", "Incorrect options in Options.py")
		#~ sys.exit(-97)
	try:
		os.umask(022)
		package_directory = os.path.dirname(os.path.abspath(__file__))
		message("dir",package_directory)
		message("options", str(Options.Options['albumPath']))
		TreeWalker(os.path.join(package_directory, Options.Options['albumPath']), os.path.join(package_directory, Options.Options['cachePath']))
	except KeyboardInterrupt:
		message("keyboard", "CTRL+C pressed, quitting.")
		sys.exit(-97)
	
if __name__ == "__main__":
	main()
