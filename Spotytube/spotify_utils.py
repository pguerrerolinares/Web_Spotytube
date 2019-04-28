import base64
import requests

# Consumer Api Keys Spotify
consumer_key = 'cb169bdfb3884a03ba9c68932f87285b'
consumer_secret = '5ad8b30856c64e569685769261fa2689'
prefix = 'https://api.spotify.com/v1/'


def request_token_spotify():
    authorization = base64.standard_b64encode(consumer_key + ':' + consumer_secret)

    headers = {'User-Agent': 'Google App Engine',
               'Authorization': 'Basic {0}'.format(authorization)}
    data = {'grant_type': 'client_credentials'}

    spotify_token_url = 'https://accounts.spotify.com/api/token'

    response = requests.post(spotify_token_url, headers=headers, data=data)

    if response.status_code != 200:
        print response.reason
    token_info = response.json()
    return token_info


def _request(spotify_token, url, data):
    """
    :param spotify_token: 
    :param url: 
    :param data: 
    :return: 
    """
    headers = {'Authorization': 'Bearer {0}'.format(spotify_token),
               'Content-Type': 'application/json'}

    data = dict(params=data)
    response = requests.get(url, headers=headers, **data)
    if response.text and len(response.text) > 0 and response.text != 'null':
        return response.json()
    else:
        return None


def _get(spotify_token, url, **kwargs):
    """
    :param spotify_token:
    :param url:
    :param kwargs:
    :return:
    """
    return _request(spotify_token, url, kwargs)


def _search(spotify_token, query, limit=10, offset=0, type=None, market=None):
    """
    :param spotify_token:
    :param query:
    :param limit:
    :param offset:
    :param type:
    :param market:
    :return:
    """
    return _get(spotify_token, prefix + 'search', q=query, limit=limit, offset=offset,
                type=type, market=market)


def search_playlists(spotify_token, playlist):
    """
    :param spotify_token:
    :param playlist:
    :return:
    """
    return _search(spotify_token, query=playlist, type='playlist', limit=9, market='ES', offset=0)


def playlist_tracks(spotify_token, playlist_id=None, fields=None,
                    limit=100, offset=0, market=None):
    """
    :param spotify_token:
    :param playlist_id:
    :param fields:
    :param limit:
    :param offset:
    :param market:
    :return:
    """
    plid = _extract_spotify_id(playlist_id)

    return _get(spotify_token, prefix + 'playlists/{0}/tracks'.format(plid),
                limit=limit, offset=offset, fields=fields,
                market=market)


def get_tracks_from_playlist(spotify_token, playlist_url):
    """
    :param spotify_token:
    :param playlist_url:
    :return:
    """
    return playlist_tracks(spotify_token, playlist_url, fields="items")['items']


def get_playlist(spotify_token, playlist_url):
    plid = _extract_spotify_id(playlist_url)
    return _get(spotify_token, prefix + 'playlists/{0}'.format(plid), market='ES')


def _extract_spotify_id(raw_string):
    """
    :param raw_string:
    :return:
    """
    # print raw_string
    # Input string is an HTTP URL
    if raw_string.endswith("/"):
        raw_string = raw_string[:-1]
    to_trim = raw_string.find("?")

    if not to_trim == -1:
        raw_string = raw_string[:to_trim]
    splits = raw_string.split("/")

    spotify_id = splits[-1]

    return spotify_id
