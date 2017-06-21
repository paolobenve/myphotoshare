import sys

usrOptions = {}
OptionsForJs = []
def SetOptions(config_file = ""):
	global usrOptions, OptionsForJs
	from CachePath import message, next_level, back_level
	#~ try:
		#~ Options
	#~ except NameError:
	
	DefaultOptions = {
		'max_verbose'                  : 0, # verbosity level
		'indexHtmlPath'                : "", # absolute path of the folder where index.html resides
		'albumPath'                    : "", # absolute path
		'cachePath'                    : "", 
		'thumbSizes'                   : [ (1600, False), (1200, False), (800, False), (150, True) ],
		'language'                     :"en", # overrides browser language
		'zeroThumbSpacing'             : False,
		'videoTranscodeBitrate'        : "4M",
		'foldersString'                : "_folders",
		'byDateString'                 : "_by_date",
		'cacheFolderSeparator'         : "-",
		'pageTitle'                    : "My photos",
		'differentAlbumThumbnails'     : False,
		'thumbnailsGenerationMode'     : "cascade", # permitted values: "cascade", "parallel", "mixed"
		# 25 images ~ 5MB each, 4 thumbnail sizes:
		# parallel ~ 60 seconds
		# mixed    ~ 35 seconds
		# cascade  ~ 30 seconds
		#
		# 25 images ~ 5MB each, 4 thumbnail sizes, the 4 already present:
		# parallel ~ 48 seconds
		# mixed    ~ 35 seconds
		# cascade  ~ 0.2 seconds
		'showMediaNamesBelowInAlbums'  : True,
		'titleFontSize'                : "medium",	# other values: large, small, or a px/em size
		'titleColor'                   : "white",
		'titleImageNameColor'          : "green",
		'jpegQuality'                  : 95,		# a number 1 -100
		'backgroundColor'              : "#222222",	# ~ gray
		'switchButtonBackgroundColor'  : "white",
		'switchButtonColor'            : "black"
	}
	
	if config_file:
		execfile(config_file)
	OptionsForJs = [
		'albumPath',
		'cachePath',
		'indexHtmlPath',
		'language',
		'js_zeroThumbSpacing',
		'foldersString',
		'byDateString',
		'cacheFolderSeparator',
		'pageTitle',
		'differentAlbumThumbnails',
		'showMediaNamesBelowInAlbums',
		'titleFontSize',
		'titleColor',
		'titleImageNameColor',
		'backgroundColor',
		'switchButtonBackgroundColor',
		'switchButtonColor'
	]
	for key in DefaultOptions :
		try:
			usrOptions[key]
		except KeyError:
			usrOptions[key] = DefaultOptions[key]
	
	if not usrOptions['indexHtmlPath'] and not usrOptions['albumPath'] and not usrOptions['cachePath']:
		message("options", "at least indexHtmlPath or both albumPath and cachePath must be given, quitting")
		sys.exit(-97)
	elif usrOptions['indexHtmlPath'] and not usrOptions['albumPath'] and not usrOptions['cachePath']:
		message("options", "on indexHtmlPath is given, using its subfolder 'albums' for albumPath and 'cache' for cachePath")
		usrOptions['albumPath'] = os.path.join(usrOptions['indexHtmlPath'], "albums")
		usrOptions['cachePath'] = os.path.join(usrOptions['indexHtmlPath'], "cache")
	elif (not usrOptions['indexHtmlPath'] and
			usrOptions['albumPath'] and
			usrOptions['cachePath'] and
			usrOptions['albumPath'][:usrOptions['albumPath'].rfind("/")] == usrOptions['cachePath'][:usrOptions['albumPath'].rfind("/")]):
		usrOptions['indexHtmlPath'] = usrOptions['albumPath'][:usrOptions['albumPath'].rfind("/")]
	message("Options", "asterisk denotes options changed by config file")
	next_level()
	
	for key in usrOptions:
		if DefaultOptions[key] == usrOptions[key]:
			option = "  "
		else:
			option = "* "
		option += str(usrOptions[key])
		message(key, option)
	back_level()
