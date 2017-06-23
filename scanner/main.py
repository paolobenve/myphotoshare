#!/usr/bin/env python2

from TreeWalker import TreeWalker
from CachePath import message, next_level, back_level
import sys
import os
import os.path
import ConfigParser
import Options


def main():
	reload(sys)
	sys.setdefaultencoding("UTF-8")
	if len(sys.argv) != 3 and len(sys.argv) != 2:
		print "usage: %s ALBUM_PATH CACHE_PATH - or %s CONFIG_FILE" % (sys.argv[0], sys.argv[0])
		return
	
	project_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..")
	default_config_file = os.path.join(project_dir, "photofloat.conf.defaults")
	default_config = ConfigParser.ConfigParser()
	usr_config = ConfigParser.ConfigParser()
	default_config.readfp(open(default_config_file))
	
	config = default_config
	if len(sys.argv) == 2:
		# 1 arguments: the config files
		# which modifies the default options
		usr_config.readfp(open(sys.argv[1]))
	else:
		usr_config.set('options', 'albumPath', sys.argv[1])
		usr_config.set('options', 'cachePath', sys.argv[2])

	message("Options", "asterisk denotes options changed by config file")
	next_level()
	# pass config values to a dict, because ConfigParser objects are not reliable
	for option in Options.config.options('options'):
		Options.config[option] = Options.config.get('options', option)
		if default_config.get('options', option) == Options.config.get('options', option):
			value = "  "
		else:
			value = "* "
		value += str(Options.config[option])
		message(option, value)
	back_level()
	#~ if not Options.config['indexHtmlPath']:
		#~ Options.config.set('options', 'indexHtmlPath', "")
	#~ Options.config.set('options', 'thumbSizes', eval(Options.config.get('options', 'thumbSizes')))
	#~ Options.config.set('options', 'jpegQuality', int(Options.config.get('options', 'jpegQuality')))

	Options.OptionsForJs = [
		'serverAlbumPath',
		'serverCachePath',
		'cachePath',
		'language',
		'thumbSpacing',
		'foldersString',
		'byDateString',
		'cacheFolderSeparator',
		'pageTitle',
		'differentAlbumThumbnails',
		'showMediaNamesBelowInAlbums',
		'titleFontSize',
		'titleColor',
		'titleColorHover',
		'titleImageNameColor',
		'backgroundColor',
		'switchButtonBackgroundColor',
		'switchButtonBackgroundColorHover',
		'switchButtonColor',
		'switchButtonColorHover',
		'thumbSizes'
	]


	if not Options.config['indexHtmlPath'] and not Options.config['albumPath'] and not Options.config['cachePath']:
		message("options", "at least indexHtmlPath or both albumPath and cachePath must be given, quitting")
		sys.exit(-97)
	elif Options.config['indexHtmlPath'] and not Options.config['albumPath'] and not Options.config['cachePath']:
		message("options", "on indexHtmlPath is given, using its subfolder 'albums' for albumPath and 'cache' for cachePath")
		Options.config['albumPath'] = os.path.join(Options.config['indexHtmlPath'], "albums")
		Options.config['cachePath'] = os.path.join(Options.config['indexHtmlPath'], "cache")
	elif (not Options.config['indexHtmlPath'] and
			Options.config['albumPath'] and
			Options.config['cachePath'] and
			Options.config['albumPath'][:Options.config['albumPath']
				.rfind("/")] == Options.config['cachePath'][:Options.config['albumPath'].rfind("/")]):
		album_path = Options.config['albumPath']
		album_base = album_path[:album_path.rfind("/")]
		#~ print 123,album_base
		Options.config['indexHtmlPath'] = album_base
	try:
		os.umask(002)
		message("Browsing", "start!")
		if len(sys.argv) == 3:
			# 2 arguments: album and cache paths
			# the other parameters are the default options
			TreeWalker(sys.argv[1], sys.argv[2])
		else:
			# 1 arguments: the config files
			# which modifies the default options
			#~ TreeWalker(ModOptions.usrOptions['albumPath'], ModOptions.usrOptions['cachePath'])
			TreeWalker(Options.config['albumPath'], Options.config['cachePath'])
	except KeyboardInterrupt:
		message("keyboard", "CTRL+C pressed, quitting.")
		sys.exit(-97)

if __name__ == "__main__":
	main()
