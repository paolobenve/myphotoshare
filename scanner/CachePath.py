import os.path
from datetime import datetime
import hashlib
import Options

max_verbose = 0
def message(category, text, verbose = 0):
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
		print "%s %s%s[%s]%s%s" % (datetime.now().isoformat(), max(0, message.level) * "  |", sep, str(category), max(1, (45 - len(str(category)))) * " ", str(text))

message.level = 0
def next_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level += 1
def back_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level -= 1
def set_cache_path_base(base):
	trim_base.base = base
def untrim_base(path):
	return os.path.join(trim_base.base, path)
def trim_base_custom(path, base):
	if path.startswith(base):
		path = path[len(base):]
	if path.startswith('/'):
		path = path[1:]
	return path
def trim_base(path):
	return trim_base_custom(path, trim_base.base)
def cache_base(path, filepath=False):
	if not filepath:
		path = trim_base(path)
	if path:
		path = path.replace('/', Options.config['cache_folder_separator']).replace(' ', '_').replace('(', '').replace('&', '').replace(',', '').replace(')', '').replace('#', '').replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace('_-_', '-').lower()
		while path.find("--") != -1:
			path = path.replace("--", "-")
		while path.find("__") != -1:
			path = path.replace("__", "_")
	else:
		path = "root"
	return path
def json_name(path):
	return cache_base(path) + ".json"
def photo_cache_name(path, size, thumb_type = ""):
	# this function is used for video thumbnails too
	suffix = "_" + str(size)
	if size == Options.config['album_thumb_size']:
		suffix += "a"
		if thumb_type == "square":
			suffix += "s"
		elif thumb_type == "fit":
			suffix += "f"
	elif size == Options.config['media_thumb_size']:
		suffix += "t"
		if thumb_type == "square":
			suffix += "s"
		elif thumb_type == "fixed_height":
			suffix += "f"
	suffix += ".jpg"
	result = cache_base(path, True) + suffix
	return result
def video_cache_name(path):
	return cache_base(path, True) + "_transcoded_" + str(Options.config['video_transcode_bitrate']) + ".mp4"
def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))
