# -*- coding: utf-8 -*-

from datetime import datetime
import os
import sys
import json
import ast

# @python2
try:
	import configparser
except ImportError:
	import ConfigParser as configparser


config = {}
date_time_format = "%Y-%m-%d %H:%M:%S"
exif_date_time_format = "%Y:%m:%d %H:%M:%S"
video_date_time_format = "%Y-%m-%d %H:%M:%S"
last_time = datetime.now()
elapsed_times = {}
elapsed_times_counter = {}
num_photo = 0
num_photo_processed = 0
num_photo_geotagged = 0
num_photo_with_exif_date = 0
num_video = 0
num_video_processed = 0
photos_without_geotag = []
photos_without_exif_date = []
options_not_to_be_saved = ['cache_path', 'index_html_path', 'album_path']
options_requiring_json_regeneration = ['geonames_language', 'unspecified_geonames_code', 'get_geonames_online']
options_requiring_reduced_images_regeneration = ['jpeg_quality']
options_requiring_thumbnails_regeneration = ['face_cascade_scale_factor', 'small_square_crops_background_color']
# set this variable to a new integer number whenever the json files structure changes
# json_version = 1 since ...
# json_version = 2 since checksums have been added
# json_version = 3 since geotag managing is optional
# json_version = 4 since search feature added
json_version = 4


def get_options():
	from Utilities import message, next_level, back_level
	project_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..")
	default_config_file = os.path.join(project_dir, "myphotoshare.conf.defaults")
	default_config = configparser.ConfigParser()
	default_config.readfp(open(default_config_file))
	usr_config = configparser.ConfigParser()
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

	message("Options", "asterisk denotes options changed by config file", 0)
	next_level()
	# pass config values to a dict, because ConfigParser objects are not reliable
	for option in default_config.options('options'):
		if option in ('max_verbose',
				'photo_map_zoom_level',
				'jpeg_quality',
				'video_crf',
				'thumb_spacing',
				'album_thumb_size',
				'media_thumb_size',
				'big_virtual_folders_threshold',
				'max_search_album_number',
				'respected_processors',
				'max_album_share_thumbnails_number',
				'min_album_thumbnail',
				'piwik_id'
		):
			try:
				if option != 'piwik_id' or config['piwik_server']:
					# piwik_id must be evaluated here because otherwise an error is produced if it's not set
					config[option] = usr_config.getint('options', option)
				else:
					config[option] = ""
			except configparser.Error:
				next_level()
				message("WARNING: option " + option + " in user config file", "is not integer, using default value", 2)
				back_level()
				config[option] = default_config.getint('options', option)
		elif option in ('follow_symlinks',
				'checksum',
				'different_album_thumbnails',
				'albums_slide_style',
				'show_media_names_below_thumbs',
				'show_album_names_below_thumbs',
				'show_album_media_count',
				'persistent_metadata',
				'default_album_name_sort',
				'default_media_name_sort',
				'default_album_date_reverse_sort',
				'default_media_date_reverse_sort',
				'recreate_fixed_height_thumbnails',
				'get_geonames_online',
				'show_faces'
		):
			try:
				config[option] = usr_config.getboolean('options', option)
			except ValueError:
				next_level()
				message("WARNING: option " + option + " in user config file", "is not boolean, using default value", 2)
				back_level()
				config[option] = default_config.getboolean('options', option)
		elif option in ('reduced_sizes', 'map_zoom_levels'):
			config[option] = ast.literal_eval(usr_config.get('options', option))
		elif option in ('mobile_thumbnail_factor', 'face_cascade_scale_factor'):
			config[option] = usr_config.getfloat('options', option)
			if config[option] < 1:
				config[option] = 1
		else:
			config[option] = usr_config.get('options', option)

		option_value = str(config[option])
		option_length = len(option_value)
		max_length = 40
		spaces = ""
		#pylint
		for _ in range(max_length - option_length):
			spaces += " "
		max_spaces = ""
		#pylint
		for _ in range(max_length):
			max_spaces += " "

		default_option_value = str(default_config.get('options', option))
		default_option_length = len(default_option_value)
		default_spaces = ""
		for _ in range(max_length - default_option_length - 2):
			default_spaces += " "
		if default_config.get('options', option) == usr_config.get('options', option):
			option_value = "  " + option_value + spaces + "[DEFAULT" + max_spaces + "]"
		else:
			option_value = "* " + option_value + spaces + "[DEFAULT: " + default_option_value + default_spaces + "]"

		message(option, option_value, 0)

	# all cache names are lower case => bit rate must be lower case too
	config['video_transcode_bitrate'] = config['video_transcode_bitrate'].lower()

	# set default values
	if config['geonames_language'] == '':
		if config['language'] != '':
			config['geonames_language'] = config['language']
			message("geonames_language option unset", "using language value: " + config['language'], 3)
		else:
			config['geonames_language'] = os.getenv('LANG')[:2]
			message("geonames_language and language options unset", "using system language (" + config['geonames_language'] + ") for geonames_language option", 3)
	if config['get_geonames_online']:
		# warn if using demo geonames user
		if config['geonames_user'] == str(default_config.get('options', 'geonames_user')):
			message("WARNING!", "You are using the myphotoshare demo geonames user, get and use your own user as soon as possible", 0)

	# values that have type != string
	back_level()

	# @python2
	if sys.version_info < (3, ):
		if config['index_html_path']:
			config['index_html_path'] = os.path.abspath(config['index_html_path']).decode(sys.getfilesystemencoding())
		if config['album_path']:
			config['album_path'] = os.path.abspath(config['album_path']).decode(sys.getfilesystemencoding())
		if config['cache_path']:
			config['cache_path'] = os.path.abspath(config['cache_path']).decode(sys.getfilesystemencoding())
	else:
		if config['index_html_path']:
			config['index_html_path'] = os.fsdecode(os.path.abspath(config['index_html_path']))
		if config['album_path']:
			config['album_path'] = os.fsdecode(os.path.abspath(config['album_path']))
		if config['cache_path']:
			config['cache_path'] = os.fsdecode(os.path.abspath(config['cache_path']))

	# try to guess value not given
	guessed_index_dir = False
	guessed_album_dir = False
	guessed_cache_dir = False
	if (
		not config['index_html_path'] and
		not config['album_path'] and
		not config['cache_path']
	):
		message("options", "neither index_html_path nor album_path or cache_path have been defined, assuming default positions", 3)
		# default position for index_html_path is script_path/../web
		# default position for album path is script_path/../web/albums
		# default position for cache path is script_path/../web/cache
		script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
		config['index_html_path'] = os.path.abspath(os.path.join(script_path, "..", "web"))
		config['album_path'] = os.path.abspath(os.path.join(config['index_html_path'], "albums"))
		config['cache_path'] = os.path.abspath(os.path.join(config['index_html_path'], "cache"))
		guessed_index_dir = True
		guessed_album_dir = True
		guessed_cache_dir = True
	elif (
		config['index_html_path'] and
		not config['album_path'] and
		not config['cache_path']
	):
		message("options", "only index_html_path is given, using its subfolder 'albums' for album_path and 'cache' for cache_path", 3)
		config['album_path'] = os.path.join(config['index_html_path'], "albums")
		config['cache_path'] = os.path.join(config['index_html_path'], "cache")
		guessed_album_dir = True
		guessed_cache_dir = True
	elif (
		not config['index_html_path'] and
		config['album_path'] and
		config['cache_path'] and
		config['album_path'][:config['album_path']
			.rfind("/")] == config['cache_path'][:config['cache_path'].rfind("/")]
	):
		guessed_index_dir = True
		message("options", "only album_path or cache_path has been given, using their common parent folder for index_html_path", 3)
		config['index_html_path'] = config['album_path'][:config['album_path'].rfind("/")]
	elif not (
		config['index_html_path'] and
		config['album_path'] and
		config['cache_path']
	):
		message("options", "you must define at least some of index_html_path, album_path and cache_path, and correctly; quitting", 0)
		sys.exit(-97)

	if guessed_index_dir or guessed_album_dir or guessed_cache_dir:
		message("options", "guessed value(s):", 2)
		next_level()
		if guessed_index_dir:
			message('index_html_path', config['index_html_path'], 2)
		if guessed_album_dir:
			message('album_path', config['album_path'], 2)
		if guessed_cache_dir:
			message('cache_path', config['cache_path'], 2)
		back_level()

	# the album directory must exist and be readable
	try:
		os.stat(config['album_path'])
	except OSError:
		message("FATAL ERROR", config['album_path'] + " doesn't exist or unreadable, quitting", 0)
		sys.exit(-97)

	# the cache directory must exist and be writable, or we'll try to create it
	try:
		os.stat(config['cache_path'])
		if not os.access(config['cache_path'], os.W_OK):
			message("FATAL ERROR", config['cache_path'] + " not writable, quitting", 0)
			sys.exit(-97)
	except OSError:
		try:
			os.mkdir(config['cache_path'])
			message("directory created", config['cache_path'], 4)
			os.chmod(config['cache_path'], 0o777)
			message("permissions set", config['cache_path'], 4)
		except OSError:
			message("FATAL ERROR", config['cache_path'] + " inexistent and couldn't be created, quitting", 0)
			sys.exit(-97)

	# create the directory where php will put album composite images
	album_cache_dir = os.path.join(config['cache_path'], config['cache_album_subdir'])
	try:
		os.stat(album_cache_dir)
	except OSError:
		try:
			message("creating cache directory for composite images", album_cache_dir, 4)
			os.mkdir(album_cache_dir)
			os.chmod(album_cache_dir, 0o777)
		except OSError:
			message("FATAL ERROR", config['cache_path'] + " not writable, quitting", 0)
			sys.exit(-97)

	# get old options: they are revised in order to decide whether to recreate something
	json_options_file = os.path.join(config['index_html_path'], "cache/options.json")
	try:
		with open(json_options_file) as old_options_file:
			old_options = json.load(old_options_file)
	except IOError:
		old_options = config

	config['recreate_reduced_photos'] = False
	for option in options_requiring_reduced_images_regeneration:
		try:
			if old_options[option] != config[option]:
				config['recreate_reduced_photos'] = True
				message("options", "'" + option + "' has changed from previous scanner run, forcing recreation of reduced size images", 3)
		except KeyError:
			config['recreate_reduced_photos'] = True
			message("options", "'" + option + "' wasn't set on previous scanner run, forcing recreation of reduced size images", 3)

	config['recreate_thumbnails'] = False
	for option in options_requiring_thumbnails_regeneration:
		try:
			if old_options[option] != config[option]:
				config['recreate_thumbnails'] = True
				message("options", "'" + option + "' has changed from previous scanner run, forcing recreation of thumbnails", 3)
		except KeyError:
			config['recreate_thumbnails'] = True
			message("options", "'" + option + "' wasn't set on previous scanner run, forcing recreation of thumbnails", 3)


	config['recreate_json_files'] = False
	for option in options_requiring_json_regeneration:
		try:
			if old_options[option] != config[option]:
				config['recreate_json_files'] = True
				message("options", "'" + option + "' has changed from previous scanner run, forcing recreation of json files", 3)
				break
		except KeyError:
			config['recreate_json_files'] = True
			message("options", "'" + option + "' wasn't set on previous scanner run, forcing recreation of json files", 3)
			break
