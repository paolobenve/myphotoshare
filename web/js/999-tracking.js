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
if (Options.piwik_server && Options.piwik_id) {
	$(window).load(function () {
	window._paq = window._paq || [];
	window._paq.push(['trackPageView']);
	window._paq.push(['enableLinkTracking']);
	(function() {
		var u="//" + Options.piwik_server;
		window._paq.push(['setTrackerUrl', u+'piwik.php']);
		window._paq.push(['setSiteId', Options.piwik_id.toString()]);
		var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
		g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
	})();
	});
	$(window).hashchange(function() {
		window._paq.push(['setCustomUrl', '/' + window.location.hash.substr(1)]);
		window._paq.push(['setDocumentTitle', PhotoFloat.cleanHash(location.hash)]);
		window._paq.push(['trackPageView']);
	});
}
