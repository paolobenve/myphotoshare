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
	if len(path) == 0:
		path = "root"
	else:
		path = trim_base(path).replace('/', Options.config['cache_folder_separator']).replace(' ', '_').replace('(', '').replace('&', '').replace(',', '').replace(')', '').replace('#', '').replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace('_-_', '-').lower()
		while path.find("--") != -1:
			path = path.replace("--", "-")
		while path.find("__") != -1:
			path = path.replace("__", "_")
	return path
def json_name(path):
	return cache_base(path) + ".json"
def image_cache(path, size):
	suffix = "_" + str(size)
	if size == Options.config['album_thumb_size']:
		suffix += "a"
		if Options.config['album_thumb_type'] == "square": 
			suffix += "s"
		elif Options.config['album_thumb_type'] == "fit": 
			suffix += "f"
	elif size == Options.config['media_thumb_size']:
		suffix += "t"
		if Options.config['media_thumb_type'] == "square": 
			suffix += "s"
		elif Options.config['media_thumb_type'] == "fixed_height": 
			suffix += "f"
	suffix += ".jpg"
	result = cache_base(path, True) + suffix
	return result
def cache_subdir(path):
	if Options.config['subdir_method'] == "md5":
		subdir = hashlib.md5(path).hexdigest()[:2]
	elif Options.config['subdir_method'] == "folder":
		if path.find("/") == -1:
			subdir = "__"
		else:
			subdir = path[:path.find("/")][:2]
	else:
		subdir = ""
	return subdir
def path_with_subdir(path, size):
	subdir = cache_subdir(path)
	if subdir:
		cache_path_with_subdir = os.path.join(Options.config['cache_path'], subdir)
		if not os.path.exists(cache_path_with_subdir):
			os.makedirs(cache_path_with_subdir)
		image_cache_with_subdir = os.path.join(subdir, image_cache(path, size))
	else:
		image_cache_with_subdir = image_cache(path, size)
	return image_cache_with_subdir
def video_cache_with_subdir(path):
	subdir = cache_subdir(path)
	if subdir:
		cache_path_with_subdir = os.path.join(Options.config['cache_path'], subdir)
		if not os.path.exists(cache_path_with_subdir):
			os.makedirs(cache_path_with_subdir)
		video_cache_with_subdir = os.path.join(subdir, video_cache(path))
	else:
		video_cache_with_subdir = video_cache(path)
	return video_cache_with_subdir
def video_cache(path):
	return cache_base(path, True) + "_transcoded.mp4"
def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))
