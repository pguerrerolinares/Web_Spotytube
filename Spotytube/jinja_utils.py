# coding=utf-8
def print_playlists(list_playlist):
    playlist_names = []
    if list_playlist['playlists']['next'] is not None:
        items = list_playlist['playlists']['items']

        for x in range(0, len(items), 1):
            array = []
            array.append(items[x]['name'])
            array.append(items[x]['images'][0]['url'])
            array.append(items[x]['id'])

            playlist_names.append(array)

    return playlist_names


def print_tracks(tracks):
    """
    Posiciones de la array:
    0 -> nombre canción
    1 -> nombre artista
    2 -> nombres de artistas
    3 -> duración(s)
    4 -> url imagen
    5 -> url preview song
    :param tracks:
    :return:
    """
    tracks_names = []
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

        array.append(current_track['duration_ms'] / 1000)
        array.append(current_track['album']['images'][0]['url'])
        array.append(current_track['preview_url'])

        tracks_names.append(array)

    return tracks_names
