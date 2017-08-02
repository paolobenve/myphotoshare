#!/usr/bin/env python2

from TreeWalker import TreeWalker
from CachePath import message, next_level, back_level
import sys
import os
#~ import os.path
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
	usr_config.add_section("options")
	for option in default_config.options('options'):
		usr_config.set("options", option, default_config.get("options", option))
	
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
	for option in default_config.options('options'):
		if option in ('max_verbose',
				'jpeg_quality',
				'thumb_spacing',
				'album_thumb_size',
				'media_thumb_size',
				'big_date_folders_threshold',
				'respected_processors',
				'max_album_share_thumbnails_number',
				'min_album_thumbnail',
				'piwik_id'
		):
			try:
				if option != 'piwik_id' or Options.config['piwik_server']:
					# piwik_id must be evaluated here because otherwise an error is produced if it's not set
					Options.config[option] = usr_config.getint('options', option)
				else:
					Options.config[option] = ""
			except:
				next_level()
				message("WARNING: option " + option + " in user config file", "is not integer, using default value")
				back_level()
				Options.config[option] = default_config.getint('options', option)
		elif option in ('different_album_thumbnails',
				'albums_slide_style',
				'show_media_names_below_thumbs_in_albums',
				'persistent_metadata',
				'default_album_reverse_sort',
				'default_media_reverse_sort'
		):
			try:
				Options.config[option] = usr_config.getboolean('options', option)
			except:
				next_level()
				message("WARNING: option " + option + " in user config file", "is not boolean, using default value")
				back_level()
				Options.config[option] = default_config.getboolean('options', option)
		elif option in ('reduced_sizes'):
			Options.config[option] = eval(usr_config.get('options', option))
		else:
			Options.config[option] = usr_config.get('options', option)
			
		option_value = str(Options.config[option])
		option_length = len(option_value)
		max_length = 40
		spaces = ""
		for i in range(max_length - option_length):
			spaces += " "
		max_spaces = ""
		for i in range(max_length):
			max_spaces += " "
		
		default_option_value = str(default_config.get('options', option))
		default_option_length = len(default_option_value)
		default_spaces = ""
		for i in range(max_length - default_option_length - 2):
			default_spaces += " "
		if default_config.get('options', option) == usr_config.get('options', option):
			option_value = "  " + option_value + spaces + "[DEFAULT" + max_spaces + "]"
		else:
			option_value = "* " + option_value + spaces + "[DEFAULT: " + default_option_value + default_spaces + "]"
		
		message(option, option_value)
	# values that have type != string
	back_level()
	
	if Options.config['index_html_path']:
		Options.config['index_html_path'] = os.path.abspath(Options.config['index_html_path']).decode(sys.getfilesystemencoding())
	if Options.config['album_path']:
		Options.config['album_path'] = os.path.abspath(Options.config['album_path']).decode(sys.getfilesystemencoding())
	if Options.config['cache_path']:
		Options.config['cache_path'] = os.path.abspath(Options.config['cache_path']).decode(sys.getfilesystemencoding())
	
	# try to guess value not given
	guessed_index_dir = False
	guessed_album_dir = False
	guessed_cache_dir = False
	if (
		not Options.config['index_html_path'] and
		not Options.config['album_path'] and
		not Options.config['cache_path']
	):
		message("options", "neither index_html_path nor album_path or cache_path have been defined, assuming default positions")
		# default position for index_html_path is script_path/../web
		# default position for album path is script_path/../web/albums
		# default position for cache path is script_path/../web/cache
		script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
		Options.config['index_html_path'] = os.path.abspath(os.path.join(script_path, "..", "web"))
		Options.config['album_path'] = os.path.abspath(os.path.join(Options.config['index_html_path'], "albums"))
		Options.config['cache_path'] = os.path.abspath(os.path.join(Options.config['index_html_path'], "cache"))
		guessed_index_dir = True
		guessed_album_dir = True
		guessed_cache_dir = True
	elif (
		Options.config['index_html_path'] and
		not Options.config['album_path'] and
		not Options.config['cache_path']
	):
		message("options", "only index_html_path is given, using its subfolder 'albums' for album_path and 'cache' for cache_path")
		Options.config['album_path'] = os.path.join(Options.config['index_html_path'], "albums")
		Options.config['cache_path'] = os.path.join(Options.config['index_html_path'], "cache")
		guessed_album_dir = True
		guessed_cache_dir = True
	elif (
		not Options.config['index_html_path'] and
		Options.config['album_path'] and
		Options.config['cache_path'] and
		Options.config['album_path'][:Options.config['album_path']
			.rfind("/")] == Options.config['cache_path'][:Options.config['cache_path'].rfind("/")]
	):
		guessed_index_dir = True
		message("options", "only album_path or cache_path has been given, using their common parent folder for index_html_path")
		Options.config['index_html_path'] = Options.config['album_path'][:Options.config['album_path'].rfind("/")]
	elif not (
		Options.config['index_html_path'] and
		Options.config['album_path'] and
		Options.config['cache_path']
	):
		message("options", "you must define at least some of index_html_path, album_path and cache_path, and correctly; quitting")
		sys.exit(-97)
	
	if guessed_index_dir or guessed_album_dir or guessed_cache_dir:
		message("options", "guessed value(s):")
		next_level()
		if guessed_index_dir:
			message('index_html_path', Options.config['index_html_path'])
		if guessed_album_dir:
			message('album_path', Options.config['album_path'])
		if guessed_cache_dir:
			message('cache_path', Options.config['cache_path'])
		back_level()
	
	# the album directory must exist and be readable
	try:
		os.stat(Options.config['album_path'])
	except:
		message("FATAL ERROR", Options.config['album_path'] + " doesn't exist or unreadable, quitting")
		sys.exit(-97)
		
	# the cache directory must exist, or we'll try to create it
	try:
		os.stat(Options.config['cache_path'])
	except:
		try:
			os.mkdir(Options.config['cache_path'])
			message("directory created", Options.config['cache_path'], 3)
			os.chmod(Options.config['cache_path'], 0777)
			message("permissions set", Options.config['cache_path'], 3)
		except:
			message("FATAL ERROR", Options.config['cache_path'] + " inexistent and couldn't be created, quitting")
			sys.exit(-97)
	
	# create the directory where php will put album composite images
	albumCacheDir = os.path.join(Options.config['cache_path'], 'album')
	try:
		os.stat(albumCacheDir)
	except:
		message("creating album cache directory for php", albumCacheDir, 3)
		os.mkdir(albumCacheDir)
	os.chmod(albumCacheDir, 0777)
	
	json_options_file = os.path.join(Options.config['index_html_path'], 'options.json')
	try:
		with open(json_options_file) as old_options_file:
			old_options = json.load(old_options_file)
	except IOError:
		json_options_file = os.path.join(Options.config['index_html_path'], "cache/options.json")
		try:
			with open(json_options_file) as old_options_file:
				old_options = json.load(old_options_file)
		except IOError:
			old_options = Options.config
	
	Options.config['recreate_reduced_photos'] = False
	try:
		if (
			old_options['jpeg_quality'] != Options.config['jpeg_quality']
		):
			Options.config['recreate_reduced_photos'] = True
			Options.config['recreate_thumbnails'] = True
	except KeyError:
		Options.config['recreate_reduced_photos'] = True
		Options.config['recreate_thumbnails'] = True
	Options.config['recreate_thumbnails'] = False
	try:
		if (
			old_options['media_thumb_type'] != Options.config['media_thumb_type'] or
			old_options['album_thumb_type'] != Options.config['album_thumb_type']
		):
			Options.config['recreate_thumbnails'] = True
	except KeyError:
		Options.config['recreate_thumbnails'] = True
	
	try:
		os.umask(002)
		TreeWalker()
	except KeyboardInterrupt:
		message("keyboard", "CTRL+C pressed, quitting.")
		sys.exit(-97)
	

if __name__ == "__main__":
	main()
