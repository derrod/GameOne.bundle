# GameOne.de Plex Plugin
# by Rodney <https://github.com/derrod>

PREFIX = "/video/gameone"

NAME = 'Game One'

ART = 'art-default.jpg'
ICON = 'icon-default.png'
IC_BLOG = 'icon_blog.png'
IC_PUP = 'icon_1up.png'
IC_SEARCH = 'icon_search.png'
IC_NEXT = 'icon_next.png'
IC_PC = 'icon_podcast.png'
IC_PT = 'icon_playtube.png'
IC_TV = 'icon_tv.png'
IC_ACC = 'icon_account.png'
IC_TV_SEARCH = 'icon_search_tv.png'
IC_PT_SEARCH = 'icon_search_playtube.png'

# The API Endpoints for fetching metadata for videos and audio files.
VIDEOAPIURL = "https://gameone.de/videos/%s.json"
AUDIOAPIURL = "https://gameone.de/audios/%s.json"
GALLERYAPIURL = "https://gameone.de/galleries/%s.json"

# This is a nonexistant url for handling video and audio files because there isn't an universal URL otherwise
MEDIAURL = "http://media.gameone.de/%s"

# Headers of the App
HTTP.Headers['User-Agent'] = 'GameOne/323 CFNetwork/609 Darwin/13.0.0'
HTTP.Headers['X-G1APP-DEVICEINFO'] = 'iPhone3,1_6.0'
HTTP.Headers['X-G1APP-VERSION'] = '2.0.1(323)'
HTTP.Headers['X-G1APP-APPIDENTIFIER'] = 'de.gameone.iphone'
HTTP.Headers['X-G1APP-IDENTIFIER'] = '824BAB323627483698C844E2CC978D06'

BASEURL = 'https://gameone.de/'

# REGEX Patterns:
REGEX_AUDIO = Regex(r'rtaudio:(.*)"')
REGEX_VIDEO = Regex(r'riptide:(.*)"')
REGEX_YOUTUBE = Regex(r'youtube://(.*)"')
REGEX_GALLERY = Regex(r'gallery:(.*)"')

# This needs to be unicode.
NEXT_SUMMARY = unicode('Nächste Seite', "utf-8")

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(PREFIX, MainMenu, NAME, ICON, ART)

	ObjectContainer.title1 = 'Game One'
	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)
	
	# 1 Hour Cache seems reasonable for the most part, images aren't changed, posts updated 1-2 times daily.
	HTTP.CacheTime = 3600.0
	# Clear Cache because not doing so seems to cause issues
	HTTP.ClearCache()

	Initialize()


def ValidatePrefs():
	ResetDict()
	Initialize()


def Initialize():
	global ITEMS_PER_PAGE
	ITEMS_PER_PAGE = int(Prefs['itemsperpage'])
	global TV_ITEMS_PER_PAGE
	TV_ITEMS_PER_PAGE = int(Prefs['itemsperpage'])

	# Login if possible
	u = Prefs['username']
	p = Prefs['password']
	if( u and p ):
		if Dict['logged_in'] == True:
			# Check Login
			url = BASEURL + 'users/me.json'
			HTTP.Headers['Authorization'] = Dict['auth_header']
			login = JSON.ObjectFromURL(url, cacheTime=0.0)
			if 'user' not in login:
				ResetDict()
			else:
				if login['user']['subscription'] == 1:
					Dict['premium'] = True
				else:
					Dict['premium'] = False
		else:
			# Log in
			credentials = {'user_session[user_login]':u,'user_session[password]':p}
			url = BASEURL + 'session.json'
			response = JSON.ObjectFromURL(url, values=credentials, cacheTime=0.0)
			if 'user' in response:
				if response['user']['subscription'] == 1:
					Dict['premium'] = True
				else:
					Dict['premium'] = False
				Dict.Save()
				Dict['logged_in'] = True
				cred_b64 = String.Base64Encode(u + ':' +  p)
				Dict['auth_header'] = 'Basic ' + cred_b64
				HTTP.Headers['Authorization'] = Dict['auth_header']
			else:
				ResetDict()
	else:
		ResetDict()	
	Dict.Save()
	
		
def MainMenu():
	if Dict['logged_in'] == True:
		if Dict['premium'] == True:
			status_text = 'Eingeloggt - 1UP Aktiv'
		else:
			status_text = 'EIngeloggt - 1UP Inaktiv'
	else:
		status_text = 'Nicht Eingeloggt'
	
	oc = ObjectContainer(no_cache = False)
	oc.add(DirectoryObject(key = Callback(Parser, content = 'blog'), title = 'Blog', thumb = R(IC_BLOG), summary = 'Blog'))
	oc.add(DirectoryObject(key = Callback(Parser, content = 'tv'), title = 'TV Sendungen', thumb = R(IC_TV), summary = 'TV Episoden'))
	
	if Dict['premium'] == False:
		oc.add(DirectoryObject(key = Callback(Unauthorized), title = '1UP Inhalte', thumb = R(IC_PUP), summary = 'Appklusiver Content'))
	else:
		oc.add(DirectoryObject(key = Callback(Parser, content = 'premium'), title = '1UP Inhalte', thumb = R(IC_PUP), summary = 'Appklusiver Content'))

	oc.add(DirectoryObject(key = Callback(Parser, content = 'podcast'), title = 'Podcasts', thumb = R(IC_PC), summary = 'Podcasts'))
	oc.add(DirectoryObject(key = Callback(PlayTubeMenu, title = 'Playtube'), title = 'Playtube', thumb = R(IC_PT), summary = 'Playtube'))
	
	oc.add(InputDirectoryObject(key = Callback(Parser, content = 'blog_search'), title = 'Blogsuche', prompt = 'Suchbegriff eingeben', thumb = R(IC_SEARCH), summary = 'Suche in Blogposts'))
	oc.add(InputDirectoryObject(key = Callback(Parser, content = 'tv_search'), title = 'TV Suche', prompt = 'Suchbegriff eingeben', thumb = R(IC_TV_SEARCH), summary = 'Suche in TV Episoden'))
	oc.add(DirectoryObject(key = Callback(Account), title = 'Mein Account: ' + status_text, thumb = R(IC_ACC), summary = 'Accountinformationen'))
	oc.add(PrefsObject(title = 'Einstellungen', summary = 'Einstellungen'))
	return oc


@route(PREFIX + '/playtube')
def PlayTubeMenu(title):
	oc = ObjectContainer(title2 = title, no_cache = False)
	oc.add(DirectoryObject(key = Callback(Parser, content = 'playtube_mostviews'), title = 'Meistgesehen Videos', thumb = R(IC_PT), summary = 'Meistgesehen Videos'))
	oc.add(DirectoryObject(key = Callback(Parser, content = 'playtube_best'), title = 'Bestbewertete Videos', thumb = R(IC_PT), summary = 'Bestbewertete Videos'))
	oc.add(DirectoryObject(key = Callback(Parser, content = 'playtube_discussed'), title = 'Meistdiskutierte Videos', thumb = R(IC_PT), summary = 'Meistdiskutierte Videos'))
	oc.add(DirectoryObject(key = Callback(Parser, content = 'playtube_latest'), title = 'Neuste Videos', thumb = R(IC_PT), summary = 'Neuste Videos'))
	oc.add(InputDirectoryObject(key = Callback(Parser, content = 'playtube_search'), title = 'Suche in Playtube', prompt = 'Suchbegriff eingeben', thumb = R(IC_PT_SEARCH), summary = 'Suche in Playtube'))
	return oc


@route(PREFIX + '/notimplemented')
def NotImplemented():
	return MessageContainer(
		"Not implemented",
		"Not implemented"
	)


@route(PREFIX + '/account')
def Account():
	if Dict['logged_in'] == False:
		text = 'Du bist nicht eingeloggt.'
	else:
		url = BASEURL + 'users/me.json'
		account_info = JSON.ObjectFromURL(url, cacheTime=0.0)['user']
		name = account_info['name']
		if Dict['premium'] == True:
			subscription_end = str(Datetime.ParseDate(account_info['subscription_end_date'])).split('+')[0].replace('-','.')
			text = 'Name: ' + name + '\n1UP aktiv bis: ' + subscription_end + '\n'
		else:
			text = 'Name: ' + name + '\nKein 1UP Abonnement\n'
	
	return MessageContainer("Dein Account", text)


# New Parser for all types of objects.
@route(PREFIX + '/parser')
def Parser(content, page = 1, query = ''):
	page = int(page)

	# What to parse, this isn't pretty but an easy way to put everything in one function:
	if content == "blog":
		content_url = BASEURL + 'app/posts/blog.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'Blog Seite ' + str(page)

	elif content == "premium":
		content_url = BASEURL + 'app/blog/premium.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'Appklusiv-Content Seite' + str(page)

	elif content == "podcast":
		content_url = BASEURL + 'app/posts/podcast.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'Podcasts Seite ' + str(page)

	elif content == "tv":
		content_url = BASEURL + 'tv.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'TV Episoden Seite ' + str(page)

	elif content == "playtube_mostviews":
		content_url = BASEURL + 'playtube/filter/hottest.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'asdf Seite ' + str(page)

	elif content == "playtube_best":
		content_url = BASEURL + 'playtube/filter/popular.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'asomasd Seite ' + str(page)

	elif content == "playtube_discussed":
		content_url = BASEURL + 'playtube/filter/discussed.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'asomasd Seite ' + str(page)
		
	elif content == "playtube_latest":
		content_url = BASEURL + 'playtube/filter/latest.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'asomasd Seite ' + str(page)

	elif content == "playtube_search":
		content_url = BASEURL + 'search/playtube.json?q=' + query + '&page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'Suche nach "' + query + '" in Playtube, Seite ' + str(page)

	elif content == "blog_search":
		content_url = BASEURL + 'search/blog.json?q=' + query + '&page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'Suche nach "' + query + '" in Blogposts, Seite ' + str(page)

	elif content == "tv_search":
		content_url = BASEURL + 'search/shows.json?q=' + query + '&page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
		title = 'Suche nach "' + query + '" in TV Shows, Seite ' + str(page)
	else:
		return MessageContainer(
			"Error",
			"The specified content type does not exist!"
		)

	oc = ObjectContainer(title2=title, replace_parent=False, no_cache = False, no_history = True)
	
	try:
		rawfeed = JSON.ObjectFromURL(content_url, cacheTime=0)
	except:
		return ObjectContainer(header='Error', message='Keine Items gefunden')


	# Parser
	for item in rawfeed['items']:
		# determine type, video or post.
		type = item.keys()[0]
		
		# Handle Post (Blogposts/Podcasts) Objects
		if type == 'post':
			post = item['post']
			raw_post_content = post['body']
			
			# Plex Home Theater doesn't display tagline, this is a small workaround
			if Client.Platform == 'Plex Home Theater':
				post_content = post['excerpt'] + '\n\n' + HTML.ElementFromString(raw_post_content).text_content()
			else:
				post_content = HTML.ElementFromString(raw_post_content).text_content()

			post_title = post['title']

			# posts are all in the path blog/
			posturl =  BASEURL + 'blog/' + str(post['id']) +'.json'

			# If an items requires a subscription we change the callback to the unauthorized message
			if post['subscription_only'] == True and Dict['premium'] == False:
				cb = Callback(Unauthorized)
			else:
				cb = Callback(GetMediaFromURL, title = post_title, url = posturl)

			oc.add(DirectoryObject(
				key = cb,
				title = post_title,
				summary = post_content,
				thumb = Resource.ContentsOfURLWithFallback(post['image_url']),
				tagline = post['excerpt']
			))
		
		# Handle TV Show objects
		elif type == 'tv_show':
			show = item['tv_show']
			if Client.Platform == 'Plex Home Theater':
				show_content = show['short_description'] + '\n\n' + HTML.ElementFromString(show['long_description']).text_content()
			else:
				show_content = HTML.ElementFromString(show['long_description']).text_content()
			show_title = show['title']

			if show['subscription_only'] == True and Dict['premium'] == False:
				oc.add(DirectoryObject(
					key = Callback(Unauthorized),
					title = show_title,
					summary = show_content,
					thumb = Resource.ContentsOfURLWithFallback(show['preview_image']),
					tagline = show['short_description']
				))
			else:
				show_url = MEDIAURL % show['video_url'].split('/')[-1].replace('.m3u8','')
				oc.add(VideoClipObject(
					url = show_url,
					title = show_title,
					summary = show_content,
					duration = int(show['duration']) * 1000,
					thumb = Resource.ContentsOfURLWithFallback(show['preview_image']),
					tagline = show['short_description']
				))
		
		# Handle playtube video objects
		elif type == 'video_meta':
			video_meta = item['video_meta']
			# Gametrailers.com Videos are included in results, these do not caontain a valid video id, so we make sure only those with one are listed
			if len(str(video_meta['riptide_video_id'])) == 32:
				video_url = MEDIAURL % video_meta['riptide_video_id']
				oc.add(VideoClipObject(
					url = video_url,
					title = video_meta['title'],
					summary = video_meta['description'],
					duration = int(video_meta['duration']) * 1000,
					thumb = Resource.ContentsOfURLWithFallback(video_meta['img_url'])
				))

	# End of Parse function appends 'NEXT' button if more items are present
	total_items = int(rawfeed['total_entries'])
	start_index = (page - 1) * ITEMS_PER_PAGE + 1

	if (start_index + ITEMS_PER_PAGE) < total_items:
		if query != '':
			oc.add(NextPageObject(
				key = Callback(Parser, content = content, page = page + 1, query = query), 
				title = "NEXT",
				thumb = R(IC_NEXT),
				summary = NEXT_SUMMARY
			))
		else:
			oc.add(NextPageObject(
				key = Callback(Parser, content = content, page = page + 1), 
				title = "NEXT",
				thumb = R(IC_NEXT),
				summary = NEXT_SUMMARY
			))

	if len(oc) < 1:
		return ObjectContainer(header='Error', message='Keine Items gefunden')
	else:
		return oc


@route(PREFIX + '/mediafromurl')
def GetMediaFromURL(title, url):
	title = unicode(title, "utf-8")
	oc = ObjectContainer(title2=title, replace_parent=False, no_cache = True)
	
	data = JSON.ObjectFromURL(url, cacheTime=0)['post']['body']

	# Handle audio files in posts
	if "rtaudio" in data:
		audios = REGEX_AUDIO.findall(data)
		for audio in audios:
			audio_meta = JSON.ObjectFromURL(AUDIOAPIURL % audio, cacheTime=3600.0)['audio_meta']
			oc.add(TrackObject(
				title = audio_meta['title'],
				summary = audio_meta['description'],
				url = MEDIAURL % audio,
				thumb = R(IC_PC)
			))
	
	# Handle Videos
	if "riptide" in data:
		videos = REGEX_VIDEO.findall(data)
		if Prefs['reverse_order'] == True:
			videos.reverse()
		for video in videos:
			video_meta = JSON.ObjectFromURL(VIDEOAPIURL % video, cacheTime=3600.0, timeout = 120.0)['video_meta']
			video_url = MEDIAURL % video_meta['riptide_video_id']
			oc.add(VideoClipObject(
				url = video_url,
				title = video_meta['title'],
				summary = video_meta['description'],
				duration = int(video_meta['duration']) * 1000,
				thumb = Resource.ContentsOfURLWithFallback(video_meta['img_url'])
			))
	
	# Handle embedded YouTube Videos:
	if "youtube://" in data:
		videos = REGEX_YOUTUBE.findall(data)
		for video in videos:
			oc.add(VideoClipObject(
				url = 'http://' + video,
				title = 'YouTube Video'
			))

	# Handle galleries in posts
	if "gallery:" in data:
		galleries = REGEX_GALLERY.findall(data)
		for gallery in galleries:
			meta = JSON.ObjectFromURL(GALLERYAPIURL % gallery, cacheTime=3600.0, timeout = 120.0)['gallery']
			name = 'gallery:' + gallery
			oc.add(PhotoAlbumObject(
				url = MEDIAURL % name,
				title = meta['title'],
				summary = 'Eine Gallerie',
				thumb = Resource.ContentsOfURLWithFallback(meta['images'][0]['image_url']),
				tagline = meta['title']
			))
	
	if len(oc) < 1:
		return ObjectContainer(header='Error', message='Keine Videos gefunden')
	else:
		return oc	

		
@route(PREFIX + '/unauthorized')
def Unauthorized():
	return MessageContainer(
		"Error",
		"Um auf diesen Inhalt zuzugreifen brauchst du\nein 1UP Abbonement, du kannst es mit der iOS oder\nAndroid App erwerben. Wenn du korrekte Daten in den\nEinstellungen angegeben hast checke\nbitte Username und Passwort"
	)

def ResetDict():
	Dict.Reset()
	Dict.Save()
	# Woraround because Dict.Reset() is not working
	Dict['logged_in'] = False
	Dict['premium'] = False
	Dict['auth_header'] = ''
	del HTTP.Headers['Authorization']
	Dict.Save()
