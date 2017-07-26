// google analytics
if (Options.google_analytics_id) {
	$(window).load(function () {
		window._gaq = window._gaq || [];
		window._gaq.push(['_setAccount', Options.google_analytics_id]);
		var ga = document.createElement('script');
		ga.type = 'text/javascript';
		ga.async = true;
		ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
		var s = document.getElementsByTagName('script')[0];
		s.parentNode.insertBefore(ga, s);
	});
	$(window).hashchange(function() {
		window._gaq = window._gaq || [];
		window._gaq.push(['_trackPageview']);
		window._gaq.push(['_trackPageview', PhotoFloat.cleanHash(location.hash)]);
	});
}

// piwik
if (Options.piwik_site && Options.piwik_id) {
	$(window).load(function () {
	var _paq = _paq || [];
	_paq.push(['trackPageView']);
	_paq.push(['enableLinkTracking']);
	(function() {
		var u="//" + Options.piwik_site;
		_paq.push(['setTrackerUrl', u+'piwik.php']);
		_paq.push(['setSiteId', Options.piwik_id.toString()]);
		var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
		g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
	})();
	});
	$(window).hashchange(function() {
		_paq.push(['setCustomUrl', '/' + window.location.hash.substr(1)]);
		_paq.push(['setDocumentTitle', PhotoFloat.cleanHash(location.hash)]);
		_paq.push(['trackPageView']);
	});
}
