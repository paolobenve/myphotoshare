# -*- coding: utf-8 -*-
# do not remove previous line: it's not a comment!

# @python2
from __future__ import print_function
from __future__ import division

from datetime import datetime
import os

import Options


def message(category, text, verbose=0):
	"""
	Print a line of logging `text` if the `verbose` level is lower than the verbosity level
	defined in the configuration file. This message is prefixed by the `category` text and
	timing information.

	The format of the log line is
	```
      2220 2018-02-04 17:17:38.517966   |  |--[album saved]     /var/www/html/myphotoshare/cache/_bd-2017-09-24.json
      ^    ^                                   ^                ^
	  |    |                                   |                text
	  |    |                                   indented category
      |    date and time
	  microseconds
	```

	Elapsed time for each category is cumulated and can be printed with `report_times`.

	Verbosity levels:
	- 0 = fatal errors only
	- 1 = add non-fatal errors
	- 2 = add warnings
	- 3 = add info
	- 4 = add more info
	"""

	try:
		message.max_verbose = Options.config['max_verbose']
	except KeyError:
		message.max_verbose = 10
	except AttributeError:
		message.max_verbose = 0

	if verbose <= message.max_verbose:
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
		print((9 - len(microseconds)) * " ", microseconds, "%s %s%s[%s]%s%s" % (now.isoformat(' '), max(0, message.level) * "  |", sep, str(category), max(1, (45 - len(str(category)))) * " ", str(text)))


"""
The verbosity level as defined by the user in the configuration file.
"""
message.max_verbose = 0


"""
The identation level printed by the message function.
"""
message.level = 0


def next_level(verbose=0):
	"""
	Increase the indentation level of log messages.
	"""
	if verbose <= message.max_verbose:
		message.level += 1


def back_level(verbose=0):
	"""
	Decrease the indentation level of log messages.
	"""
	if verbose <= message.max_verbose:
		message.level -= 1

# find a file in file system, from https://stackoverflow.com/questions/1724693/find-a-file-in-python
def find(name):
	for root, dirnames, files in os.walk('/'):
		dirnames[:] = [dir for dir in dirnames if not os.path.ismount(os.path.join(root, dir))]
		if name in files:
			return os.path.join(root, name)
	return False

def find_in_usr_share(name):
	for root, dirnames, files in os.walk('/usr/share/'):
		dirnames[:] = [dir for dir in dirnames if not os.path.ismount(os.path.join(root, dir))]
		if name in files:
			return os.path.join(root, name)
	return False


def time_totals(time):
	seconds = int(round(time / 1000000))
	if time <= 1800:
		_total_time = str(int(round(time))) + " μs"
	elif time <= 1800:
		_total_time = str(int(round(time / 1000))) + "    ms"
	else:
		_total_time = str(seconds) + "       s "

	_total_time_m, _total_time_s = divmod(seconds, 60)
	_total_time_h, _total_time_m = divmod(_total_time_m, 60)

	_total_time_hours = str(_total_time_h) + "h " if _total_time_h else ""
	_total_time_minutes = str(_total_time_m) + "m " if _total_time_m else ""
	_total_time_seconds = str(_total_time_s) + "s" if _total_time_m else ""
	_total_time_unfolded = _total_time_hours + _total_time_minutes + _total_time_seconds
	if _total_time_unfolded:
		_total_time_unfolded = "= " + _total_time_unfolded
	return (_total_time, _total_time_unfolded)

def report_times(final):
	"""
	Print a report with the total time spent on each `message()` categories and the number of times
	each category has been called. This report can be considered a poor man's profiler as it cumulates
	the number of times the `message()` function has been called instead of the real excution time of
	the code.
	The report includes a section at the end with the number of media processed by type and list the
	albums where media is not geotagged or has no EXIF.
	"""

	try:
		# detect uninitialized variable
		report_times.num_media_in_tree
	except AttributeError:
		# calculate the number of media in the album tree: it will be used in order to guess the execution time
		special_files = [Options.config['exclude_tree_marker'], Options.config['exclude_files_marker'], Options.config['metadata_filename']]
		message("counting media in albums...", "", 4)
		report_times.num_media_in_tree = sum([len([file for file in files if file[:1] != '.' and file not in special_files]) for dirpath, dirs, files in os.walk(Options.config['album_path']) if dirpath.find('/.') == -1])
		next_level()
		message("media in albums counted", str(report_times.num_media_in_tree), 4)
		back_level()

	print()
	print((50 - len("message")) * " ", "message", (15 - len("total time")) * " ", "total time", (15 - len("counter")) * " ", "counter", (20 - len("average time")) * " ", "average time")
	print()
	time_till_now = 0
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

		time_till_now += time

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

	(_time_till_now, _time_till_now_unfolded) = time_totals(time_till_now)
	print()
	print((50 - len("time taken till now")) * " ", "time taken till now", (18 - len(_time_till_now)) * " ", _time_till_now, "     ", _time_till_now_unfolded)
	num_media = Options.num_video + Options.num_photo

	_num_media = str(num_media)
	# do not print the report if browsing hasn't been done
	if num_media > 0 and report_times.num_media_in_tree > 0:
		# normal run, print final report about photos, videos, geotags, exif dates
		try:
			time_missing = time_till_now / num_media * report_times.num_media_in_tree - time_till_now
			if time_missing >= 0:
				(_time_missing, _time_missing_unfolded) = time_totals(time_missing)
				print((50 - len("total time missing")) * " ", "total time missing", (18 - len(_time_missing)) * " ", _time_missing, "     ", _time_missing_unfolded)
			time_total = time_till_now + time_missing
			if time_total > 0:
				(_time_total, _time_total_unfolded) = time_totals(time_total)
				print((50 - len("total time")) * " ", "total time", (18 - len(_time_total)) * " ", _time_total, "     ", _time_total_unfolded)
		except ZeroDivisionError:
			pass
		print()

		_num_media = str(num_media)
		num_media_processed = Options.num_photo_processed + Options.num_video_processed
		_num_media_processed = str(num_media_processed)
		_num_photo = str(Options.num_photo)
		_num_photo_processed = str(Options.num_photo_processed)
		_num_photo_geotagged = str(Options.num_photo_geotagged)
		_num_photo_with_exif_date = str(Options.num_photo_with_exif_date)
		_num_photo_without_geotags = str(Options.num_photo - Options.num_photo_geotagged)
		_num_photo_without_exif_date = str(Options.num_photo - Options.num_photo_with_exif_date)
		_num_video = str(Options.num_video)
		_num_video_processed = str(Options.num_video_processed)
		max_digit = len(_num_media)

		media_count_and_time = "Media    " + ((max_digit - len(_num_media)) * " ") + _num_media + ' / ' + str(report_times.num_media_in_tree) + ' (' + str(int(num_media * 1000 / report_times.num_media_in_tree) / 10) + '%)'
		if num_media:
			media_count_and_time += ",      " + str(int(time_till_now / 1000000 / num_media * 1000) / 1000) + " s/media"
		print(media_count_and_time)
		media_count_and_time = "                  processed " + ((max_digit - len(_num_media_processed)) * " ") + _num_media_processed
		if num_media_processed and num_media_processed != num_media:
			media_count_and_time += ",      " + str(int(time_till_now / num_media_processed / 10000) / 100) + " s/processed media"
		print(media_count_and_time)
		print("- Videos " + ((max_digit - len(_num_video)) * " ") + _num_video)
		print("                  processed " + ((max_digit - len(_num_video_processed)) * " ") + _num_video_processed)
		print("- Photos " + ((max_digit - len(_num_photo)) * " ") + _num_photo)
		print("                  processed " + ((max_digit - len(_num_photo_processed)) * " ") + _num_photo_processed)
		print("                                  geotagged         " + ((max_digit - len(_num_photo_geotagged)) * " ") + _num_photo_geotagged)
		print("                                  whithout geotags  " + ((max_digit - len(_num_photo_without_geotags)) * " ") + _num_photo_without_geotags)
		if final and Options.num_photo_processed != Options.num_photo_geotagged:
			for photo in Options.photos_without_geotag:
				print("                                      - " + photo)
		print("                                  with exif date    " + ((max_digit - len(_num_photo_with_exif_date)) * " ") + _num_photo_with_exif_date)
		print("                                  without exif date " + ((max_digit - len(_num_photo_without_exif_date)) * " ") + _num_photo_without_exif_date)
		if final and Options.num_photo_processed != Options.num_photo_with_exif_date:
			for photo in Options.photos_without_exif_date:
				print("                                      - " + photo)
		print()
