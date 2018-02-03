# -*- coding: utf-8 -*-
# do not remove previous line: it's not a comment!

# @python2
from __future__ import print_function

from datetime import datetime
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
		max_verbose = 10
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

message.level = 0

def next_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level += 1

def back_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level -= 1

def report_times(final):
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

	seconds = int(round(total_time / 1000000))
	if total_time <= 1800:
		_total_time = str(int(round(total_time))) + " μs"
	elif total_time <= 1800:
		_total_time = str(int(round(total_time / 1000))) + "    ms"
	else:
		_total_time = str(seconds) + "       s "

	_total_time_m, _total_time_s = divmod(seconds, 60)
	_total_time_h, _total_time_m = divmod(_total_time_m, 60)

	_total_time_hours = str(_total_time_h) + "h " if _total_time_h else ""
	_total_time_minutes = str(_total_time_m) + "m " if _total_time_m else ""
	_total_time_seconds = str(_total_time_s) + "s" if _total_time_m else ""
	if _total_time_seconds:
		_total_time_seconds = "= " + _total_time_seconds
	print()
	print((50 - len("total time")) * " ", "total time", (18 - len(_total_time)) * " ", _total_time, "     ", _total_time_hours + _total_time_minutes + _total_time_seconds)
	print()
	num_media = Options.num_video + Options.num_photo
	_num_media		= str(num_media)
	num_media_processed = Options.num_photo_processed + Options.num_video_processed
	_num_media_processed	= str(num_media_processed)
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
	if num_media:
		print("                                                              " + str(int(total_time / num_media / 10000) / 100) + " s/media")
	print("                  processed " + ((max_digit - len(_num_media_processed)) * " ") + _num_media_processed)
	if num_media_processed and num_media_processed != num_media:
		print("                                                              " + str(int(total_time / num_media_processed / 10000) / 100) + " s/processed media")
	print("- Videos " + ((max_digit - len(_num_video)) * " ") + _num_video)
	print("                  processed " + ((max_digit - len(_num_video_processed)) * " ") + _num_video_processed)
	print("- Photos " + ((max_digit - len(_num_photo)) * " ") + _num_photo)
	print("                  processed " + ((max_digit - len(_num_photo_processed)) * " ") + _num_photo_processed)
	print("                                  geotagged        " + ((max_digit - len(_num_photo_geotagged)) * " ") + _num_photo_geotagged)
	print("                                  whithout geotags " + ((max_digit - len(_num_photo_without_geotags)) * " ") + _num_photo_without_geotags)
	if final and Options.num_photo_processed != Options.num_photo_geotagged:
		for photo in Options.photos_without_geotag:
			print("                                      - " + photo)
	print("                                  with exif date    " + ((max_digit - len(_num_photo_with_exif_date)) * " ") + _num_photo_with_exif_date)
	print("                                  without exif date " + ((max_digit - len(_num_photo_without_exif_date)) * " ") + _num_photo_without_exif_date)
	if final and Options.num_photo_processed != Options.num_photo_with_exif_date:
		for photo in Options.photos_without_exif_date:
			print("                                      - " + photo)
	print()
