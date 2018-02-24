# Changelog

* moved scripts into bin directory. Create `scanner` as a link to `main.py`. Added `make_album_ini.sh`to create a default `album.ini` file in a directory.
* add options `social`, `social_size` and `social_color` for tuning display of social icons.
* use Debian/Ubuntu system-wide JavaScript packages if available (you might need to run `sudo a2enconf javascript-common` on the server to enable the use of `/javascript` virtual directory).
* added support for `uglifyjs` JavaScript minifier
* new option `small_square_crops_background_color` for filling the background of small square crops
* bug fixes
* new debug option `show_faces`: lets the scanner show the faces detected (but read the note in `myphotoshare.conf.default`)
* new option `face_cascade_scale_factor`: a parameter of `opencv`'s `detectMultiScale` function that detects the faces in the photo
* UI cleaned putting sort and view switches to a hidden top right menu
* user can toggle album slide mode, thumbnails spacing, thumbnails types, show album and media names, show media count, all with right top corner menu
* the scanner manages more precisely certain option changes that require regenerating of `json` files, reduced size images, thumbnails
* new option `slide_album_caption_color`: the color to use with album slide mode
* implemented search function: media and albums can be searched by file name, title, description, tags; search may be whole word or inside words, considering accents and capitals or not
  * new option `by_search_string`: the string used for search albums
  * new option `max_search_album_number`: the maximum number of search album that will be loaded
* reorganization of documentation:
  * creation of `doc` and `doc/img` folders
  * `README.md` split into individual files
  * explained how to use advanced features like geonames or face detection
  * created a gallery of screenshots
* Reduced images and thumbnail naming schema is now more robust
  * cache files names are now made of only lower case ascii characters



### version 3.3 (January 22, 2018)

* new option `get_geonames_online`, if true, get country, state, place names from geonames.org (online), otherwise get it from the files in scanner/geonames/cities1000.txt (names are in english)
* clustering of places with too many photos is done now by the k-means algorithm
* added options `js_minifier` and `css_minifier` to specify what minifier to use: web services or local ones
* removed `thumbnail_generation_mode` option: only cascade method is left, parallel and mixed methods are removed
* option `show_media_names_below_thumbs_in_albums` changed to `show_media_names_below_thumbs`
* new option `show_album_names_below_thumbs`: decides whether to show the album name in album thumbnails
* new option `show_media_count`: decides whether to show the media count in album thumbnail and title
* cropping to square takes now into account faces if opencv and python-opencv are installed
* scanner code for producing the thumbnails was optimized
* default options give now a light UI

### version 3.2 (January 7, 2018)

* Added `debug_css` and `debug_js` options for debugging (thanks to pmetras)
* Added french translations (thanks to pmetras)
* Bug fixes by pmetras
* Fixed unnecessary exposure of paths (thanks pmetras for reporting it)

### version 3.1 (December 30, 2017)

 * new option `checksum`: controls whether a checksum should be generated in order to decide if a media file has changed (useful with geotags)
 * better scanner reports
 * bug fixes

### version 3.0 (December 12, 2017):

* Manages photo's gps data and retrieves map names from geonames.org web service: builds a country/region-state/place tree as for dates, and, when a photo has gps metadata permits switching among album, date and place viewed
* - shows place in map
* - place virtual albums are split into various subfolder if they have too many photos inside them
* - new option `map_service`: specify what service is used for showing maps; can be "openstreetmap", "googlemaps", or osmtools; the last allows a marker on the map
* - new option `unspecified_geonames_code`: the code used in gps tree for unspecified admin names (there should be no need to change it)
* - new option `map_zoom_levels`: a 3-values tuple specifying the zoom values to use respectively for country-, admin- and place-level maps
* - new option `photo_map_zoom_level`: the value to use for the map shown with the photos
* - option `big_date_folders_threshold` renamed to `big_virtual_folders_threshold`

### version 2.8 (November 18, 2017):

* better user experience on mobile: show sharper images
* removed option server_cache_path (closes #54), server cache folder is now always "cache":
  if it was previously set to a different value in custom option file, please move it on your server and change web server settings in order to avoid recreation of all the thumbnails

### version 2.7.5 (October 26, 2017):

* added link for direct download of media
* piwik bug fixed

### version 2.7.4 (September 29, 2017):

* various bugs fixed

### version 2.7.3 (September 21, 2017):

* various bugs fixed

### version 2.7.2 (September 16, 2017):

* various bugs fixed

### version 2.7.1 (September 11, 2017):

* fixed php bug in album sharing

### version 2.7 (September 10, 2017):

* fullscreen simulation for devices not implementing fullscreen api
* added sorting by name of subalbums and media
* modified default reverse sorting options, and now they only apply to date sorting (name default sorting is always normal)
* - default_album_reverse_sort -> default_album_date_reverse_sort
* - default_media_reverse_sort -> default_media_date_reverse_sort
* bug fixes

### version 2.6.4 (September 5, 2017):

* fixed sharing of videos
* removed unnecessary parameter when sharing

### version 2.6.3 (September 2, 2017):

* album buttons has now a link to go to random image directly

### version 2.6.2 (September 2, 2017):

* videos: a transparency indicating it's a video is added to thumbnails
* added media count in title
* updated modernizr
* bug fixes

### version 2.6.1 (August 16, 2017):

* added media count to subalbums slides
* only update json files and composite images if needed
* bug fixes

### version 2.6 (August 16, 2017):

* composite images for sharing albums are now generated by scanner (not by php any more);
* new option `cache_album_subdir`: the subdir of cache_path where the album composite images will be saved
* new option `video_crf` for video quality
* new option `follow_symlinks`, defaults to false, set it to true if you want to use symlink directories
* albums and media which have a companion which would have the same cache base are now managed correctly (solves #43, #44)
* date albums with same image in two different folders are now managed correctly (solves #30)
* scanner produced a final time report (useful for trimming the code)
* more speedy (removed unuseful garbage collectors)

### version 2.5 (August 3, 2017):

* project name is now `myphotoshare`
* keyboard navigation: arrows, pageup/down, esc, f (fullscreen), m (metadata)
* added vertical swipe gestures on media (they are mapped on arrow up/down)
* restored cache use in scanner: scanner is now faster on already scanned albums
* implemented verbosity levels, default is now 3 = errors, warnings, walkings
* new option `recreate_fixed_height_thumbnails`: makes the scanner delete wide media fixed height thumbnail, in order to get rid of a previous versions bug which caused these thumbnail be generated blurred. Set it to `true`/`1` and make the scanner work, then reset again it to `false`/`0`

### version 2.4.1 (July 26, 2017):

* do not produce canvas for small images: they are shown in their original size
* two new options: `exclude_files_marker` and `exclude_tree_marker`: when the markers are found in a folder, the media in the folder itself or the whole tree isn't scanned

### version 2.4 (July 24, 2017):

* swipe gesture on mobile to go to next/previous photo/video
* media animation when passing to next/previous image
* simplified html structure and json files
* new option `min_album_thumbnail`: sets how many album thumbnails will fit at least on screen width

### version 2.3 (July 20, 2017):

* social buttons for sharing on facebook, whatsapp (only on mobile), twitter, google+, email
* web page isn't `index.html` any more, it's `index.php`: this way we accomplish various things through php:
* - php can set page title (by reading the options.json file)
* - php can set the `<link rel"..." ...>` tag in <head></head>, which permits facebook and google+ to show the image when sharing a photo or a video: when sharing an album, php builds an image made of n x n thumbnail (in order to get that, album-size square thumbnails are always generated by python scanner)
* new options `max_album_share_thumbnails_number`: how many thumbnails will be used at most when creating the composite image for sharing albums

### version 2.2 (July 15, 2017):

* translations are now managed via a separate js file: enthusiasts and followers are encouraged to provide the translation for their language
* better managing of errors
* separated albums and media sorting
* - default_album_reverse_sort (boolean) sets default sorting for albums
* - default_media_reverse_sort (boolean) sets default sorting for images/video
* separate managing of album and media thumbnails
* - albums thumbs can have square (classic behaviour) or fit (rectangular thumbnail) type, according to new album_thumb_type option
* - images/video thumbs can have square (classic behaviour) or fixed height (rectangular thumbnail) type, according to new media_thumb_type option
* more new options:
* - big_date_folders_threshold: doesn't make thumbnails show for date albums too big
* - albums_slide_style (boolean): albums are shown in a simple way or with slide style
* removed options:
* - different_album_thumbnails
* buttons appearing on mouse over are shown persistently on mobile
* landscape photos are shown vertically centered
* if the window is resized, the reduced size image shown is changed according to window size, so that it never shows blurred
* videos now works perfectly in fullscreen mode
* new option `respected_processors`: tells the scanner how many processor not to use

### version 2.1.1 (July 6, 2017):

* new options:
* - persistent_metadata (boolean): permits to have metadata shown persistently on image
* - album_button_background_color
* - album_caption_color

### version 2.1 (July 6, 2017):

* Images and directories can be sorted ascending/descending (via a cookie)

### version 2.0 (July 4, 2017):

* A date tree is builded, permitting photo to be seen by year, month, date
* When a photo is viewed, the user can switch between the folder and the date the photo was taken
* Better error management: if folder is wrong, show root folder; if image is wrong, show album
* In addition to former invocation (with albums and cache paths), `myphotoshare` can be invoked with one parameter: the customization file, which adds many configuration variables;
* web site appearance now is very customizable:
* - choose between cascade, parallel and mixed thumbnails generation
* - fhoose between putting thumbnails in cache dir or in subdir, by 2-letters, from folder md5 or beginning of folder
* - thumbnail can be spaced
* - album thumbnails can be showed different from images ones
* - jpeg quality can be set
* - 3 different thumbnail types: square (photofloat's classical), fixed_height (the size determines the height, the width will depend on orientation), canvas (square thumbnail containing the whole image)
* - page title, font sizes, colors and background colors can be customized
* - photo names can be shown below thumbnails when showing an album
* - initial language support
* - albums and cache server folders can be anywhere, even on another server (obviously, they will be generated on a pc and then uploaded wherever)
* (to do) share buttons

### version by Joachim (2015):

* generate minified css and js through external api
* parallel thumbnail generation

### version by Jerome (2013):

* manage videos

### initial features by Jason (2012):

* Animations to make the interface feel nice
* Separate album view and photo view
* Album metadata pre-fetching
* Photo pre-loading
* Recursive async randomized tree walking album thumbnail algorithm
* Smooth up and down scaling
* Mouse-wheel support
* Metadata display
* Consistent hash url format
* Linkable states via ajax urls
* Static rendering for googlebot conforming to the AJAX crawling spec.
* Facebook meta tags for thumbnail and post type
* Link to original images (can be turned off)
* Optional Google Analytics integration
* Optional server-side authentication support
* A thousand other tweaks here and there...
