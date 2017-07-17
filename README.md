# photofloat v. 2.2
### A Web Photo Gallery Done Right via Static JSON & Dynamic Javascript
#### by Jason A. Donenfeld (<Jason@zx2c4.com>), Jerome Charaoui (jerome@riseup.net)  Joachim Tingvold (joachim@tingvold.com), Paolo Benvenuto (<paolobenve@gmail.com>)

![Screenshot](screnshot-panorama-2.2.png)
![Screenshot](screnshot-classic-square-2.2.png)
![Screenshot](screnshot-no-slide-mode-fit-2.2.png)
![Screenshot](screnshot-slide-mode-2.2.png)

It's an open source web photo gallery aimed at sleekness and speed. It keeps with an old hat mentality, preferring to work over directory structures rather than esoteric photo database management software. Everything it generates is static, which means it's extremely fast.

This is a Jason A. Donenfeld's Photofloat fork, enriched by following contributors: Jerome Charaoui's patches about showing videos, and Paolo Benvenuto's following development.

[Check out a demo!](http://palmaro.qumran2.net/#!/_folders-giovani-biscotti_natale_2016/giovani_preparazione_biscotti_2016-12-16-17.17.27.jpg)

## How It Works

photofloat consists of two segments – a Python script and a JavaScript application.

The Python script scans a directory tree of images, whereby each directory constitutes an album. It then populates a second folder, known as the cache folder with statically generated JSON files and thumbnails. It writes an `options.json` file too, putting inside it all the options from default config file or user config file. The scanner extracts metadata from EXIF tags in JPEG photos. photofloat is smart about file and directory modification time, so you are free to run the scanner script as many times as you want, and it will be very fast if there are few or zero changes since the last time you ran it.

The JavaScript application consists of a single `index.php` file with a single `scripts.min.js` and a single `styles.min.css`. It fetches the `options.json` file and the statically generated JSON files and thumbnails on the fly from the `cache` folder to create a speedy interface.

It is, essentially, the slickest and fastest, most minimal but still well-featured photo gallery app on the net.

### Dependencies

Photofloat needs:

* `python` 2.7
* a working web server (e.g. `apache`, `nginx`, etc.) with `php` module installed
* `avconv`/`ffmpeg` in order to be able to manage videos.

## Changelog

Features added in version 2.2 (July 15, 2017):

* translations are now managed via a separate js file: enthusiasts and followers are encouraged to provide the translation for their language 
* better managing of errors
* separated albums and media sorting
* - default_album_reverse_sort (boolean) set default sorting for albums
* - default_media_reverse_sort (boolean) sets the default sorting for images/video
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

Features added in version 2.1.1 (July 6, 2017):

* new options:
* - persistent_metadata (boolean): permits to have metadata shown persistently on image
* - album_button_background_color
* - album_caption_color

Features added in version 2.1 (July 6, 2017):

* Images and directories can be sorted ascending/descending (via a cookie)

Features added in version 2.0 (July 4, 2017):

* A date tree is builded, permitting photo to be seen by year, month, date
* When a photo is viewed, the user can switch between the folder and the date the photo was taken
* Better error management: if folder is wrong, show root folder; if image is wrong, show album
* In addition to former invocation (with albums and cache paths), photofloat can be invoked with one parameter: the customization file, which adds many configuration variables;
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

Features added by Joachim (2015):

* generate minified css and js through external api
* parallel thumbnail generation

Features added by Jerome (2013):

* manage videos

Features by Jason (2012):

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

## Installation

#### Download the source code from the git repository:

    $ git clone https://github.com/paolobenve/photofloat.git
    $ cd photofloat

#### Copy and tweak the configuration file

    $ sudo mkdir /etc/photofloat
    $ sudo cp photofloat.conf.defaults /etc/photofloat/myproject.conf
    $ sudo vim /etc/photofloat/myproject.conf

In your config file (myproject.conf, name can be whatever you want)set the proper folders for albums (your photo, they won't be modified) and cache (all the stuff photofloat requieres in order to work)

#### Build the web page.

This simply minifies and concatenate everything of js and css.

    $ ./js-css-minify.sh

#### (When photofloat code is updated) Update your photofloat installation

Go to the folder you cloned the repository in and execute:

    $ git pull https://github.com/paolobenve/photofloat.git
    $ ./js-css-minify.sh

#### Generate the albums:

When you're done run the static generator (you need Python≥2.6 and the Python Imaging Library; for video something like libav-conv is requiered too):

    $ /your/photofloat/installation/dir/scanner/main.py /etc/photofloat/myproject.conf

After it finishes, you will be all set. Simply have your web server serve pages out of your web directory. You may want to do the scanning step in a cronjob, if you don't use the deployment makefiles mentioned below.

Note: The albums web folder and the cache one could be anywhere in the file system or in web, the only requierement is that the web server has access to them.

cron file example with albums and cache in /var/www:

    # update photofloat cache
    
    58 1  * * *<--->root<-->/your/photofloat/installation/dir/scanner/main.py /etc/photofloat/myproject.conf > /var/log/myphotofloatproject.log

instead or running photofloat as root, you can use whatever user that have access to the directories you set up in your config file

## Optional: Server-side Authentication

The JavaScript application uses a very simple API to determine if a photo can be viewed or not. If a JSON file returns error `403`, the album is hidden from view. To authenticate, `POST` a username and a password to `/auth`. If unsuccessful, `403` is returned. If successful, `200` is returned, and the previously denied json files may now be requested. If an unauthorized album is directly requested in a URL when the page loads, an authentication box is shown.

photofloat ships with an optional server side component called FloatApp to faciliate this, which lives in `scanner/floatapp`. It is a simple Flask-based Python web application.

#### Edit the app.cfg configuration file:

    $ cd scanner/floatapp
    $ vim app.cfg

Give this file a correct username and password, for both an admin user and a photo user, as well as a secret token. The admin user is allowed to call `/scan`, which automatically runs the scanner script mentioned in the previous section.

#### Decide which albums or photos are protected:

    $ vim auth.txt

This file takes one path per line. It restricts access to all photos in this path. If the path is a single photo, then that single photo is restricted.

#### Configure nginx:

FloatApp makes use of `X-Accel-Buffering` and `X-Accel-Redirect` to force the server-side component to have minimal overhead. Here is an example nginx configuration that can be tweaked:

    server {                                                                                                               
            listen 80;                                                                                                     
            server_name photos.jasondonenfeld.com;                                                                         
            location / {
                    index index.html;
                    root /var/www/htdocs/photos.jasondonenfeld.com;
            }
    
            include uwsgi_params;
            location /albums/ {
                    uwsgi_pass unix:/var/run/uwsgi-apps/photofloat.socket;
            }
            location /cache/ {
                    uwsgi_pass unix:/var/run/uwsgi-apps/photofloat.socket;
            }
            location /scan {
                    uwsgi_pass unix:/var/run/uwsgi-apps/photofloat.socket;
            }
            location /auth {
                    uwsgi_pass unix:/var/run/uwsgi-apps/photofloat.socket;
            }
            location /photos {
                    uwsgi_pass unix:/var/run/uwsgi-apps/photofloat.socket;
            }
    
            location /internal-cache/ {
                    internal;
                    alias /var/www/uwsgi/photofloat/cache/;
            }
            location /internal-albums/ {
                    internal;
                    alias /var/www/uwsgi/photofloat/albums/;
            }
    }

Note that the `internal-*` paths must match that of `app.cfg`. This makes use of uwsgi for execution:

    metheny ~ # cat /etc/uwsgi.d/photofloat.ini 
    [uwsgi]
    chdir = /var/www/uwsgi/%n
    master = true
    uid = %n
    gid = %n
    chmod-socket = 660
    chown-socket = %n:nginx
    socket = /var/run/uwsgi-apps/%n.socket
    logto = /var/log/uwsgi/%n.log
    processes = 4
    idle = 1800
    die-on-idle = true
    plugins = python27
    module = floatapp:app

## Optional: Deployment Makefiles

Both the scanner and the webpage have a `make deploy` target, and the scanner has a `make scan` target, to automatically deploy assets to a remote server and run the scanner. For use, customize `deployment-config.mk` in the root of the project, and carefully read the `Makefile`s to learn what's happening.

## License

Copyright (C):
* 2010 - 2014 Jason A. Donenfeld
* 2016 Jerome Charaoui
* 2017 Paolo Benvenuto

Thanks to Joachim and all other contributors for their help!

All Rights Reserved.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
