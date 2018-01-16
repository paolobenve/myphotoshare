#!/usr/bin/python3

# This script downloads alternateNames.zip from geonames.org and prepares the files the scanner needs for using local language names instead of english city names

# Usage:
# ./get_alternate_names.py language_code1 language_code2 language_code3 ...

from __future__ import print_function  # Only needed for Python 2
from fileinput import input
import requests, zipfile, io
import json
import os
import sys

zip_file = "alternateNames.zip"
print()
print("getting " + zip_file + "  from geonames.org and extracting it to file...")
url = "http://download.geonames.org/export/dump/" + zip_file
request = requests.get(url)
if request.status_code != 200:
	print("error getting url, quitting")
else:
	alternate_names = zipfile.ZipFile(io.BytesIO(request.content))
	alternate_names_file_name = "alternateNames.txt"
	alternate_names.extract(alternate_names_file_name)
	print("done!")
	print()

	print("getting known languages list")
	translations_file = "web/js/009-translations.js"
	translations_structure = {}
	with open(translations_file, "rt") as translations_p:
		translations = translations_p.read().splitlines(True)
		translations_json = ''.join(translations[1:])[:-1].replace("\t", "").replace(" ", "").replace("\n", "")[:-1]
		translations_dict = json.loads(translations_json)

	languages = []
	for key, value in list(translations_dict.items()):
		languages.append(key)
	print("got!")
	# add the languages specified as command line arguments
	for i in range(len(sys.argv)):
		if i == 0:
			continue
		if sys.argv[i] not in languages:
			languages.append(sys.argv[i])

	print()

	alt_file_ = "scanner/geonames/alternate_names_"
	file_ = open(alt_file_, "wt")

	file_languages = {}
	for language in languages:
		file_language = alt_file_ + language
		file_languages[language] = open(file_language, "wt")

	print("generating local files...")
	with open(alternate_names_file_name, 'rt') as alternate_names_file:
		for line in alternate_names_file:
			col = line.split('\t')
			# only retain geoname id and name
			essential_line = '\t'.join([col[1], col[3]]) + '\n'
			if col[2] == '':
				file_.write(essential_line)
			for language, file_language in list(file_languages.items()):
				if col[2] == language:
					file_language.write(essential_line)
	print("local files generated!")

	os.remove(alternate_names_file_name)
	os.remove(zip_file)

	file_.close()
	for language, file_language in list(file_languages.items()):
		file_language.close()
