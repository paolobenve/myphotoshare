# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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

from Utilities import message, next_level, back_level, find, find_in_usr_share

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
options_requiring_json_regeneration = ['geonames_language', 'unspecified_geonames_code', 'get_geonames_online', 'metadata_tools_preference']
options_requiring_reduced_images_regeneration = ['jpeg_quality']
options_requiring_thumbnails_regeneration = ['face_cascade_scale_factor', 'small_square_crops_background_color', 'cv2_installed']

# lets put here all unicode combining code points, in order to be sure to use the same in both python and js
# from https://github.com/paulmillr/unicode-categories/blob/master/index.js

# Unicode non-spacing marks
unicode_combining_marks_n = '\u0300\u0301\u0302\u0303\u0304\u0305\u0306\u0307\u0308\u0309\u030A\u030B\u030C\u030D\u030E\u030F\u0310\u0311\u0312\u0313\u0314\u0315\u0316\u0317\u0318\u0319\u031A\u031B\u031C\u031D\u031E\u031F\u0320\u0321\u0322\u0323\u0324\u0325\u0326\u0327\u0328\u0329\u032A\u032B\u032C\u032D\u032E\u032F\u0330\u0331\u0332\u0333\u0334\u0335\u0336\u0337\u0338\u0339\u033A\u033B\u033C\u033D\u033E\u033F\u0340\u0341\u0342\u0343\u0344\u0345\u0346\u0347\u0348\u0349\u034A\u034B\u034C\u034D\u034E\u034F\u0350\u0351\u0352\u0353\u0354\u0355\u0356\u0357\u0358\u0359\u035A\u035B\u035C\u035D\u035E\u035F\u0360\u0361\u0362\u0363\u0364\u0365\u0366\u0367\u0368\u0369\u036A\u036B\u036C\u036D\u036E\u036F\u0483\u0484\u0485\u0486\u0487\u0591\u0592\u0593\u0594\u0595\u0596\u0597\u0598\u0599\u059A\u059B\u059C\u059D\u059E\u059F\u05A0\u05A1\u05A2\u05A3\u05A4\u05A5\u05A6\u05A7\u05A8\u05A9\u05AA\u05AB\u05AC\u05AD\u05AE\u05AF\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7\u05B8\u05B9\u05BA\u05BB\u05BC\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061A\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0656\u0657\u0658\u0659\u065A\u065B\u065C\u065D\u065E\u0670\u06D6\u06D7\u06D8\u06D9\u06DA\u06DB\u06DC\u06DF\u06E0\u06E1\u06E2\u06E3\u06E4\u06E7\u06E8\u06EA\u06EB\u06EC\u06ED\u0711\u0730\u0731\u0732\u0733\u0734\u0735\u0736\u0737\u0738\u0739\u073A\u073B\u073C\u073D\u073E\u073F\u0740\u0741\u0742\u0743\u0744\u0745\u0746\u0747\u0748\u0749\u074A\u07A6\u07A7\u07A8\u07A9\u07AA\u07AB\u07AC\u07AD\u07AE\u07AF\u07B0\u07EB\u07EC\u07ED\u07EE\u07EF\u07F0\u07F1\u07F2\u07F3\u0901\u0902\u093C\u0941\u0942\u0943\u0944\u0945\u0946\u0947\u0948\u094D\u0951\u0952\u0953\u0954\u0962\u0963\u0981\u09BC\u09C1\u09C2\u09C3\u09C4\u09CD\u09E2\u09E3\u0A01\u0A02\u0A3C\u0A41\u0A42\u0A47\u0A48\u0A4B\u0A4C\u0A4D\u0A51\u0A70\u0A71\u0A75\u0A81\u0A82\u0ABC\u0AC1\u0AC2\u0AC3\u0AC4\u0AC5\u0AC7\u0AC8\u0ACD\u0AE2\u0AE3\u0B01\u0B3C\u0B3F\u0B41\u0B42\u0B43\u0B44\u0B4D\u0B56\u0B62\u0B63\u0B82\u0BC0\u0BCD\u0C3E\u0C3F\u0C40\u0C46\u0C47\u0C48\u0C4A\u0C4B\u0C4C\u0C4D\u0C55\u0C56\u0C62\u0C63\u0CBC\u0CBF\u0CC6\u0CCC\u0CCD\u0CE2\u0CE3\u0D41\u0D42\u0D43\u0D44\u0D4D\u0D62\u0D63\u0DCA\u0DD2\u0DD3\u0DD4\u0DD6\u0E31\u0E34\u0E35\u0E36\u0E37\u0E38\u0E39\u0E3A\u0E47\u0E48\u0E49\u0E4A\u0E4B\u0E4C\u0E4D\u0E4E\u0EB1\u0EB4\u0EB5\u0EB6\u0EB7\u0EB8\u0EB9\u0EBB\u0EBC\u0EC8\u0EC9\u0ECA\u0ECB\u0ECC\u0ECD\u0F18\u0F19\u0F35\u0F37\u0F39\u0F71\u0F72\u0F73\u0F74\u0F75\u0F76\u0F77\u0F78\u0F79\u0F7A\u0F7B\u0F7C\u0F7D\u0F7E\u0F80\u0F81\u0F82\u0F83\u0F84\u0F86\u0F87\u0F90\u0F91\u0F92\u0F93\u0F94\u0F95\u0F96\u0F97\u0F99\u0F9A\u0F9B\u0F9C\u0F9D\u0F9E\u0F9F\u0FA0\u0FA1\u0FA2\u0FA3\u0FA4\u0FA5\u0FA6\u0FA7\u0FA8\u0FA9\u0FAA\u0FAB\u0FAC\u0FAD\u0FAE\u0FAF\u0FB0\u0FB1\u0FB2\u0FB3\u0FB4\u0FB5\u0FB6\u0FB7\u0FB8\u0FB9\u0FBA\u0FBB\u0FBC\u0FC6\u102D\u102E\u102F\u1030\u1032\u1033\u1034\u1035\u1036\u1037\u1039\u103A\u103D\u103E\u1058\u1059\u105E\u105F\u1060\u1071\u1072\u1073\u1074\u1082\u1085\u1086\u108D\u135F\u1712\u1713\u1714\u1732\u1733\u1734\u1752\u1753\u1772\u1773\u17B7\u17B8\u17B9\u17BA\u17BB\u17BC\u17BD\u17C6\u17C9\u17CA\u17CB\u17CC\u17CD\u17CE\u17CF\u17D0\u17D1\u17D2\u17D3\u17DD\u180B\u180C\u180D\u18A9\u1920\u1921\u1922\u1927\u1928\u1932\u1939\u193A\u193B\u1A17\u1A18\u1B00\u1B01\u1B02\u1B03\u1B34\u1B36\u1B37\u1B38\u1B39\u1B3A\u1B3C\u1B42\u1B6B\u1B6C\u1B6D\u1B6E\u1B6F\u1B70\u1B71\u1B72\u1B73\u1B80\u1B81\u1BA2\u1BA3\u1BA4\u1BA5\u1BA8\u1BA9\u1C2C\u1C2D\u1C2E\u1C2F\u1C30\u1C31\u1C32\u1C33\u1C36\u1C37\u1DC0\u1DC1\u1DC2\u1DC3\u1DC4\u1DC5\u1DC6\u1DC7\u1DC8\u1DC9\u1DCA\u1DCB\u1DCC\u1DCD\u1DCE\u1DCF\u1DD0\u1DD1\u1DD2\u1DD3\u1DD4\u1DD5\u1DD6\u1DD7\u1DD8\u1DD9\u1DDA\u1DDB\u1DDC\u1DDD\u1DDE\u1DDF\u1DE0\u1DE1\u1DE2\u1DE3\u1DE4\u1DE5\u1DE6\u1DFE\u1DFF\u20D0\u20D1\u20D2\u20D3\u20D4\u20D5\u20D6\u20D7\u20D8\u20D9\u20DA\u20DB\u20DC\u20E1\u20E5\u20E6\u20E7\u20E8\u20E9\u20EA\u20EB\u20EC\u20ED\u20EE\u20EF\u20F0\u2DE0\u2DE1\u2DE2\u2DE3\u2DE4\u2DE5\u2DE6\u2DE7\u2DE8\u2DE9\u2DEA\u2DEB\u2DEC\u2DED\u2DEE\u2DEF\u2DF0\u2DF1\u2DF2\u2DF3\u2DF4\u2DF5\u2DF6\u2DF7\u2DF8\u2DF9\u2DFA\u2DFB\u2DFC\u2DFD\u2DFE\u2DFF\u302A\u302B\u302C\u302D\u302E\u302F\u3099\u309A\uA66F\uA67C\uA67D\uA802\uA806\uA80B\uA825\uA826\uA8C4\uA926\uA927\uA928\uA929\uA92A\uA92B\uA92C\uA92D\uA947\uA948\uA949\uA94A\uA94B\uA94C\uA94D\uA94E\uA94F\uA950\uA951\uAA29\uAA2A\uAA2B\uAA2C\uAA2D\uAA2E\uAA31\uAA32\uAA35\uAA36\uAA43\uAA4C\uFB1E\uFE00\uFE01\uFE02\uFE03\uFE04\uFE05\uFE06\uFE07\uFE08\uFE09\uFE0A\uFE0B\uFE0C\uFE0D\uFE0E\uFE0F\uFE20\uFE21\uFE22\uFE23\uFE24\uFE25\uFE26'
# Unicode combining space marks
unicode_combining_marks_c = '\u0903\u093E\u093F\u0940\u0949\u094A\u094B\u094C\u0982\u0983\u09BE\u09BF\u09C0\u09C7\u09C8\u09CB\u09CC\u09D7\u0A03\u0A3E\u0A3F\u0A40\u0A83\u0ABE\u0ABF\u0AC0\u0AC9\u0ACB\u0ACC\u0B02\u0B03\u0B3E\u0B40\u0B47\u0B48\u0B4B\u0B4C\u0B57\u0BBE\u0BBF\u0BC1\u0BC2\u0BC6\u0BC7\u0BC8\u0BCA\u0BCB\u0BCC\u0BD7\u0C01\u0C02\u0C03\u0C41\u0C42\u0C43\u0C44\u0C82\u0C83\u0CBE\u0CC0\u0CC1\u0CC2\u0CC3\u0CC4\u0CC7\u0CC8\u0CCA\u0CCB\u0CD5\u0CD6\u0D02\u0D03\u0D3E\u0D3F\u0D40\u0D46\u0D47\u0D48\u0D4A\u0D4B\u0D4C\u0D57\u0D82\u0D83\u0DCF\u0DD0\u0DD1\u0DD8\u0DD9\u0DDA\u0DDB\u0DDC\u0DDD\u0DDE\u0DDF\u0DF2\u0DF3\u0F3E\u0F3F\u0F7F\u102B\u102C\u1031\u1038\u103B\u103C\u1056\u1057\u1062\u1063\u1064\u1067\u1068\u1069\u106A\u106B\u106C\u106D\u1083\u1084\u1087\u1088\u1089\u108A\u108B\u108C\u108F\u17B6\u17BE\u17BF\u17C0\u17C1\u17C2\u17C3\u17C4\u17C5\u17C7\u17C8\u1923\u1924\u1925\u1926\u1929\u192A\u192B\u1930\u1931\u1933\u1934\u1935\u1936\u1937\u1938\u19B0\u19B1\u19B2\u19B3\u19B4\u19B5\u19B6\u19B7\u19B8\u19B9\u19BA\u19BB\u19BC\u19BD\u19BE\u19BF\u19C0\u19C8\u19C9\u1A19\u1A1A\u1A1B\u1B04\u1B35\u1B3B\u1B3D\u1B3E\u1B3F\u1B40\u1B41\u1B43\u1B44\u1B82\u1BA1\u1BA6\u1BA7\u1BAA\u1C24\u1C25\u1C26\u1C27\u1C28\u1C29\u1C2A\u1C2B\u1C34\u1C35\uA823\uA824\uA827\uA880\uA881\uA8B4\uA8B5\uA8B6\uA8B7\uA8B8\uA8B9\uA8BA\uA8BB\uA8BC\uA8BD\uA8BE\uA8BF\uA8C0\uA8C1\uA8C2\uA8C3\uA952\uA953\uAA2F\uAA30\uAA33\uAA34\uAA4D'
# all combining mark: this variable will be passed in options.json to js
config['unicode_combining_marks'] = unicode_combining_marks_n + unicode_combining_marks_c

thumbnail_types_and_sizes_list = None
config['cv2_installed'] = True
face_cascade = None
eye_cascade = None

# set this variable to a new value (previously was a number, now it may include letters) whenever the json files structure changes, it can be the app version
# json_version = 0 is debug mode: json files are always considered invalid
# json_version = 1 since ...
# json_version = 2 since checksums have been added
# json_version = 3 since geotag managing is optional
# json_version = 4 since search feature added
json_version = "3.4beta10"

def initialize_opencv():
	global face_cascade, eye_cascade

	try:
		import cv2

		message("importer", "opencv library available, using it!", 3)
		next_level()
		FACE_CONFIG_FILE = "haarcascade_frontalface_default.xml"
		message("looking for file...", FACE_CONFIG_FILE + " in /usr/share", 5)
		face_config_file_with_path = find_in_usr_share(FACE_CONFIG_FILE)
		if not face_config_file_with_path:
			message("face xml file not found", FACE_CONFIG_FILE + " not found in /usr/share", 5)
			message("looking for file...", FACE_CONFIG_FILE + " in /", 5)
			face_config_file_with_path = find(FACE_CONFIG_FILE)
		if not face_config_file_with_path:
			next_level()
			message("face xml file not found", FACE_CONFIG_FILE, 5)
			back_level()
			config['cv2_installed'] = False
		else:
			face_cascade = cv2.CascadeClassifier(face_config_file_with_path)

			next_level()
			message("face xml file found and initialized:", face_config_file_with_path, 5)
			back_level()
			EYE_CONFIG_FILE = "haarcascade_eye.xml"
			message("looking for file...", EYE_CONFIG_FILE, 5)
			eye_config_file_with_path = find_in_usr_share(EYE_CONFIG_FILE)
			if not eye_config_file_with_path:
				eye_config_file_with_path = find(EYE_CONFIG_FILE)
			if not eye_config_file_with_path:
				next_level()
				message("eyes xml file not found", EYE_CONFIG_FILE, 5)
				back_level()
				config['cv2_installed'] = False
			else:
				eye_cascade = cv2.CascadeClassifier(eye_config_file_with_path)
				next_level()
				message("found and initialized:", eye_config_file_with_path, 5)
				back_level()
		back_level()
	except ImportError:
		config['cv2_installed'] = False
		message("importer", "No opencv library available, not using it", 2)

def get_options():
	project_dir = os.path.dirname(os.path.realpath(os.path.join(__file__, "..")))
	default_config_file = os.path.join(project_dir, "myphotoshare.conf.defaults")
	default_config = configparser.ConfigParser()
	default_config.readfp(open(default_config_file, "r"))
	usr_config = configparser.ConfigParser()
	usr_config.add_section("options")
	for option in default_config.options('options'):
		usr_config.set("options", option, default_config.get("options", option))

	if len(sys.argv) == 2:
		# 1 arguments: the config files
		# which modifies the default options
		usr_config.readfp(open(sys.argv[1], "r"))
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
				# the following option will be converted to integer further on
				'num_processors',
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
				'default_album_reverse_sort',
				'default_media_reverse_sort',
				'recreate_fixed_height_thumbnails',
				'get_geonames_online',
				'show_faces',
				'use_stop_words'
		):
			try:
				config[option] = usr_config.getboolean('options', option)
			except ValueError:
				next_level()
				message("WARNING: option " + option + " in user config file", "is not boolean, using default value", 2)
				back_level()
				config[option] = default_config.getboolean('options', option)
		elif option in ('reduced_sizes', 'map_zoom_levels', 'metadata_tools_preference'):
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
