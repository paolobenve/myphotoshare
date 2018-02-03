#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from TreeWalker import TreeWalker
from Utilities import *
import sys
import Options
import os

# @python2
# Builtins removed in Python3
try:
	from imp import reload
except ImportError:
	pass


def main():
	# @python2
	if sys.version_info < (3,):
		reload(sys)
		sys.setdefaultencoding("UTF-8")
	if len(sys.argv) != 3 and len(sys.argv) != 2:
		print("usage: {0} ALBUM_PATH CACHE_PATH - or {1} CONFIG_FILE".format(sys.argv[0], sys.argv[0]))
		return

	Options.get_options()

	try:
		os.umask(0o02)
		TreeWalker()
		report_times()
	except KeyboardInterrupt:
		message("keyboard", "CTRL+C pressed, quitting.")
		sys.exit(-97)


if __name__ == "__main__":
	main()
