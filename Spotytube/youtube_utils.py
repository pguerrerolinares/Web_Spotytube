# Google keys
import json
import requests
import urllib

google_secret_key = "1FfMRgteyw6T8b46872U0dgb"
client_id = "990115409802-q9o1n9f5hab5lrlg84l21u2si23m90ph.apps.googleusercontent.com"


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

    json_respuesta = json.loads(response.content)
    # print json_respuesta
    return json_respuesta['access_token']


def search_track(yt_token, tittle):
    params = {'part': 'snippet',
              'order': 'relevance',
              'q': tittle,
              'type': 'video'}
    params_encoded = urllib.urlencode(params)

    headers = {'Authorization': 'Bearer {0}'.format(yt_token),
               'Accept': 'application/json'}

    response = requests.get("https://www.googleapis.com/youtube/v3/search", headers=headers,
                            params=params_encoded)

    json_respuesta = json.loads(response.content)
    items = json_respuesta['items']
    return items[0]['id']['videoId']


def create_playlist(yt_token, name):
    headers = {'Authorization': 'Bearer {0}'.format(yt_token),
               'Accept': 'application/json',
               'Content-Type': 'application/json'}

    params = {'part': 'snippet'}
    params_encoded = urllib.urlencode(params)

    data = {'snippet': {'title': name}}
    jsondata = json.dumps(data)
    response = requests.post('https://www.googleapis.com/youtube/v3/playlists?' + params_encoded,
                             headers=headers, data=jsondata)
    json_respuesta = json.loads(response.content)
    return json_respuesta['id']


def add_track(yt_token, playlist_id, video_id):
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
    return requests.post('https://www.googleapis.com/youtube/v3/playlistItems?' + params_encoded,
                         headers=headers, data=jsondata)
