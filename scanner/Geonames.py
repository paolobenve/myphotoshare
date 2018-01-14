# original from https://gist.github.com/Markbnj/e1541d15699c4d2d8c98
# added code from gottengeography project, https://gitlab.com/robru/gottengeography
# files scanner/geonames/territories.json and scanner/geonames/countries.json from gottengeography project too

import requests
import json
import Options
from CachePath import *
import TreeWalker
import math
import numpy as np
import random
import os
import sys

# For information on endpoints and arguments see the geonames
# API documentation at:
#
#   http://www.geonames.org/export/web-services.html

class Geonames(object):
	"""
	This class provides a client to call certain entrypoints of the geonames
	API.
	"""
	GEONAMES_API = "http://api.geonames.org/"
	# through this cache many calls to geonames web services are saved
	geonames_cache = {}
	# the maximum distance in meters for considering two different coordinates equivalent
	max_distance_meters = 50

	def __init__(self):
		if Options.config['use_geonames_online']:
			self._base_nearby_url = "{}findNearbyJSON?lat={{}}&lng={{}}{{}}&username={}&lang={}".format(self.GEONAMES_API, Options.config['geonames_user'], Options.config['geonames_language'])
		else:
			territories_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", 'scanner/geonames/territories.json')
			countries_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", 'scanner/geonames/countries.json')
			cityfile = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", 'scanner/geonames/cities15000.txt')

			with open(territories_file, 'r') as territories_file_p:
				territories = json.load(territories_file_p)
			with open(countries_file, 'r') as countries_file_p:
				countries = json.load(countries_file_p)

			with open(cityfile, 'r') as cities:
				self.cities = []
				for line in cities:
					col = line.split('\t')
					country_code = col[8]
					state_code = col[10]
					try:
						country = countries[country_code]
					except KeyError:
						country = ''
					try:
						state = territories[country_code + '.' + state_code]
					except KeyError:
						state = ''
					my_line = {
						'city': col[1],
						#'city_alt': col[3].split(','),
						'lat': float(col[4]),
						'long': float(col[5]),
						'country_code': country_code,
						'country': country,
						'state_code': state_code,
						'state': state
					}
					self.cities.append(my_line)

	def lookup_nearby_place(self, latitude, longitude):
		"""
		Looks up places near a specific geographic location, optionally
		filtering for feature class and feature code.
		"""

		for (c_latitude, c_longitude) in Geonames.geonames_cache:
			distance = self.distance_between_coordinates(c_latitude, c_longitude, latitude, longitude)
			if distance < self.max_distance_meters:
				# get it from cache!
				result = Geonames.geonames_cache[(c_latitude, c_longitude)]
				next_level()
				message("geoname got from cache", "", 5)
				back_level()
				# add to cache only if not too closed to existing point
				if distance > self.max_distance_meters / 10.0:
					Geonames.geonames_cache[(latitude, longitude)] = result
				return result

		if Options.config['use_geonames_online']:
			# get country, region (state for federal countries), and place
			url = self._base_nearby_url.format(latitude, longitude)
			response = requests.get(url)
			result = self._decode_nearby_place(response.text)
			next_level()
			message("geoname got from geonames.org online", "", 5)
			back_level()
		else:
			# get country, region (state for federal countries), and place
			result = min([city for city in cities], key=self.distance_between_coordinates(city.lat, city.long, latitude, longitude))
			next_level()
			message("geoname got from geonames files on disk", "", 5)
			back_level()

		# add to cache
		Geonames.geonames_cache[(latitude, longitude)] = result

		return result

	def _decode_nearby_place(self, response_text):
		"""
		Decodes the response from the geonames nearby place lookup and
		returns the properties in a dict.
		"""
		raw_result = json.loads(response_text)
		result = {}

		if 'status' not in raw_result and len(raw_result['geonames']) > 0:
				geoname = raw_result['geonames'][0]
				correspondence = {
					'country_name': 'countryName',
					'country_code': 'countryCode',
					'region_name': 'adminName1',
					'region_code': 'adminCode1',
					'place_name': 'name',
					'place_code': 'geonameId',
					'latitude': 'lat',
					'longitude': 'lng',
					'distance': 'distance'
				}
				for index in correspondence:
					# vatican places don't have region fields, and perhaps others fields could not exist
					if correspondence[index] in geoname:
						result[index] = geoname[correspondence[index]]
					else:
						if index[-5:] == '_code':
							result[index] = Options.config['unspecified_geonames_code']
						else:
							result[index] = ''
		return result

	def recalculate_mean(self, old_mean, old_len, new_value, new_len = 1):
		return (old_mean * old_len + new_value * new_len) / (old_len + new_len)


	def distance_between_media(self, media1, media2):
		# calculate the distance between the media gps coordinates
		lat1 = media1.latitude
		lon1 = media1.longitude
		lat2 = media2.latitude
		lon2 = media2.longitude

		return self.distance_between_coordinates(lat1, lon1, lat2, lon2)

	def distance_between_coordinates(self, lat1, lon1, lat2, lon2):
		# https://gis.stackexchange.com/questions/61924/python-gdal-degrees-to-meters-without-reprojecting
		# Calculate the great circle distance in meters between two points on the earth (specified in decimal degrees)

		# convert decimal degrees to radians
		r_lon1, r_lat1, r_lon2, r_lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
		# haversine formula
		d_r_lon = r_lon2 - r_lon1
		d_r_lat = r_lat2 - r_lat1
		a = math.sin(d_r_lat / 2.0) ** 2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(d_r_lon / 2.0) ** 2
		c = 2.0 * math.asin(math.sqrt(a))
		m = 6371.0 * c * 1000.0
		return m

	# the following functions implement k-means clustering, got from https://datasciencelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python/
	# the main functino is find_centers
	def cluster_points(self, media_list, mu):
		clusters  = {}
		for media in media_list:
			# bestmukey = min([(i[0], np.linalg.norm(x-mu[i[0]])) for i in enumerate(mu)], key=lambda t:t[1])[0]
			bestmukey = min([(index_and_point[0], np.linalg.norm(self.coordinates(media) - mu[index_and_point[0]])) for index_and_point in enumerate(mu)], key=lambda t:t[1])[0]
			try:
				clusters[bestmukey].append(media)
			except KeyError:
				clusters[bestmukey] = [media]
		return clusters

	def reevaluate_centers(self, mu, clusters):
		newmu = []
		keys = sorted(clusters.keys())
		for k in keys:
			newmu.append(np.mean([self.coordinates(_media) for _media in clusters[k]], axis = 0))
		return newmu

	def has_converged(self, mu, oldmu):
		return set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu])

	def coordinates(self, media):
		return np.array((media.latitude, media.longitude))

	def find_centers(self, media_list, K):
		# Initialize to K random centers
		coordinate_list = [self.coordinates(media) for media in media_list]
		try:
			oldmu = random.sample(coordinate_list, K)
		except ValueError:
			oldmu = coordinate_list
		try:
			mu = random.sample(coordinate_list, K)
		except ValueError:
			mu = coordinate_list
		first_time = True
		while first_time or not self.has_converged(mu, oldmu):
			oldmu = mu
			# Assign all points in media_list to clusters
			clusters = self.cluster_points(media_list, mu)
			# Reevaluate centers
			mu = self.reevaluate_centers(oldmu, clusters)
			if first_time:
				first_time = False
		cluster_list = [cluster for key, cluster in clusters.iteritems()]
		return cluster_list
