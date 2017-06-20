#!/usr/bin/env python2

from TreeWalker import TreeWalker
from CachePath import *
import sys
import os
import os.path
from Options import Options


def main():
	reload(sys)
	sys.setdefaultencoding("UTF-8")
	if len(sys.argv) != 3 and len(sys.argv) != 2:
		print "usage: %s ALBUM_PATH CACHE_PATH - or %s CONFIG_FILE" % (sys.argv[0], sys.argv[0])
		return
	
	#~ except TypeError:
		#~ message("Options", "Incorrect options in Options.py")
		#~ sys.exit(-97)
	try:
		os.umask(022)
		if len(sys.argv) == 3:
			# 2 arguments: album and cache paths
			# the other parameters are the default options
			Options()
			message("Browsing", "start!")
			TreeWalker(sys.argv[1], sys.argv[2])
		else:
			# 1 arguments: the config files
			# which modifies the default options
			execfile(sys.argv[1])
			Options()
			message("Browsing", "start!")
			TreeWalker(Options.Options['albumPath'], Options.Options['cachePath'])
	except KeyboardInterrupt:
		message("keyboard", "CTRL+C pressed, quitting.")
		sys.exit(-97)
	
if __name__ == "__main__":
	main()
