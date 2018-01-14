#!/bin/bash

# Parse which minifiers to use from configuration file
CONF=/etc/myphotoshare/myphotoshare.conf

MINIFY_JS="$(sed -nr 's/^\s*minify_js\s*=\s*(\w+)\s*.*$/\1/p' $CONF)"
MINIFY_JS=${MINIFY_JS:-web_service}

MINIFY_CSS="$(sed -nr 's/^\s*minify_css\s*=\s*(\w+)\s*.*$/\1/p' $CONF)"
MINIFY_CSS=${MINIFY_CSS:-web_service}

unixseconds=$(date +%s)

# Check that local minifiers are installed
case $MINIFY_JS in
	web_service)
		curl https://javascript-minifier.com/ > /dev/null 2>&1
		if [ $? -ne 0 ]; then
			echo "'curl' not installed or 'https://javascript-minifier.com/' down"
			echo "Aborting..."
			exit 1
		fi
	;;
	jsmin2)
		python2 -m jsmin > /dev/null 2>&1
		if [ $? -ne 0 ]; then
			echo "'jsmin' for Python2 is not installed. Look for package 'python-jsmin' or 'https://github.com/tikitu/jsmin'"
			echo "Aborting..."
			exit 1
		fi
	;;
	jsmin3)
		python3 -m jsmin > /dev/null 2>&1
		if [ $? -ne 0 ]; then
			echo "'jsmin' for Python3 is not installed. Look for package 'python3-jsmin' or 'https://github.com/tikitu/jsmin'"
			echo "Aborting..."
			exit 1
		fi
	;;
esac

case $MINIFY_CSS in
	web_service)
		curl https://cssminifier.com/ > /dev/null 2>&1
		if [ $? -ne 0 ]; then
			echo "'curl' not installed or 'https://cssminifier.com/' down"
			echo "Aborting..."
			exit 1
		fi
	;;
	cssmin)
		cssmin -h > /dev/null 2>&1
		if [ $? -ne 0 ]; then
			echo "'cssmin' is not installed. Look for package 'cssmin' or 'https://github.com/zacharyvoase/cssmin'"
			echo "Aborting..."
			exit 1
		fi
	;;
esac

# minify all .js-files
cd web/js
echo
echo == Minifying js files in js directory ==
echo
rm -f *.min.js
ls -1 *.js | grep -Ev "min.js$" | while read jsfile; do
	newfile="${jsfile%.*}.min.js"
	echo "minifying $jsfile"
	case $MINIFY_JS in
		web_service)
			curl -X POST -s --data-urlencode "input@$jsfile" https://javascript-minifier.com/raw > $newfile
		;;

		jsmin2)
			python2 -m jsmin $jsfile > $newfile
		;;

		jsmin3)
			python3 -m jsmin $jsfile > $newfile
		;;

		*)
			echo "Unsupported Javascript minifier: $MINIFY_JS. Check option 'minify_js' in '$CONF'"
			echo "Doing nothing on file $jsfile"
	esac
done

# merge all into one single file
rm -f scripts.min.js
cat *.min.js > scripts.min.js


# minify all .css-files
cd ../css
echo
echo == Minifying css files in css directory ==
echo
rm -f *.min.css
ls -1 *.css | grep -Ev "min.css$" | while read cssfile; do
	newfile="${cssfile%.*}.min.css"
	echo "minifying $cssfile"
	case $MINIFY_CSS in
		web_service)
			curl -X POST -s --data-urlencode "input@$cssfile" https://cssminifier.com/raw > $newfile
		;;

		cssmin)
			cssmin < $cssfile > $newfile
		;;

		*)
			echo "Unsupported CSS minifier: $MINIFY_CSS. Check option 'minify_css' in '$CONF'"
			echo "Doing nothing on file $cssfile"
	esac
done

# merge all into one single file
rm -f styles.min.css
cat *.min.css > styles.min.css

echo
echo "Completed in $((`date +%s` - $unixseconds)) s."
