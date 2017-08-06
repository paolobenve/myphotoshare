import os.path
from datetime import datetime
import hashlib
import Options

max_verbose = 0
def message(category, text, verbose = 0):
	# verbosity levels:
	# 0 = fatal errors only
	# 1 = add non-fatal errors
	# 2 = add warnings
	# 3 = add info
	# 4 = add more info
	global usrOptions
	try:
		max_verbose = Options.config['max_verbose']
	except KeyError:
		max_verbose = 0
	except AttributeError:
		max_verbose = 0
	if (verbose <= max_verbose):
		if message.level <= 0:
			sep = "  "
		else:
			sep = "--"
		print "%s %s%s[%s]%s%s" % (datetime.now().isoformat(' '), max(0, message.level) * "  |", sep, str(category), max(1, (45 - len(str(category)))) * " ", str(text))

message.level = 0
def next_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level += 1
def back_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level -= 1
def trim_base_custom(path, base):
	if path.startswith(base):
		path = path[len(base):]
	if path.startswith('/'):
		path = path[1:]
	return path
def remove_album_path(path):
	return trim_base_custom(path, Options.config['album_path'])
def cache_base(path, album, filepath=False):
	print 1111,path, album
	if not filepath:
		path = remove_album_path(path)
	if path:
		# this suffix will be used in case that different files produce the same cache name
		distinguish_suffix = 0
		while True:
			path = path.replace('/', Options.config['cache_folder_separator']).replace(' ', '_').replace('+', '_').replace('(', '').replace('&', '').replace(',', '').replace(')', '').replace('#', '').replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace('_-_', '-').lower()
			while path.find("--") != -1:
				path = path.replace("--", "-")
			while path.find("__") != -1:
				path = path.replace("__", "_")
			if album is None:
				break
			if distinguish_suffix:
				path += "_" + str(distinguish_suffix)
			cache_name_absent = True
			for media in album.media_list:
				print 333,path,media.cache_base
				if path == media.cache_base:
					cache_name_absent = False
					distinguish_suffix += 1
					break
			if cache_name_absent:
				break
	else:
		path = "root"
	print 2222,path
	return path
def json_name(path, album = None):
	return cache_base(path, album) + ".json"
def photo_cache_name(album, path, size, thumb_type = ""):
	# this function is used for video thumbnails too
	photo_suffix = "_"
	photo_suffix += str(size)
	if size == Options.config['album_thumb_size']:
		photo_suffix += "a"
		if thumb_type == "square":
			photo_suffix += "s"
		elif thumb_type == "fit":
			photo_suffix += "f"
	elif size == Options.config['media_thumb_size']:
		photo_suffix += "t"
		if thumb_type == "square":
			photo_suffix += "s"
		elif thumb_type == "fixed_height":
			photo_suffix += "f"
	photo_suffix += ".jpg"
	result = cache_base(path, album, True) + photo_suffix
	
	return result
def video_cache_name(album, path):
	return cache_base(path, album, True) + "_transcoded_" + Options.config['video_transcode_bitrate'] + ".mp4"
def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))
