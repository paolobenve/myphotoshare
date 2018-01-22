# -*- coding: utf-8 -*-
# do not remove previous line: it's not a comment!

from __future__ import print_function

import os.path
from datetime import datetime
from datetime import timedelta
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
		now = datetime.now()
		time_elapsed = now - Options.last_time
		Options.last_time = now
		microseconds = int(time_elapsed.total_seconds() * 1000000)
		if microseconds == 0:
			microseconds = ""
		else:
			try:
				Options.elapsed_times[category] += microseconds
				Options.elapsed_times_counter[category] += 1
			except KeyError:
				Options.elapsed_times[category] = microseconds
				Options.elapsed_times_counter[category] = 1
			microseconds = str(microseconds)
		#print((9 - len(microseconds)) * " ", microseconds, "%s %s%s[%s]%s%s" % (now.isoformat(' '), max(0, message.level) * "  |", sep, str(category), max(1, (45 - len(str(category)))) * " ", str(text)))
		print((9 - len(microseconds)) * " ", microseconds, "%s %s%s[%s]%s%s" % (now.isoformat(' '), max(0, message.level) * "  |", sep, str(category), max(1, (45 - len(str(category)))) * " ", str(text)))

def report_times():
	print()
	print((50 - len("message")) * " ", "message", (15 - len("total time")) * " ", "total time", (15 - len("counter")) * " ", "counter", (20 - len("average time")) * " ", "average time")
	print()
	total_time = 0
	for category in sorted(Options.elapsed_times, key=Options.elapsed_times.get, reverse=True):
		time = int(round(Options.elapsed_times[category]))
		if time == 0:
			_time = ""
		elif time <= 1800:
			_time = str(time) + " μs"
		elif time <= 1800000:
			_time = str(int(round(time / 1000))) + "    ms"
		else:
			_time = str(int(round(time / 1000000))) + "       s "

		total_time += time

		counter = str(Options.elapsed_times_counter[category]) + " times"

		average_time = int(Options.elapsed_times[category] / Options.elapsed_times_counter[category])
		if average_time == 0:
			_average_time = ""
		elif average_time <= 1800:
			_average_time = str(average_time) + " μs"
		elif average_time <= 1800000:
			_average_time = str(int(round(average_time / 1000))) + "    ms"
		else:
			_average_time = str(int(round(average_time / 1000000))) + "       s "
		print((50 - len(category)) * " ", category, (18 - len(_time)) * " ", _time, (15 - len(counter)) * " ", counter, (20 - len(_average_time)) * " ", _average_time)
	if total_time <= 1800:
		_total_time = str(int(round(total_time))) + " μs"
	elif total_time <= 1800:
		_total_time = str(int(round(total_time / 1000))) + "    ms"
	else:
		_total_time = str(int(round(total_time / 1000000))) + "       s "
	print()
	print((50 - len("total time")) * " ", "total time", (18 - len(_total_time)) * " ", _total_time)
	print()
	_num_media		= str(Options.num_video + Options.num_photo)
	_num_media_processed	= str(Options.num_photo_processed + Options.num_video_processed)
	_num_photo		= str(Options.num_photo)
	_num_photo_processed	= str(Options.num_photo_processed)
	_num_photo_geotagged	= str(Options.num_photo_geotagged)
	_num_photo_with_exif_date	= str(Options.num_photo_with_exif_date)
	_num_photo_without_geotags = str(Options.num_photo - Options.num_photo_geotagged)
	_num_photo_without_exif_date = str(Options.num_photo - Options.num_photo_with_exif_date)
	_num_video		= str(Options.num_video)
	_num_video_processed	= str(Options.num_video_processed)
	max_digit = len(_num_media)
	print("Media    " + ((max_digit - len(_num_media)) * " ") + _num_media)
	print("                  processed " + ((max_digit - len(_num_media_processed)) * " ") + _num_media_processed)
	print("- Videos " + ((max_digit - len(_num_video)) * " ") + _num_video)
	print("                  processed " + ((max_digit - len(_num_video_processed)) * " ") + _num_video_processed)
	print("- Photos " + ((max_digit - len(_num_photo)) * " ") + _num_photo)
	print("                  processed " + ((max_digit - len(_num_photo_processed)) * " ") + _num_photo_processed)
	print("                                  geotagged        " + ((max_digit - len(_num_photo_geotagged)) * " ") + _num_photo_geotagged)
	print("                                  whithout geotags " + ((max_digit - len(_num_photo_without_geotags)) * " ") + _num_photo_without_geotags)
	if Options.num_photo_processed != Options.num_photo_geotagged:
		for photo in Options.photos_without_geotag:
			print("                                      - " + photo)
	print("                                 with exif date    " + ((max_digit - len(_num_photo_with_exif_date)) * " ") + _num_photo_with_exif_date)
	print("                                 without exif date " + ((max_digit - len(_num_photo_without_exif_date)) * " ") + _num_photo_without_exif_date)
	if Options.num_photo_processed != Options.num_photo_with_exif_date:
		for photo in Options.photos_without_exif_date:
			print("                                      - " + photo)

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

# find a file in file system, from https://stackoverflow.com/questions/1724693/find-a-file-in-python
def find(name):
	message("finding file in file system...", name, 4)
	for root, dirs, files in os.walk('/'):
		if name in files:
			return os.path.join(root, name)
	message("file found in file system", name, 4)



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
	_thumbnail_types_and_sizes = {"square": square_thumbnail_sizes()}

	if Options.config['album_thumb_type'] == "fit":
		_thumbnail_types_and_sizes[Options.config['album_thumb_type']] = [(Options.config['album_thumb_size'], True), (Options.config['album_thumb_size'], False)]
	if Options.config['media_thumb_type'] == "fixed_height":
		_thumbnail_types_and_sizes[Options.config['media_thumb_type']] = [(Options.config['media_thumb_size'], True), (Options.config['media_thumb_size'], False)]

	return _thumbnail_types_and_sizes
