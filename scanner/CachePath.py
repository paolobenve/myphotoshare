# -*- coding: utf-8 -*-
# do not remove previous line: it's not a comment!

# @python2
from __future__ import print_function
from __future__ import unicode_literals

import os.path
from datetime import datetime
import hashlib
import unicodedata
import unidecode

import Options

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

def remove_non_alphabetic_characters(phrase):
	# normalize unicode, see https://stackoverflow.com/questions/16467479/normalizing-unicode
	phrase = unicodedata.normalize('NFC', phrase)
	# convert non-alphabetic characters to spaces
	new_phrase = ''
	for c in phrase:
		new_phrase += c if (c.isalpha() or c in Options.config['unicode_combining_marks']) else " "
	# normalize multiple, leading and trailing spaces
	phrase = ' '.join(new_phrase.split())

	return phrase

def remove_all_but_alphanumeric_chars_dashes_slashes_dots(phrase):
	# normalize unicode, see https://stackoverflow.com/questions/16467479/normalizing-unicode
	phrase = unicodedata.normalize('NFC', phrase)
	# convert non-alphabetic characters to spaces
	new_phrase = ''
	for c in phrase:
		new_phrase += c if (c in ['-', '/', '.'] or c.isalpha() or c.isdecimal() or c in Options.config['unicode_combining_marks']) else " "
	# normalize multiple, leading and trailing spaces
	phrase = ' '.join(new_phrase.split())

	return phrase

def remove_digits(phrase):
	# remove digits
	phrase = "".join(["" if c.isdecimal() else c for c in phrase])
	# normalize multiple, leading and trailing spaces
	phrase = ' '.join(phrase.split())

	return phrase

def remove_accents(phrase):
	# strip accents (from http://nullege.com/codes/show/src@d@b@dbkit-0.2.2@examples@notary@notary.py/38/unicodedata.combining)
	normalized_phrase = unicodedata.normalize('NFKD', phrase)
	accentless_phrase = ''
	for c in normalized_phrase:
		if c not in Options.config['unicode_combining_marks']:
			accentless_phrase += c

	return accentless_phrase

def switch_to_lowercase(phrase):
	phrase = phrase.lower()

	return phrase

def convert_to_ascii_only(phrase):
	# convert accented characters to ascii, from https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string

	# the following line generate a problem with chinese, because unidecode translate every ideogram with a word
	#phrase = unidecode.unidecode(phrase)

	words = phrase_to_words(phrase)
	decoded_words = []
	for word in words:
		# removing spaces is necessary with chinese: every ideogram is rendered with a word
		decoded_words.append(unidecode.unidecode(word).strip().replace(' ', '_'))

	phrase = ' '.join(decoded_words)

	return phrase

def phrase_to_words(phrase):
	# splits the phrase into a list
	return list(phrase.split(' '))

def photo_cache_name(photo, size, thumb_type="", mobile_bigger=False):
	# this function is used for video thumbnails too
	photo_suffix = Options.config['cache_folder_separator']
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
	if size == Options.config['media_thumb_size']:
		photo_suffix += "t"
		if thumb_type == "square":
			photo_suffix += "s"
		elif thumb_type == "fixed_height":
			photo_suffix += "f"
	photo_suffix += ".jpg"
	result = photo.cache_base + photo_suffix

	return result


def video_cache_name(video):
	return video.cache_base + Options.config['cache_folder_separator'] + "transcoded_" + Options.config['video_transcode_bitrate'] + "_" + str(Options.config['video_crf']) + ".mp4"

def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))

def last_modification_time(path):
	maximum = 0
	for root, dirs, files in os.walk(path):
		maximum = max(maximum, os.path.getmtime(root))
		if files:
			maximum = max(maximum, max(os.path.getmtime(os.path.join(root, file)) for file in files))
	last_mtime = datetime.fromtimestamp(maximum)
	return last_mtime

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
	# the second element in the tuple_arg is `mobile_bigger`.
	square_sizes = [(Options.config['album_thumb_size'], False)]
	if Options.config['mobile_thumbnail_factor'] > 1:
		square_sizes.append((Options.config['album_thumb_size'], True))
	square_sizes.append((Options.config['media_thumb_size'], False))
	if Options.config['mobile_thumbnail_factor'] > 1 and (Options.config['media_thumb_size'], True) not in square_sizes:
		square_sizes.append((Options.config['media_thumb_size'], True))
	# sort sizes descending
	square_sizes = sorted(square_sizes, key=modified_size, reverse=True)
	return square_sizes

def modified_size(tuple_arg):
	(size, mobile_bigger) = tuple_arg
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
