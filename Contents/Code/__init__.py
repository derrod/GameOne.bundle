# GameOne.de Plex Plugin
# by Rodney <https://github.com/derrod>

PREFIX = "/video/gameone"

NAME = 'Game One'

# Icons
ART = 'art-default.jpg'
ICON = 'icon-default.png'
IC_BLOG = 'icon_blog.png'
IC_PUP = 'icon_1up.png'
IC_SEARCH = 'icon_search.png'
IC_NEXT = 'icon_next.png'
IC_PC = 'icon_podcast.png'
IC_TV = 'icon_tv.png'
IC_ACC = 'icon_account.png'
IC_TV_SEARCH = 'icon_search_tv.png'

# The API URL's to fetch metadata for videos and audio files.
VIDEOAPIURL = "https://gameone.de/videos/%s.json"
AUDIOAPIURL = "https://gameone.de/audios/%s.json"

# This is a nonexistant url for handling video and audio files because there isn't an universal URL otherwise
MEDIAURL = "http://media.gameone.de/%s"

# All videos below a certain ID/Before a certain Date are max. 360p,
# this URL will be used to tell the URL Service that the video is only 360p
SDMEDIAURL = "http://sd.media.gameone.de/%s"

# Headers of the official App, not all are necessary but I kept it close to the original
HTTP.Headers['User-Agent'] = 'GameOne/323 CFNetwork/609 Darwin/13.0.0'
HTTP.Headers['X-G1APP-DEVICEINFO'] = 'iPhone3,1_6.0'
HTTP.Headers['X-G1APP-VERSION'] = '2.0.1(323)'
HTTP.Headers['X-G1APP-APPIDENTIFIER'] = 'de.gameone.iphone'
HTTP.Headers['X-G1APP-IDENTIFIER'] = '824BAB323627483698C844E2CC978D06'

# Base URL of the website, we use https for all requests
BASEURL = 'https://gameone.de/'

# 8 Items is what the App uses, you can increase this but it might cause issues
# with loading times, also VideoObject view is buggy in Plex Home Theater
ITEMS_PER_PAGE = 8
TV_ITEMS_PER_PAGE = 8

# REGEX Patterns for Audio/Video/YouTube stuff inside of posts
REGEX_AUDIO = Regex(r'rtaudio:(.*)"')
REGEX_VIDEO = Regex(r'riptide:(.*)"')
REGEX_YOUTUBE = Regex(r'youtube://(.*)"')

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(PREFIX, MainMenu, NAME, ICON, ART)

	ObjectContainer.title1 = 'Game One'
	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)

	# One hour seems reasonable for images and feeds that are updated 1-2 times a day
	# You can turn it off if you experience problems with image loading
	HTTP.CacheTime = 3600.0
	# Cache should be cleared between seesion because not doing so seems to cause Issues
	HTTP.ClearCache()

	Initialize()

def ValidatePrefs():
	ResetDict()
	Initialize()


def Initialize():
	# Clunky login funtion
	u = Prefs['username']
	p = Prefs['password']
	if( u and p ):
		if Dict['logged_in'] == True:
			# Check Login
			url = BASEURL + 'users/me.json'
			HTTP.Headers['Authorization'] = Dict['auth_header']
			login = JSON.ObjectFromURL(url, cacheTime=0.0)
			if 'user' not in login:
				Dict['logged_in'] = False
				Dict['premium'] = False
				Dict['auth_header'] = ''
			else:
				if login['user']['subscription'] == 1:
					Dict['premium'] = True
				else:
					Dict['premium'] = False
		else:
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
				Dict['logged_in'] = False
				Dict['premium'] = False
				Dict['auth_header'] = ''
	else:
		Dict['logged_in'] = False
		Dict['premium'] = False
		Dict['auth_header'] = ''	
	Dict.Save()
	
		
def MainMenu():
	# Text as title of the account item to provide feedback on login status
	if Dict['logged_in'] == True:
		if Dict['premium'] == True:
			status_text = 'Eingeloggt - 1UP Aktiv'
		else:
			status_text = 'EIngeloggt - 1UP Inaktiv'
	else:
		status_text = 'Nicht Eingeloggt'
	
	oc = ObjectContainer(no_cache = True)
	oc.add(DirectoryObject(key = Callback(ParsePosts, title = 'Blogposts', content = 'blog'), title = 'Blog', thumb = R(IC_BLOG), summary = 'Blog'))
	oc.add(DirectoryObject(key = Callback(ParseTVShows, title = 'TV Sendungen'), title = 'TV Sendungen', thumb = R(IC_TV), summary = 'TV Episoden'))
	
	# We don't want people to get into the premium menu if they don't have a subscription.
	# Even if someone bypasses this (which isn't that hard to do obv.) the server won't send
	# the ID's of media to the client if the account doesn't have a subscription.
	# This is just a little message for the user as to why they can't access any content there.
	if Dict['premium'] == False:
		oc.add(DirectoryObject(key = Callback(Unauthorized), title = '1UP Inhalte', thumb = R(IC_PUP), summary = 'Appklusiver Content'))
	else:
		oc.add(DirectoryObject(key = Callback(ParsePosts, title = 'Appklusiv', content = 'premium'), title = '1UP Inhalte', thumb = R(IC_PUP), summary = 'Appklusiver Content'))

	oc.add(DirectoryObject(key = Callback(ParsePosts, title = 'Podcasts', content = 'podcast'), title = 'Podcasts', thumb = R(IC_PC), summary = 'Podcasts'))
	oc.add(InputDirectoryObject(key = Callback(Search, title='Suche'), title = 'Blogsuche', prompt = 'Suchbegriff eingeben', thumb = R(IC_SEARCH), summary = 'Suche in Blogposts'))
	oc.add(InputDirectoryObject(key = Callback(ParseTVShows, title='Suche in TV'), title = 'TV Suche', prompt = 'Suchbegriff eingeben', thumb = R(IC_TV_SEARCH), summary = 'Suche in TV Episoden'))
	oc.add(DirectoryObject(key = Callback(Account), title = 'Mein Account: ' + status_text, thumb = R(IC_ACC), summary = 'Accountinformationen'))
	oc.add(PrefsObject(title = 'Einstellungen', summary = 'Einstellungen'))
	return oc

@route(PREFIX + '/account')
def Account():
	# Just returns a checkbox that returns your name and if your subscription is still valid
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

@route(PREFIX + '/posts')
def ParsePosts(title, content, page = 1):
	# If routes are used page is not an int anymore
	page = int(page)
	oc = ObjectContainer(title2=title, replace_parent=False, no_cache = True)

	if content == "blog":
		content_url = BASEURL + 'app/posts/blog.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
	elif content == "premium":
		content_url = BASEURL + 'app/blog/premium.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
	elif content == "podcast":
		content_url = BASEURL + 'app/posts/podcast.json?page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)
	else:
		content_url = content + '&page=' + str(page) + '&per_page=' + str(ITEMS_PER_PAGE)

	try:
		rawfeed = JSON.ObjectFromURL(content_url, cacheTime=0)
	except:
		return ObjectContainer(header='Error', message='Keine Videos gefunden')

	for item in rawfeed['items']:
		post = item['post']
		raw_post_content = post['body']
		
		# Plex Home Theater doesn't display the 'tagline' field, so we just put it before the text content
		# of a blog post
		if Client.Platform == 'Plex Home Theater':
			post_content = post['excerpt'] + '\n\n' + HTML.ElementFromString(raw_post_content).text_content()
		else:
			post_content = HTML.ElementFromString(raw_post_content).text_content()
		post_title = post['title']
		
		# URLs are currently all blogposts as this fucntion does not parse PlayTube ot TV Shows so we can safely use this.
		posturl =  BASEURL + '/blog/' + str(post['id']) +'.json'

		# Same as in the main menu, just return a message if you aren't allowed to access that content.
		if post['subscription_only'] == True and Dict['premium'] == False:
			cb = Callback(Unauthorized)
		else:
			cb = Callback(GetMediaFromData, title = post_title, url = posturl)
		
		oc.add(DirectoryObject(
			key = cb,
			title = post_title,
			summary = post_content,
			thumb = Resource.ContentsOfURLWithFallback(post['image_url']),
			tagline = post['excerpt']
		))


	total_posts = int(rawfeed['total_entries'])
	start_index = (page - 1) * ITEMS_PER_PAGE + 1

	if (start_index + ITEMS_PER_PAGE) < total_posts:
		oc.add(NextPageObject(
			key = Callback(ParsePosts, title = title, content = content, page = page + 1), 
			title = "NEXT",
			thumb = R(IC_NEXT)
		))

	if len(oc) < 1:
		return ObjectContainer(header='Error', message='Keine Videos gefunden')
	else:
		return oc

@route(PREFIX + '/shows')
def ParseTVShows(title, page = 1, query = ''):
	# If routes are used page is not an int anymore
	page = int(page)

	if len(query) > 3:
		content_url = BASEURL + '/search/shows.json?q=' + query + '&page=' + str(page) + '&per_page=' + str(TV_ITEMS_PER_PAGE)
		title = 'Suche nach "' + query + '" in TV Shows'
	else:
		content_url = BASEURL + 'tv.json?page=' + str(page) + '&per_page=' + str(TV_ITEMS_PER_PAGE)

	oc = ObjectContainer(title2=title, replace_parent=False, no_cache = True)
	
	try:
		rawfeed = JSON.ObjectFromURL(content_url, cacheTime=0)
	except:
		return ObjectContainer(header='Error', message='Keine Videos gefunden')
	
	for item in rawfeed['items']:
		show = item['tv_show']
		if Client.Platform == 'Plex Home Theater':
			show_content = show['short_description'] + '\n\n' + HTML.ElementFromString(show['long_description']).text_content()
		else:
			show_content = HTML.ElementFromString(show['long_description']).text_content()
		
		show_title = show['title']
		
		# For tv episodes we can determine if it's HD by using the episode number.
		if show['episode'] < 250:
			show_url = SDMEDIAURL % show['video_url'].split('/')[-1].replace('.m3u8','')
		else:
			show_url = MEDIAURL % show['video_url'].split('/')[-1].replace('.m3u8','')
			
		# This can be probably changed, but I didn't try out if VideoClipObjects can be used to show a message box yet.
		if show['subscription_only'] == True and Dict['premium'] == False:
			oc.add(DirectoryObject(
				key = Callback(Unauthorized),
				title = show_title,
				summary = show_content,
				thumb = Resource.ContentsOfURLWithFallback(show['preview_image']),
				tagline = show['short_description']
			))
		else:
			oc.add(VideoClipObject(
				url = show_url,
				title = show_title,
				summary = show_content,
				duration = int(show['duration']) * 1000,
				thumb = Resource.ContentsOfURLWithFallback(show['preview_image']),
				tagline = show['short_description']
			))

	total_posts = int(rawfeed['total_entries'])
	start_index = (page - 1) * TV_ITEMS_PER_PAGE + 1

	if (start_index + TV_ITEMS_PER_PAGE) < total_posts:
		oc.add(NextPageObject(
			key = Callback(ParseTVShows, title = title, page = page + 1), 
			title = "NEXT",
			thumb = R(IC_NEXT)
		))

	if len(oc) < 1:
		return ObjectContainer(header='Error', message='Keine Videos gefunden')
	else:
		return oc

@route(PREFIX + '/mediafromurl')
def GetMediaFromData(title, url):
	oc = ObjectContainer(title2=title, replace_parent=False, no_cache = True)
	
	data = JSON.ObjectFromURL(url, cacheTime=0)['post']['body']

	# Handle audio ids
	if "rtaudio" in data:
		audios = REGEX_AUDIO.findall(data)
		for audio in audios:
			audio_meta = JSON.ObjectFromURL(AUDIOAPIURL % audio, cacheTime=CACHE_1HOUR)['audio_meta']
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
			video_meta = JSON.ObjectFromURL(VIDEOAPIURL % video, cacheTime=CACHE_1HOUR, timeout = 120.0)['video_meta']
			# Here we split HD and non-HD Videos, luckily the id is just a increaing number so we actually can use it to determine whether a Video is HD or not!
			if video_meta['id'] > 636600:
				video_url = MEDIAURL % video_meta['riptide_video_id']
			else:
				video_url = SDMEDIAURL % video_meta['riptide_video_id']

			oc.add(VideoClipObject(
				url = video_url,
				title = video_meta['title'],
				summary = video_meta['description'],
				duration = int(video_meta['duration']) * 1000,
				thumb = Resource.ContentsOfURLWithFallback(video_meta['img_url'])
			))
	
	# Create Link for embedded YouTube Videos, because there is no code to grab metadata (title) just give it a generic one
	if "youtube://" in data:
		videos = REGEX_YOUTUBE.findall(data)
		for video in videos:
			oc.add(VideoClipObject(
				url = 'http://' + video,
				title = 'YouTube Video'
			))
	
	if len(oc) < 1:
		return ObjectContainer(header='Error', message='Keine Videos gefunden')
	else:
		return oc

# Search just creates a new url as content variable which the ParsePosts function handles accordingly
@route(PREFIX + '/search')
def Search(query = '', title = ''):
	url = BASEURL + 'search/blog.json?q=' + query
	title = 'Suche nach "' + query + '"'
	return ParsePosts(title = title, content = url)

def Unauthorized():
	return MessageContainer(
		"Error",
		"Um auf diesen Inhalt zuzugreifen brauchst du\nein 1UP Abbonement, du kannst es mit der iOS oder\nAndroid App erwerben. Wenn du korrekte Daten in den\nEinstellungen angegeben hast checke\nbitte Username und Passwort"
	)
	

def ResetDict():
	Dict.Reset()
	Dict.Save()
	# Woraround because Dict.Reset() is not working :(
	Dict['logged_in'] = False
	Dict['premium'] = False
	Dict['auth_header'] = ''
	Dict.Save()
