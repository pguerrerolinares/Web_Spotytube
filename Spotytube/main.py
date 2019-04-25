# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import time

import logging
import os

import base64
import json
import pprint

import urllib

from spotytube_utils import get_tracks_from_playlist, search_playlists
from webapp2_extras import sessions
import webapp2
import jinja2

import requests
import requests_toolbelt.adapters.appengine

from flask import Flask, session, render_template, request, redirect, url_for, flash

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app = Flask(__name__)
app.secret_key = "super secret key"


def is_spotify_token_expired(token_info):
    now = int(time.time())
    return token_info['expires_at'] - now < 60


def _request_token():
    # Consumer Api Keys Spotify
    consumer_key = 'cb169bdfb3884a03ba9c68932f87285b'
    consumer_secret = '5ad8b30856c64e569685769261fa2689'

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


def _add_custom_values_to_token_info(token_info):
    token_info['expires_at'] = int(time.time()) + token_info['expires_in']
    return token_info


def _get_access_token():
    token_info = _request_token()
    token_info = _add_custom_values_to_token_info(token_info)

    # pprint.pprint(token_info)
    token_info = token_info

    return token_info


@app.route('/LoginSpotify')
def login_spotify():
    logging.debug('ENTERING LoginAndAuthorizeHandler --->')

    # Step 1: Obtaining a request token
    token_info = _get_access_token()

    # and store  values
    session['spotify_token'] = token_info
    return index()


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


def _print_playlists(list_playlist):
    if list_playlist['playlists']['next'] is not None:
        items = list_playlist['playlists']['items']
        session['playlist_names'] = []

        for x in range(0, len(items), 1):
            array = []
            array.append(items[x]['name'])
            array.append(items[x]['images'][0]['url'])
            array.append(items[x]['id'])

            session['playlist_names'].append(array)
        # pprint.pprint(session['playlist_names'])


@app.route('/ShowTracks', methods=['GET'])
def show_tracks():
    spotify_token = session['spotify_token']['access_token']
    playlist2search = request.args.get("id")

    tracks = search_playlists(spotify_token, playlist2search)
    _print_tracks(tracks)
    template_tracks = session.get('tracks_names')

    return render_template('header.html', tracks_names=template_tracks, template_selector=1)


def _print_tracks(tracks):
    session['tracks_names'] = []
    for track in tracks:
        current_track = track['track']
        # pprint.pprint(current_track)
        array = []
        array.append(current_track['name'])

        track_artists = []
        for artist in current_track['artists']:
            track_artists.append(artist['name'])
        featured_artists = ';'.join(track_artists)
        artist = featured_artists.split(';')[0]
        array.append(artist)

        album_artists = []
        for artist in current_track['album']['artists']:
            album_artists.append(artist['name'])
        array.append(album_artists)

        array.append(current_track['duration_ms'])
        array.append(current_track['album']['images'][0]['url'])
        array.append(current_track['preview_url'])

        session['tracks_names'].append(array)


@app.route('/SearchSpotify', methods=['GET'])
def search_spotify():
    spotify_token = session['spotify_token']['access_token']
    playlist2search = request.args.get("id")
    type_seach = request.args.get('typesearch')

    if playlist2search is None:
        if type_seach is not "name":
            to_search = request.args.get('search')
            list_playlist = search_playlists(spotify_token, to_search)
            _print_playlists(list_playlist)
    template_playlist_names = session.get('playlist_names')

    return render_template('header.html', playlist_names=template_playlist_names,
                           template_selector=0)


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
