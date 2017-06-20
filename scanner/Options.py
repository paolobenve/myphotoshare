#~ from CachePath import message

class Options:
	try:
		Options
	except NameError:
		Options = {}
	
	DefaultOptions = {
		'max_verbose'                  : 0, # verbosity level
		'albumPath'                    : "", # absolute path
		'cachePath'                    : "", # absolute path
		'indexHtmlPath'                : "", # absolute path of the folder where index.html resides
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

	
	def __init__(self):
		for key in self.DefaultOptions :
			try:
				self.Options[key]
			except KeyError:
				self.Options[key] = self.DefaultOptions[key]

