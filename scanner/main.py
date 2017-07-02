#!/usr/bin/env python2

from TreeWalker import TreeWalker
from CachePath import message, next_level, back_level
import sys
import os
import os.path
import ConfigParser
import Options
import json

def main():
	reload(sys)
	sys.setdefaultencoding("UTF-8")
	if len(sys.argv) != 3 and len(sys.argv) != 2:
		print "usage: %s ALBUM_PATH CACHE_PATH - or %s CONFIG_FILE" % (sys.argv[0], sys.argv[0])
		return
	
	project_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..")
	default_config_file = os.path.join(project_dir, "photofloat.conf.defaults")
	default_config = ConfigParser.ConfigParser()
	default_config.readfp(open(default_config_file))
	
	usr_config = ConfigParser.ConfigParser()
	usr_config = default_config
	
	if len(sys.argv) == 2:
		# 1 arguments: the config files
		# which modifies the default options
		usr_config.readfp(open(sys.argv[1]))
	else:
		usr_config.set('options', 'album_path', sys.argv[1])
		usr_config.set('options', 'cache_path', sys.argv[2])

	message("Options", "asterisk denotes options changed by config file")
	next_level()
	# pass config values to a dict, because ConfigParser objects are not reliable
	for option in usr_config.options('options'):
		Options.config[option] = usr_config.get('options', option)
		if default_config.get('options', option) == Options.config.get('options', option):
			option_value = "  "
		else:
			option_value = "* "
		option_value += str(Options.config[option])
		message(option, option_value)
	back_level()

	if not Options.config['index_html_path'] and not Options.config['album_path'] and not Options.config['cache_path']:
		message("options", "at least index_html_path or both album_path and cache_path must be given, quitting")
		sys.exit(-97)
	elif Options.config['index_html_path'] and not Options.config['album_path'] and not Options.config['cache_path']:
		message("options", "on index_html_path is given, using its subfolder 'albums' for album_path and 'cache' for cache_path")
		Options.config['album_path'] = os.path.join(Options.config['index_html_path'], "albums")
		Options.config['cache_path'] = os.path.join(Options.config['index_html_path'], "cache")
	elif (not Options.config['index_html_path'] and
			Options.config['album_path'] and
			Options.config['cache_path'] and
			Options.config['album_path'][:Options.config['album_path']
				.rfind("/")] == Options.config['cache_path'][:Options.config['album_path'].rfind("/")]):
		album_path = Options.config['album_path']
		album_base = album_path[:album_path.rfind("/")]
		Options.config['index_html_path'] = album_base

	json_options_file = os.path.join(Options.config['index_html_path'], 'options.json')
	try:
		with open(json_options_file) as old_options_file:
			old_options = json.load(old_options_file)
	except IOError:
		options_file = os.path.join(Options.config['index_html_path'], "cache/options.json")
		with open(json_options_file) as old_options_file:
			old_options = json.load(old_options_file)
	
	Options.config['recreate_photo_thumbnails'] = False
	try:
		if int(old_options['jpeg_quality']) != int(Options.config['jpeg_quality']):
			Options.config['recreate_photo_thumbnails'] = True
	except KeyError:
		Options.config['recreate_photo_thumbnails'] = False
	Options.config['retranscode_videos'] = False
	try:
		if str(old_options['video_transcode_bitrate']) != str(Options.config['video_transcode_bitrate']):
			Options.config['retranscode_videos'] = True
	except KeyError:
		Options.config['retranscode_videos'] = False

	try:
		os.umask(002)
		message("Browsing", "start!")
		TreeWalker(Options.config['album_path'], Options.config['cache_path'])
	except KeyboardInterrupt:
		message("keyboard", "CTRL+C pressed, quitting.")
		sys.exit(-97)
	

if __name__ == "__main__":
	main()
