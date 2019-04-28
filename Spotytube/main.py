# coding=utf-8


# [START app]
import time
import logging
import pprint
import re

from jinja_utils import print_playlists, print_tracks
from spotify_utils import get_tracks_from_playlist, search_playlists, request_token_spotify, \
    get_playlist
import requests_toolbelt.adapters.appengine
from flask import Flask, session, render_template, request, redirect
from youtube_utils import request_code_youtube, request_token_youtube, create_playlist, add_video, search_best_video

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app = Flask(__name__)
app.secret_key = "super secret key"
template_tracks = None


@app.route('/')
def index():
    spotify_token = session.get('spotify_token')
    if spotify_token is None:
        # Si no hay token
        return login_spotify()
    else:
        if is_spotify_token_expired(spotify_token):
            return login_spotify()

    return render_template('base.html', template_selector=0)


@app.route('/LoginSpotify')
def login_spotify():
    logging.debug('ENTERING LoginAndAuthorizeHandler --->')

    # Step 1: Obtaining a request token
    token_info = _get_access_token()

    # and store  values
    session['spotify_token'] = token_info
    return index()


@app.route('/SearchSpotify', methods=['GET'])
def search_spotify():
    spotify_token = session['spotify_token']['access_token']
    type_search = request.args.get('typesearch')
    to_search = request.args.get('search')

    if type_search == 'name':
        list_playlist = search_playlists(spotify_token, to_search)
        template_playlist_names = print_playlists(list_playlist)
        session['playlist_names'] = template_playlist_names
        return render_template('base.html', playlist_names=template_playlist_names,
                               template_selector=0)
    elif type_search == 'url':
        return show_tracks(to_search)


@app.route('/ShowTracks', methods=['GET'])
def show_tracks(to_search=None):
    spotify_token = session['spotify_token']['access_token']
    if to_search is None:
        playlist2search = request.args.get("id")
        playlist_names = session.get('playlist_names')
        playlist_name = ''
        for playlist in playlist_names:
            if playlist[2] == playlist2search:
                playlist_name = playlist[0]

        tracks = get_tracks_from_playlist(spotify_token, playlist2search)

        global template_tracks
        template_tracks = print_tracks(tracks)

    else:
        if is_spotify(to_search):
            playlist2search = get_playlist(spotify_token, to_search)
            if playlist2search['error'] is not None:
                return index()
            else:
                playlist_name = playlist2search['name']
                playlist_id = playlist2search['id']
                tracks = get_tracks_from_playlist(spotify_token, playlist_id)
                global template_tracks
                template_tracks = print_tracks(tracks)
        else:
            return index()
    return render_template('base.html', tracks_names=template_tracks, playlist_name=playlist_name,
                           template_selector=1)


@app.route('/LoginGoogle', methods=['GET'])
def login_google():
    yt_token = session.get('yt_token')
    if yt_token is None:
        # Si no hay token
        response = request_code_youtube()
        if response.status_code == 200:
            return redirect(str(response.url))
    else:
        return create_playlist_yt()


@app.route('/oauth2callback')
def oauthcallback_google():
    # Get code
    code = request.args.get('code')
    access_token = request_token_youtube(code)
    session['yt_token'] = access_token

    return create_playlist_yt()


@app.route('/Playlist')
def create_playlist_yt():
    yt_token = session.get('yt_token')
    # pruebas, solo el primer video
    track_num1 = template_tracks[0]
    best_video = search_best_video(yt_token, track_num1)
    pprint.pprint(best_video)
    # playlist_id = create_playlist(yt_token, 'Ed Sheeran')

    # add_video(yt_token, playlist_id, video_id)
    return 'primer video:\n' + \
           '<p> channel title: ' + str(best_video['snippet']['channelTitle']) + '</p>' + \
           '<p> title: ' + str(best_video['snippet']['title']) + '</p>'


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500


# [Métodos para renovación de cookie]
def is_spotify_token_expired(token_info):
    now = int(time.time())
    return token_info['expires_at'] - now < 60


def _add_custom_values_to_token_info(token_info):
    token_info['expires_at'] = int(time.time()) + token_info['expires_in']
    return token_info


def _get_access_token():
    token_info = request_token_spotify()
    token_info = _add_custom_values_to_token_info(token_info)

    # pprint.pprint(token_info)
    token_info = token_info

    return token_info


#
def is_spotify(raw_song):
    return re.search(r'https://open.spotify.com/playlist/([a-z|0-9|A-Z]*)', raw_song)
# [END app]
