# coding=utf-8
# Google keys
from bs4 import BeautifulSoup
import isodate
import json
import pprint
import re
import requests
import urllib

google_secret_key = "1FfMRgteyw6T8b46872U0dgb"
client_id = "990115409802-q9o1n9f5hab5lrlg84l21u2si23m90ph.apps.googleusercontent.com"
prefix_yt = "https://www.googleapis.com/youtube/v3/"

#client_id = "990115409802-2ui236qmc7om12c8b2hm65ad8cakmqmb.apps.googleusercontent.com"
#google_secret_key = "U288IasNakebHr3cQDyWYz0v"


def request_code_youtube():
    # Enviar una solicitud de autenticacion a google
    redirect_uri = 'http://localhost:8080/oauth2callback'  # Localhost
    # redirect_uri = 'http://spotytube.appspot.com/oauth2callback'

    server = 'https://accounts.google.com/o/oauth2/v2/auth'

    params = {'client_id': client_id,
              'response_type': 'code',
              'scope': 'https://www.googleapis.com/auth/youtube',
              'redirect_uri': redirect_uri,
              'access_type': 'offline'}

    headers = {'User-Agent': 'Google App Engine'}

    params_encoded = urllib.urlencode(params)

    return requests.get(server, headers=headers, params=params_encoded)


def request_token_youtube(code):
    # Get token
    redirect_uri = 'http://localhost:8080/oauth2callback'  # Localhost

    headers = {
        'Host': 'www.googleapis.com',
        'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': google_secret_key,
        'grant_type': 'authorization_code'
    }
    response = requests.post("https://www.googleapis.com/oauth2/v4/token", headers=headers, data=data)
    pprint.pprint(response.content)

    json_respuesta = json.loads(response.content)
    return json_respuesta['access_token']


def _request(yt_token, url, data):
    """
    :param yt_token:
    :param url:
    :param data:
    :return:
    """
    headers = {'Authorization': 'Bearer {0}'.format(yt_token),
               'Content-Type': 'application/json'}

    data = dict(params=data)
    response = requests.get(url, headers=headers, **data)
    if response.text and len(response.text) > 0 and response.text != 'null':
        return response.json()
    else:
        return None


def _get(yt_token, url, **kwargs):
    """
    :param yt_token:
    :param url:
    :param kwargs:
    :return:
    """
    return _request(yt_token, url, kwargs)


def _search_video_query(yt_token, query, part='snippet,id', order='relevance', type='video', maxResults=10):
    """
    :param yt_token:
    :param query:
    :param part:
    :param order:
    :param type:
    :param maxResults:
    :param id:
    :return:
    """
    query = re.sub(r'\((feat.|)(.*?)\)', '', query)
    return _get(yt_token, prefix_yt + 'search', q=query, part=part, order=order,
                type=type, maxResults=maxResults)['items']


def _search_videos_id(yt_token, videos_ids, part='contentDetails', id=None):
    """
    :param yt_token:
    :param videos_ids:
    :param part:
    :param id:
    :return:
    """
    id = ','.join(videos_ids)
    return _get(yt_token, prefix_yt + 'videos', part=part, id=id)['items']


def create_playlist(yt_token, name):
    headers = {'Authorization': 'Bearer {0}'.format(yt_token),
               'Accept': 'application/json',
               'Content-Type': 'application/json'}

    params = {'part': 'snippet'}
    params_encoded = urllib.urlencode(params)

    data = {'snippet': {'title': name}}
    jsondata = json.dumps(data)
    response = requests.post(prefix_yt + 'playlists?' + params_encoded,
                             headers=headers, data=jsondata)
    json_respuesta = json.loads(response.content)
    print json_respuesta
    return json_respuesta['id']


def add_video(yt_token, playlist_id, video_id):
    headers = {'Authorization': 'Bearer {0}'.format(yt_token),
               'Accept': 'application/json',
               'Content-Type': 'application/json'}
    params = {'part': 'snippet'}
    params_encoded = urllib.urlencode(params)

    data = {'snippet': {'playlistId': playlist_id,
                        'resourceId': {
                            'videoId': video_id,
                            'kind': 'youtube#video'}
                        }
            }
    jsondata = json.dumps(data)
    return requests.post(prefix_yt + 'playlistItems?' + params_encoded,
                         headers=headers, data=jsondata)


def search_best_video(yt_token, track):
    artist = 1
    name = 0
    query = '{0} - {1}'.format(track[artist], track[name])
    video_selected_dict = {}
    items1 = _search_video_query(yt_token, query)
    videos_ids = []
    for video in items1:
        videos_ids.append(video['id']['videoId'])
    items2 = _search_videos_id(yt_token, videos_ids)

    selected_video = [{}, -100]

    for i in range(0, len(items1)):
        video1 = items1[i]
        video2 = items2[i]
        duration = video2['contentDetails']['duration']
        video1.__setitem__('duration', isodate.parse_duration(duration).total_seconds())
        video_points = _attribute_meta_points(track, video1)

        if video_points > selected_video[1]:
            selected_video = [video1, video_points]

    if selected_video[1] >= 5:
        # print 'Video "{0}" tiene "{1}" puntos'.format(selected_video[0]['snippet']['title'], selected_video[1])
        video_selected_dict = selected_video[0]

    return video_selected_dict


def search_best_video_scrapping(track):
    name = 0
    artists = 2
    artist_main = track[artists][0]
    feat_artist_text = ''
    for feat_artist in track[artists]:
        if artist_main is not feat_artist:
            feat_artist_text += '+' + feat_artist

    full_link = None
    title = artist_main + '+' + track[name] + '+' + feat_artist_text
    hd = "&sp=EgIQAQ%253D%253D"
    t = title.replace('%', '%25').replace(' ', '%20').replace('&', '%26').replace('/', '%2F')
    url = 'https://www.youtube.com/results?search_query=' + t + hd + '&sp=EgIQAQ%253D%253D'
    items = requests.get(url).content

    items_parse = BeautifulSoup(items, "html.parser")

    max_attribute_point = -100

    best_video = None
    for x in items_parse.find_all(
            "div", {"class": "yt-lockup-dismissable yt-uix-tile"}
    ):
        y = x.find("div", class_="yt-lockup-content")

        link = y.find("a")["href"][-11:]
        z = y.find("a", class_="yt-uix-sessionlink spf-link")
        w = y.find("span", class_="yt-uix-tooltip yt-channel-title-icon-verified yt-sprite")
        title = y.find("a")["title"]

        videotime = x.find("span", class_="video-time").get_text().split(':')

        youtubedetails = {
            "link": link,
            "title": title,
            "duration": int(videotime[0]) * 60 + int(videotime[1]),
            "channel": z.string,
            "verified": w
        }

        tmp_max_att_point = _attribute_meta_points(track, youtubedetails)
        if tmp_max_att_point > max_attribute_point:
            max_attribute_point = tmp_max_att_point
            best_video = youtubedetails

    return best_video['link']


'''

    full_link = "youtube.com" + result
    print("http://" + full_link)
    '''


def _attribute_meta_points(track, video):
    points = 0
    artist = 1
    name = 0
    duration = 3
    video_verified = video['verified']
    fx_channel_name = video['channel'].lower()
    title = re.sub(r'[^\w\s]', '', video['title'].lower())
    title = re.sub(r'\((feat.|)(.*?)\)', '', title).replace('  ', ' ')
    fx_artist_name = re.sub(r'[^\w\s]', '', track[artist].lower())
    fx_track_name = re.sub(r'[^\w\s]', '', track[name].lower())
    fx_track_name = re.sub(r'\((feat.|)(.*?)\)', '', fx_track_name).replace('  ', ' ')

    # titutlo del video tiene nomre de la canción
    if fx_track_name in title:
        points += 20
    # titulo del video tiene el nombre del artista
    if fx_artist_name in title:
        points += 10

    # titulo del video tiene "official, oficial, ..."
    if re.search(r'[oO]f(f|)ici([a])l', title):
        points += 5

    if re.search(r'[oO]f(f|)ici([a])l audio', title) or re.search(r'[aA]udio [oO]f(f|)ici([a])l', title):
        if 'remix' in fx_track_name and 'remix' in title:
            points += 5

    if re.search(r'[oO]f(f|)ici(a)l [vV]ideo', title) or re.search(r'[vV]ideo [oO]f(f|)ici([a])l', title):
        if 'remix' in fx_track_name and 'remix' in title:
            points += 5

    if re.search(r'of(f|)ici([ae])l music (video|)', title):
        points += 5

    # Ozuna - única
    if re.search(r'{0}(\s|)([:\-])(\s|){1}'.format(fx_artist_name, fx_track_name), title):
        points += 5

    if 'live' not in fx_track_name and 'live' in title:
        points -= 10

    if 'cover' not in fx_track_name and 'cover' in title:
        points -= 10

    if 'acoustic' not in fx_track_name and 'acoustic' in title:
        points -= 10

    if 'edit' not in fx_track_name and 'edit' in title:
        points -= 5

    if not re.search(r'[rR]emix', fx_track_name) and re.search(r'[rR]emix', title):
        points -= 10

    if 'instrumental' not in fx_track_name and 'instrumental' in title:
        points -= 10
    # nombre del canal coincide con el artista
    if re.sub(r'[\W]+', '', fx_channel_name) == re.sub(r'[\W]+', '', fx_artist_name):
        points += 5
    if video_verified is not None:
        points += 10
    if fx_channel_name == fx_artist_name + 'vevo':
        points += 10

    dur_diff = int(video['duration'] - track[duration])
    points -= abs(dur_diff)

    return points
