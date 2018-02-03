# -*- coding: utf-8 -*-
# do not remove previous line: it's not a comment!

# @python2
from __future__ import print_function

import os.path
from datetime import datetime
import hashlib
import Options

def trim_base_custom(path, base):
	if path.startswith(base):
		path = path[len(base):]
	if path.startswith('/'):
		path = path[1:]
	return path

def remove_album_path(path):
	return trim_base_custom(path, Options.config['album_path'])

# find a file in file system, from https://stackoverflow.com/questions/1724693/find-a-file-in-python
def find(name):
	for root, dirs, files in os.walk('/'):
		if name in files:
			return os.path.join(root, name)
	return False

def find_in_usr_share(name):
	for root, dirs, files in os.walk('/usr/share/'):
		if name in files:
			return os.path.join(root, name)
	return False


def remove_folders_marker(path):
	marker_position = path.find(Options.config['folders_string'])
	if marker_position == 0:
		path = path[len(Options.config['folders_string']):]
		if len(path) > 0:
			path = path[1:]
	return path

def cache_base(path, filepath=False):
	if not filepath:
		path = remove_album_path(path)
	if path:
		path = path.replace('/', Options.config['cache_folder_separator']).replace(' ', '_').replace('+', '_').replace('(', '').replace('&', '').replace(',', '').replace(')', '').replace('#', '').replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace('_-_', '-').lower()
		while path.find("--") != -1:
			path = path.replace("--", "-")
		while path.find("__") != -1:
			path = path.replace("__", "_")
	else:
		path = "root"
	return path

def photo_cache_name(photo, size, thumb_type = "", mobile_bigger = False):
	# this function is used for video thumbnails too
	photo_suffix = "_"
	actual_size = size
	if mobile_bigger:
		actual_size = int(actual_size * Options.config['mobile_thumbnail_factor'])
	photo_suffix += str(actual_size)
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
	result = photo.cache_base + photo_suffix

	return result

def video_cache_name(video):
	return video.cache_base + "_transcoded_" + Options.config['video_transcode_bitrate'] + "_" + str(Options.config['video_crf']) + ".mp4"

def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))

def checksum(path):
	block_size = 65536
	hasher = hashlib.md5()
	with open(path, 'rb') as afile:
		buf = afile.read(block_size)
		while len(buf) > 0:
			hasher.update(buf)
			buf = afile.read(block_size)
	return hasher.hexdigest()

def square_thumbnail_sizes():
	# collect all the square sizes needed

	# album size: square thumbnail are generated anyway, because they are needed by the code that generates composite images for sharing albums
	# the second element in the tuple il mobile_bigger
	square_sizes = [(Options.config['album_thumb_size'], False)]
	if Options.config['album_thumb_type'] == "square":
		if Options.config['mobile_thumbnail_factor'] > 1:
			square_sizes.append((Options.config['album_thumb_size'], True))
	if Options.config['media_thumb_type'] == "square":
		square_sizes.append((Options.config['media_thumb_size'], False))
		if Options.config['mobile_thumbnail_factor'] > 1:
			square_sizes.append((Options.config['media_thumb_size'], True))
	# sort sizes descending
	square_sizes = sorted(square_sizes, key=modified_size, reverse=True)
	return square_sizes

def modified_size(tuple):
	(size, mobile_bigger) = tuple
	if mobile_bigger:
		return  int(round(size * Options.config['mobile_thumbnail_factor']))
	else:
		return size

def thumbnail_types_and_sizes():
	# collect all the square sizes needed
	# album size: square thumbnail are generated anyway, because they are needed by the code that generates composite images for sharing albums
	_thumbnail_types_and_sizes = {
		"square": square_thumbnail_sizes(),
		"fit": [(Options.config['album_thumb_size'], True), (Options.config['album_thumb_size'], False)],
		"fixed_height": [(Options.config['media_thumb_size'], True), (Options.config['media_thumb_size'], False)]
	}

	return _thumbnail_types_and_sizes
