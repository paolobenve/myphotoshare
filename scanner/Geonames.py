# original from https://gist.github.com/Markbnj/e1541d15699c4d2d8c98

import requests
import json
import Options


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

		def __init__(self):
			GEONAMES_USER = Options.config['geonames_user']
			GEONAMES_LANGUAGE = Options.config['geonames_language']
			self._base_feature_url = "{}getJSON?geonameId={{}}&username={}&style=full&lang={}".format(self.GEONAMES_API, GEONAMES_USER, GEONAMES_LANGUAGE)
			self._base_nearby_url = "{}findNearbyJSON?lat={{}}&lng={{}}{{}}&cities=cities5000&username={}&lang={}".format(self.GEONAMES_API, GEONAMES_USER, GEONAMES_LANGUAGE)
			self._base_neighbourhood_url = "{}neighbourhoodJSON?lat={{}}&lng={{}}&username={}&lang={}".format(self.GEONAMES_API, GEONAMES_USER, GEONAMES_LANGUAGE)

		def lookup_feature(self, geoname_id):
				"""
				Looks up a feature based on its geonames id
				"""
				url = self._base_feature_url.format(geoname_id)
				response = requests.get(url)
				return self._decode_feature(response.text)

		def _decode_feature(self, response_text):
				"""
				Decodes the response from geonames.org feature lookup and
				returns the properties in a dict.
				"""
				raw_result = json.loads(response_text)

				if 'status' in raw_result:
						raise Exception("Geonames: call returned status {}".format(raw_result['status']['value']))

				result = dict(
						geoname_id=raw_result['geonameId'],
						name=raw_result['name'],
						country_name=raw_result['countryName'],
						country_code=raw_result['countryCode'],
						admin_name_1=raw_result['adminName1'],
						admin_code_1=raw_result['adminCode1'],
						toponym_name=raw_result['toponymName']
				)
				return result

		def lookup_nearby_place(self, latitude, longitude, feature_class='P', feature_code=None):
				"""
				Looks up places near a specific geographic location, optionally
				filtering for feature class and feature code.
				"""
				feature_filter = ''
				if feature_class:
						feature_filter += "&featureClass={}".format(feature_class)
				if feature_code:
						feature_filter += "&featureCode={}".format(feature_code)

				url = self._base_nearby_url.format(latitude, longitude, feature_filter)
				response = requests.get(url)
				result = self._decode_nearby_place(response.text)
				return result

		def _decode_nearby_place(self, response_text):
				"""
				Decodes the response from the geonames nearby place lookup and
				returns the properties in a dict.
				"""
				raw_result = json.loads(response_text)
				result = None

				if 'status' not in raw_result and len(raw_result['geonames']) > 0:
						geoname = raw_result['geonames'][0]
						result = dict(
								country_name=geoname['countryName'],
								country_code=geoname['countryCode'],
								admin_name_1=geoname['adminName1'],
								admin_code_1=geoname['adminCode1']
								name=geoname['name'],
								geoname_id=geoname['geonameId'],
								latitude=geoname['lat'],
								longitude=geoname['lng'],
								distance=geoname['distance'],
						)
				return result

		def lookup_neighbourhood(self, latitude, longitude):
				"""
				Finds the neighborhood record for a specific geographic location.
				"""
				url = self._base_neighbourhood_url.format(latitude, longitude)
				response = requests.get(url)
				return self._decode_neighbourhood(response.text)

		def _decode_neighbourhood(self, response_text):
				raw_result = json.loads(response_text)
				result = None

				if 'status' not in raw_result:
						result = dict(
								country_name=raw_result['neighbourhood']['countryName'],
								country_code=raw_result['neighbourhood']['countryCode'],
								admin_name_1=raw_result['neighbourhood']['adminName1'],
								admin_code_1=raw_result['neighbourhood']['adminCode1'],
								admin_name_2=raw_result['neighbourhood']['adminName2'],
								city=raw_result['neighbourhood']['city'],
								name=raw_result['neighbourhood']['name']
						)
				return result
