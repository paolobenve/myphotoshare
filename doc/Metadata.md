# Metadata

## EXIF metadata of images and videos
The scanner retrieve EXIF matadata from photos. This metadata is accessible from the JavaScript in the gallery and is displayed on-demand.

### Metadata displayed
For images, if available in EXIF/IPTC/XMP:
* Image size
* Image orientation
* Camera make
* Camera model
* Aperture
* FNumber
* Focal length
* ISO speed rating
* ISO
* Photographic sensitivity
* Exposure time
* Flash
* Light source
* Exposure program
* Spectral sensitivity
* Metering mode
* Sensing method
* Scene capture type
* Subject distance range
* Exposure compensation
* Exposure bias value
* Date/Time, from DateTimeOriginal if available or DateTime
* Latitude if geotagged
* Longitude if geotagged

For video, depending on codec:
* Size, height and width
* Duration
* Rotation
* Original size


## User defined metadata in album.ini files
The user can overwrite existing metadata or complement missing metadata using `album.ini` files.

To do so, place a file name `album.ini` in the directory containing the picture files. This file follows the traditional syntax for configuration files as defined in [Python ConfigParser documentation](https://docs.python.org/3/library/configparser.html). Define a section named with the name of the media file you want to change the metadata. Or you can use the special section `[DEFAULT]` to define values that apply to all media in the directory. The special section `[album]` allows to define metadata for the album itself.

In a section, you can then set metadata values that will apply for the media file, the album or all media files. The values in the media files are not changed in the files but overloaded by the values specified in `album.ini` by the scanner script and stored in the JSON files used by the web application.

Supported metadata selectors are:
* `title`: To give a title to the photo, video or album. For the moment, this information is only displayed in the Metadata drawer window, but the goal would be to replace the filename used as caption.
* `description`: A long description of the media. The description can span multiple lines if enclosed in quotes or if the subsequent lines are indented. A future development would be to implement a search feature and find pictures or videos whose description contains the search terms...
* `date`: The date the photo was taken, in the format YYYY-MM-DD.
* `latitude`: The latitude of the media, for instance if the media was not geotagged when captured. You can use numerous web sites to find the latitude and longitude of places from a map. Examples are https://www.latlong.net/ or https://www.gps-coordinates.org/.
* `longitude`: The longitude of the capture of media.
* `country_name`: The name of the country where the photo was shot. You can have to overwrite the value found by the geoname feature in the case where a foreign city is nearer from the place the photo was shot than a local city.
* `region_name`: The name of the region. The geoname feature sometimes uses region denominations that are not the ones used locally.
* `place_name`: The name of the city or town to be displayed. This value is only used if the media is geotagged, that is has a latitude/longitude, either from EXIF metadata in the file or from album.ini. Overloading this value is interesting when the geoname feature does not find the correct place name. For instance, if you want to specify a special location instead of a city name.
* `tags`: A comma separated list of key words. For the moment, these tags are only displayed in the Metadata drawer window, but one could use them to build new navigation between media or search by key word.

Section names are case sensitive. Particularly `[DEFAULT]` must be in uppercase. Spaces in sections are part of the name and section names are not trimmed!
Metadata selectors are not case sensitive and are trimmed for spaces. Metadata values are timmed for spaces too.

### Inheritance for finding metadata values

The scanner supports a 2-levels inheritance to search for metadata values. It searches the metadata selector first into the section named with the name of the media file, and if not found it looks for it in the `[DEFAULT]` section.
The same principle applies for `[album]` that is searched first and then `[DEFAULT]` if not found.
If a media is not defined as a section of the `album.ini`, it will inherit metadata from `[DEFAULT]` that applies to all media files in the album.

The algorithm used is:
```
  For media metadata:
    If section [<media_filename>] exists:
      Search value in section [<media_filename>] else in [DEFAULT]
    Else:
      Search value in [DEFAULT]
  
  For album metadata
    If section [album] exists:
      Search value in [album] else in [DEFAULT]
    Else:
      Search value in [DEFAULT]
```

A simple way to use the `album.ini` would be:
1. Define in `[DEFAULT]` section the metadata that apply to all or most media files of the directory. It could be a location or a date, or tags depending on how you manage your media.
2. For the media where the defaults don't apply, create sections with the name of the files and specify the metadata that you want to change.


### `album.ini` example

```ini
# Additional metadata for album, pictures and videos
# See syntax on https://docs.python.org/3/library/configparser.html

# These default values apply to all media content in the directory
[DEFAULT]
# Manual geotagging of all pictures
# You can use https://www.latlong.net/, https://www.gps-coordinates.org/ or similar service to find places
# All photos and videos in the current album, including the album itself, will appear to have
# been takes in Montreal, Canada
longitude = -73.588014
latitude = 45.508873

# When album metadata is developped, this information will be used. For the moment, it's useless
# as it is not displayed in the web application, but you can start documenting your albums...
[album]
# The title of the album
title = A trip to Canada

# The album will appear to have geoname Montreal
place_name = Montreal


# The following metadata will apply only on photo file named '20171030_083915.jpg'.
# If a metadata is not defined in that section, it will use the ones defined in [DEFAULT],
# currently 'latitude' and 'longitude' for Montreal.
[20171030_083915.jpg]
# We give a caption to the picture instead of using filename.
title = From the airport

# The description allows us to use a short text associated with the picture.
description = The weather is cloudy in Paris when we leave for Montreal...

# This photo has been shoot in Paris, so we define its geographical coordinates here as
# it does not contain goegraphical information in its EXIF. Contrarily to all the other
# photos that were shoot in Montreal, that will use the values in the [DEFAULT] section,
# we define here the 'latitude' and 'longitude' that we want to use when the application
# is looking for geonames.
longitude = 2.3135018348693848
latitude = 48.86257477660442

# We can define keywords associated with the photo. They are simply displayed in the web
# application for the moment, but they could be used to browse by keywords or for searches.
tags = airport,plane,eiffel tower,Paris


# Now we defined metadata for photo named '20171031_160457.jpg'.
[20171031_160457.jpg]
# Use the following title instead of the file name.
title = Sunny in Montreal

# A description can span multiple lines when the following lines are indented.
description = Montrealers love to walk on the Mont-Royal.
  We've seen lots of squirels and racoons...

# Jump into the future! We don't want to use the date in the EXIF...
date = 2019-06-14

# And we associate keywords too.
tags = Canada,trip,holiday,Mount Royal



# All other files which are not defined in the 'album.ini' file will use the metadata
# defined in the [DEFAULT] section.

```

## Hints

### Geographical names are not overloaded. What happens?

If you want to overwrite geonames metadata, i.e. `country_name`, `region_name` and `place_name`, you have to keep in mind that this metadata information is only created by the scanner if it feels that it has to manage georgraphical information. It means that these metadata fields are only created when the scanner has seen `latitude` and `longitude` metadata, either by extracting it from the media EXIF or reading it from user defined values in `album.ini`.

Defining these values in `album.ini` does not inject them in the EXIF of the media. You can probably do it with a small Python/Shell script and the [`exiv2`](http://www.exiv2.org/) tool. These values are only used for display and browsing in MyPhotoShare.


### `title` and `description` metadata values are line-sensitive

The user defined metadata options `title` and `description` are line sensitive. It means that line breaks typed into `album.ini` will be kept and rendered as new lines when displayed by MyPhotoShare.

For instance, with the following `album.ini` extract:

```ini
[20180130_134216.jpg]
title = A trip in bicycle...
  ... turned into a nightmare!
description = Julia and I decided to visit New Delhi back country by bike.
  We rented two used bicycles from a friend of our janitor.
  After a few kilometers, Julia's had a flat. We had no tools to repair it.
  When we came back pushing the bicycles, the rain started to rain like cats and dogs.
  We were soaked when we came back home.
```

The title will be displayed on two lines and the description on five lines.

You can decide to include HTML markup into these metadata values, like `<strong>` or `<br>` tags, and they will be rendered by MyPhotoShare. But we recommend you not to if you later decide to ingest that metadata into your media EXIF (or you'll have to filter it out before doing it).

Like for other user defined metadata in `album.ini`, this information is not injected back into the media EXIF (see [exiv2 Metadata reference tables](http://www.exiv2.org/metadata.html) for more information). It's only used for display by MyPhotoShare.
