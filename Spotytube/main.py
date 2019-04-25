# coding=utf-8


# [START app]
import time
import logging
from jinja_utils import print_playlists, print_tracks
from spotify_utils import get_tracks_from_playlist, search_playlists, request_token_spotify
import requests_toolbelt.adapters.appengine
from flask import Flask, session, render_template, request, redirect
from youtube_utils import request_code_youtube, request_token_youtube, create_playlist, search_track, add_track

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app = Flask(__name__)
app.secret_key = "super secret key"


@app.route('/')
def index():
    spotify_token = session.get('spotify_token')
    if spotify_token is None:
        # Si no hay token
        return login_spotify()
    else:
        if is_spotify_token_expired(spotify_token):
            return login_spotify()

    return render_template('header.html', template_selector=0)


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
    playlist2search = request.args.get("id")
    type_seach = request.args.get('typesearch')
    template_playlist_names = []
    if playlist2search is None:
        if type_seach is not "name":
            to_search = request.args.get('search')
            list_playlist = search_playlists(spotify_token, to_search)
            template_playlist_names = print_playlists(list_playlist)

    return render_template('header.html', playlist_names=template_playlist_names,
                           template_selector=0)


@app.route('/ShowTracks', methods=['GET'])
def show_tracks():
    spotify_token = session['spotify_token']['access_token']
    playlist2search = request.args.get("id")

    tracks = get_tracks_from_playlist(spotify_token, playlist2search)
    template_tracks = print_tracks(tracks)

    return render_template('header.html', tracks_names=template_tracks, template_selector=1)


@app.route('/LoginGoogle')
def login_google():
    response = request_code_youtube()
    if response.status_code == 200:
        return redirect(str(response.url))


@app.route('/oauth2callback')
def oauthcallback_google():
    # Get code
    code = request.args.get('code')
    access_token = request_token_youtube(code)
    session['yt_token'] = access_token
    redirect('/')


@app.route('/Playlist')
def create_playlist_yt():
    yt_token = session.get('yt_token')
    playlist_id = create_playlist(yt_token, 'Ed Sheeran')
    video_id = search_track(yt_token, 'Perfect')
    add_track(yt_token, playlist_id, video_id)


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
# [END app]
