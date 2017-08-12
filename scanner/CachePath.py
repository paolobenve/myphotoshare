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
		#~ milliseconds = time_elapsed.microseconds / 1000 + time_elapsed.seconds 
		milliseconds = int(time_elapsed.total_seconds() * 1000)
		if milliseconds == 0:
			milliseconds = ""
		else:
			try:
				Options.elapsed_times[category] += milliseconds
				Options.elapsed_times_counter[category] += 1
			except KeyError:
				Options.elapsed_times[category] = milliseconds
				Options.elapsed_times_counter[category] = 1
			milliseconds = str(milliseconds)
		print (5 - len(milliseconds)) * " ", milliseconds, "%s %s%s[%s]%s%s" % (now.isoformat(' '), max(0, message.level) * "  |", sep, str(category), max(1, (45 - len(str(category)))) * " ", str(text))

def report_times():
	print
	print (50 - len("message")) * " ", "message", (15 - len("total time")) * " ", "total time", (15 - len("counter")) * " ", "counter", (20 - len("average time")) * " ", "average time"
	print
	total_time = 0
	for category in sorted(Options.elapsed_times, key=Options.elapsed_times.get, reverse=True):
		time = int(round(Options.elapsed_times[category]))
		total_time += time
		if time == 0:
			_time = ""
		elif time <= 1800:
			_time = str(time) + " ms"
		else:
			_time = str(int(round(time / 1000))) + "    s "
		counter = str(Options.elapsed_times_counter[category]) + " times"
		average_time = str(int(Options.elapsed_times[category] / Options.elapsed_times_counter[category])) + " ms"
		print (50 - len(category)) * " ", category, (15 - len(_time)) * " ", _time, (15 - len(counter)) * " ", counter, (20 - len(average_time)) * " ", average_time
	if total_time <= 1800:
		_total_time = str(int(round(total_time))) + " ms"
	else:
		_total_time = str(int(round(total_time / 1000))) + "    s "
	print
	print (50 - len("total time")) * " ", "total time", (15 - len(_total_time)) * " ", _total_time
	print
	if Options.num_photo > 0:
		_num_photo = str(Options.num_photo)
	else:
		_num_photo = ""
	if Options.num_photo_processed > 0:
		_num_photo_processed = str(Options.num_photo_processed)
	else:
		_num_photo_processed = ""
	if Options.num_video > 0:
		_num_video = str(Options.num_video)
	else:
		_num_video = ""
	if Options.num_video_processed > 0:
		_num_video_processed = str(Options.num_video_processed)
	else:
		_num_photo = ""
	print "Photos: total = ", (10 - len(_num_photo)) * " ", _num_photo, ", processed = ", (10 - len(_num_photo_processed)) * " ", _num_photo_processed
	print "Video : total = ", (10 - len(_num_video)) * " ", _num_video, ", processed = ", (10 - len(_num_video_processed)) * " ", _num_video_processed

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
#~ def json_name(path):
	#~ return cache_base(path) + ".json"
def photo_cache_name(photo, size, thumb_type = ""):
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
	result = photo.cache_base + photo_suffix
	
	return result
def video_cache_name(video):
	return video.cache_base + "_transcoded_" + Options.config['video_transcode_bitrate'] + "_" + str(Options.config['video_crf']) + ".mp4"
def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))
