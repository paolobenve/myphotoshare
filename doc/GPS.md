# Geolocation of media

MyPhotoShare extracts geotags from media files to locate where your photos were taken. It then uses the latitude and longitude position to regroup the pictures by place names and offers geographic browsing of the albums. It can even display a map indicating where the photo was shot.


## Geonames database

MyPhotoShare comes with a database of place names originating from [GeoNames.org](http://www.geonames.org/) but it can also be configured to retrieve place names online from web services (look at the `get_geonames_online` option in config file).

To update the database, run the `get_alternate_names.py` script indicating the languages you want to retrieve, like for instance:

```bash
$ ./bin/get_alternate_names.py ru
```

This script will download the names of countries, regions and cities/towns in the languages known by MyPhotoShare adding the languages specified as arguments.


## Overloading geolocation

There are situations where you need to overload automatic geolocation for your media:
* Sometimes, the name referenced by GeoNames.org is not correct in your locale. For example, in French, the French region Corsica is named Corse and not Corsica as reported by GeoNames.
* Your media is not geotagged (you don't have a GPS camera) but you know where the photos or videos were shot.
* MyPhotoShare distance calculation algorithms tags your media with the wrong name. Geonaming uses only distances and does not knows about borders...

In these cases, you can correct the geographic information used by MyPhotoShare using the `album.ini` user defined metadata. Particularly look at options `latitude`, `longitude`, `country_name`, `region_name` and `place_name`. Remember that when you use these options, the original media is not changed but only the information used by MyPhotoShare. Also the `country_name`, `region_name` and `place_name` are used by MyPhotoShare **only if** `latitude` and `longitude` are defined.

More information is available in [Metadata](Metadata.md).
