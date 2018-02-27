# Utility scripts

Various scripts are stored in the `bin` directory.


## The album scanner: `scanner`

This is MyPhotoShare's main program used to scan media files in directories. You must give a configuration file as parameter. A typical run looks like:

```
$ bin/scanner /etc/myphotoshare/myphotoshare.conf 
    853349 2018-02-23 20:43:15.318259   [importer]                 No opencv library available, not using it
     26805 2018-02-23 20:43:15.345064   [Options]                  asterisk denotes options changed by config file
       257 2018-02-23 20:43:15.345321   |--[debug_css]                * true                    [DEFAULT: false           ]
       120 2018-02-23 20:43:15.345441   |--[debug_js]                 * true                    [DEFAULT: false           ]
       135 2018-02-23 20:43:15.345576   |--[max_verbose]                3                       [DEFAULT                  ]
       129 2018-02-23 20:43:15.345705   |--[show_faces]                 False                   [DEFAULT                  ]
       116 2018-02-23 20:43:15.345821   |--[css_minifier]               cssmin                  [DEFAULT                  ]
...
```

The scanner outputs various stats when browsing into the albums and parsing media files. At the end, it prints performance data.


## `js-css-minify.sh`

This script has to be run once when you first setup MyPhotoShare. It minifies (compress) JavaScript and CSS resources using either locally installed minifiers or web services. You must give the configuration file as parameter where your prefered minifiers are defined.

Minifying JavaScript and CSS reduces the bandwidth used to display MyPhotoShare web pages and reduces the number of requests sent to the server. You will probably use it on your production server. You can disable minifying in the configuration file if you want to view human-readable source files in your browser.

```
$ bin/js-css-minify.sh /etc/myphotoshare/myphotoshare.conf 

Using cssmin as CSS minifier
Using uglifyjs as JS minifier

== Minifying js files in js directory ==

minifying 000-jquery-1.12.4.js
... Found system jquery; using it.
minifying 001-hashchange.js
...
```


## `get_alternate_names.py`

This script downloads the alternate locations file from [GeoNames.org](https://www.geonames.org/) and prepares the locations files used by MyPhotoShare. If the script is run with additional language code parameters like 'ru', it will download localized place names for these parameters, in the current example in Russian. Without parameters, it defaults to using the language codes for the languages supported by MyPhotoShare: currently 'en', 'it', 'es' and 'fr'.
The resulting files are stored into `scanner/geonames/alternate_names_LN` where `LN` is a language code.

```
$ bin/get_alternate_names.py 

getting alternateNames.zip from geonames.org and extracting it to file...
done!

building language list
got: ['fr', 'en', 'it', 'es']

generating local files...
local files generated!
```


## `make_album_ini.sh`

`album.ini` files contain user-defined metadata. The user can create them into album directories with media. Running this script with a directory parameter creates a default `album.ini` file in that directory with sections for all media found.

The metadata added is commented in each section and you only have to uncomment it and add values:
```ini
#[DEFAULT]
#tags =
#date =
#latitude =
#longitude =
#place_name =
#region_name =
#country_name =

[album]
#title = ALBUM_NAME
#description =
#tags =

[MEDIA_FILENAME]
#title = MEDIA_FILENAME_WITHOUT_EXTENSION
#description =
#tags =
#latitude =
#longitude =
```

If an `album.ini` file already exists in the directory, new media found in the album is added to `album.ini`. When an error occurs, the script exits with error code `1`.
