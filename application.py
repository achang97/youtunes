# ./application.py

from flask import Flask, jsonify, make_response, request, session, redirect
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import isodate
import string
import random
import requests
import base64
import os
import urllib
import base64
import datetime
import boto3
from botocore.exceptions import ClientError
import tempfile
import pafy
from pydub import AudioSegment
from StringIO import StringIO
import configparser
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TALB, TPE1, TPE2, TIT2, error
import youtube_dl

KEYS = {}

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
RANDOM_STRING_LENGTH = 16
YOUTUBE_URL = 'https://www.youtube.com/watch?v='

SPOTIFY_BASE_URL = 'https://api.spotify.com'
SPOTIFY_REDIRECT = 'http://www.youtunes-downloader.com/spotifyCallback'
# SPOTIFY_REDIRECT = 'http://localhost:5000/spotifyCallback'
SPOTIFY_STATE_KEY = 'spotify_auth_state'
SPOTIFY_EXPIRATION = 3600

AWS_BUCKET_NAME = 'elasticbeanstalk-us-west-1-417250080989'
AWS_BUCKET_BASE_URL = 'https://s3-us-west-1.amazonaws.com/elasticbeanstalk-us-west-1-417250080989/'
AWS_MP3_PATH = 'resources/youtunes/mp3-files/'

FRONT_COVER = 3

MILLISECONDS_PER_SECOND = 1000

application = Flask(__name__, static_url_path='', static_folder='')
application.secret_key = 'Y\x16++D\xdf\xbeww\x9a\x01(\xe9\xd6\xc6\xa2\xaa\x97wDp\xa6\xd2\xd1n<\xafO\x93\xf8H\x82'


@application.route("/")
def index():
    # redirect to home page
    return redirect('/music-app.html')


def generate_random_string(size=RANDOM_STRING_LENGTH, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@application.route('/spotifyLogin', methods=['POST'])
def spotify_login():
    # check to see if session already has info
    if 'spotify_name' in session:
        return make_response('Already logged in!')

    state = generate_random_string()

    scope = 'user-read-private playlist-read-private user-follow-read user-read-currently-playing user-library-read user-top-read user-read-recently-played'
    info_obj = {'response_type': 'code', 'client_id': KEYS['SPOTIFY_CLIENT_ID'], 'scope': scope, 'redirect_uri': SPOTIFY_REDIRECT,
        'state': state
    }

    query_string = urllib.urlencode(info_obj)

    response = jsonify({'login_url' : 'https://accounts.spotify.com/authorize/?' + query_string})
    response.set_cookie(SPOTIFY_STATE_KEY, state)

    return response


@application.route('/spotifyCallback', methods=['GET'])
def spotify_callback():
    if 'spotify_name' in session:
        return make_response('Already logged in!')

    code = request.args.get('code')
    state = request.args.get('state')
    cookies = request.cookies
    
    storedState = cookies[SPOTIFY_STATE_KEY] if cookies else None

    if not state or state != storedState:
        # error
        return redirect('/music-app.html#!/home?' + urllib.urlencode({'error': 'Spotify failed to authenticate user. Please try again.'}))
    else:
        headers = {'Authorization': 'Basic ' + base64.b64encode(KEYS['SPOTIFY_CLIENT_ID'] + ':' + KEYS['SPOTIFY_CLIENT_SECRET'])}
        data = {
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT,
            'grant_type': 'authorization_code'
        }

        r = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        
        if r.status_code != 200:
            # failure
            return redirect('/music-app.html#!/home?' + urllib.urlencode({'error': 'Spotify failed to authenticate user. Please try again.'}))
        else:
            content = r.json()

            now = datetime.datetime.now()

            access_token = content['access_token']
            refresh_token = content['refresh_token']
            expires_in = content['expires_in']

            # get some information about user
            headers = {'Authorization': 'Bearer ' + access_token}
            r = requests.get(SPOTIFY_BASE_URL + '/v1/me', headers=headers)

            if r.status_code != 200:
                return redirect('/music-app.html#!/home?' + urllib.urlencode({'error': 'Spotify credentials were valid, but failed to fetch user information. Please try again.'}))

            content = r.json()
            images = content['images']
            if len(images) != 0:
                session['spotify_img_url'] = images[0]['url']


            # store all this information in session
            session['spotify_id'] = content['id']
            session['spotify_name'] = content['display_name']
            session['spotify_access_token'] = access_token
            session['spotify_refresh_token'] = refresh_token
            session['spotify_expiration'] = now + datetime.timedelta(seconds=expires_in)
            session['country'] = content['country']

            return redirect('/music-app.html#!/browse')


def spotify_refresh():
    # requesting access token from refresh token
    refresh_token = session['spotify_refresh_token']
    
    headers = {'Authorization': 'Basic ' + base64.b64encode(KEYS['SPOTIFY_CLIENT_ID'] + ':' + KEYS['SPOTIFY_CLIENT_SECRET'])}
    data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}

    now = datetime.datetime.now()
    r = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

    if r.status_code == 200:
        # replace the session id
        session['spotify_access_token'] = r.json()['access_token']
        session['spotify_expiration'] = now + datetime.timedelta(seconds=SPOTIFY_EXPIRATION)
        return True
    else:
        return False


@application.route('/spotifyLogout', methods=['POST'])
def spotify_logout():
    # just clear session info
    session.clear()

    return make_response('Logged out successfully.')


@application.route('/getSpotifyInfo', methods=['GET'])
def get_spotify_info():
    if 'spotify_name' not in session:
        return make_response('No Spotify user information.', 401)

    # check to see that access token is still valid
    if (datetime.datetime.now() > session['spotify_expiration']):
        success = spotify_refresh()
        if not success:
            return make_response('Failed to refresh token.', 400)

    # fetch information from session
    return jsonify({'name': session['spotify_name'], 'img_url': session['spotify_img_url']})


def make_spotify_get_request(endpoint, params={}):
    if 'spotify_name' not in session:
        return make_response('No Spotify user information.', 401), False

    # check to see that access token is still valid
    if (datetime.datetime.now() > session['spotify_expiration']):
        success = spotify_refresh()
        if not success:
            return make_response('Failed to refresh token.', 400), False

    headers = {'Authorization': 'Bearer ' + session['spotify_access_token']}

    response = requests.get(SPOTIFY_BASE_URL + endpoint, headers=headers, params=params)

    return response, True


def filter_spotify_info(item):
    filtered_info = {
        'song_name': item['name'],
        'artists': [artist_info['name'] for artist_info in item['artists']],
        'uri': item['uri'],
    }

    # calculate duration
    seconds = item['duration_ms'] / MILLISECONDS_PER_SECOND
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    if h != 0:
        filtered_info['duration'] = "%d:%02d:%02d" % (h, m, s)
    else:
        filtered_info['duration'] = "%d:%02d" % (m, s)

    if 'album' in item:
        album = item['album']

        if 'artists' in album:
            filtered_info['album_artists'] = [album_artist_info['name'] for album_artist_info in album['artists']]

        if 'name' in album:
            filtered_info['album_name'] = album['name']

        if 'images' in album and len(album['images']) != 0:
            filtered_info['album_art_url'] = album['images'][0]['url']

    return filtered_info



@application.route('/getSpotifyRecentlyPlayed', methods=['GET'])
def get_spotify_recently_played():

    response, success = make_spotify_get_request('/v1/me/player/recently-played')

    if not success:
        # failed refresh token
        return response

    if response.status_code == 200:
        content = response.json()
        items = content['items']

        filtered_items = []
        for item in items:
            filtered_info = filter_spotify_info(item['track'])
            if filtered_info not in filtered_items:
                filtered_items.append(filter_spotify_info(item['track']))

        return jsonify({'tracks': filtered_items, 'type': 'Recently Played Tracks'})
    else:
        return make_response('Failed to get recently-played tracks.', response.status_code)


@application.route('/getSpotifyTopTracks', methods=['GET'])
def get_top_tracks():

    response, success = make_spotify_get_request('/v1/me/top/tracks')

    if not success:
        # failed refresh token
        return response

    if response.status_code == 200:
        content = response.json()
        items = content['items']

        return jsonify({'tracks': [filter_spotify_info(item) for item in items], 'type': 'Top Tracks'})
    else:
        return make_response('Failed to get top tracks.', response.status_code)



@application.route('/getSpotifySaved', methods=['GET'])
def get_spotify_saved():

    # add albums later
    #/v1/me/albums

    response, success = make_spotify_get_request('/v1/me/tracks')

    if not success:
        # failed refresh token
        return response

    if response.status_code == 200:
        content = response.json()
        items = content['items']

        return jsonify({'tracks': [filter_spotify_info(item['track']) for item in items], 'type': 'Saved Tracks'})
    else:
        return make_response('Failed to get top tracks.', response.status_code)


@application.route('/getSpotifyNew', methods=['GET'])
def get_new_releases():

    response, success = make_spotify_get_request('/v1/browse/new-releases', params={'limit': 5})

    if not success:
        # failed refresh token
        return response

    if response.status_code == 200:
        content = response.json()
        albums = content['albums']['items']

        new_releases = []

        for album in albums:
            id = album['id']
            album_name = album['name']
            album_artists = [album_artist['name'] for album_artist in album['artists']]

            if len(album['images']) != 0:
                album_art_url = album['images'][0]['url']

            response, success = make_spotify_get_request('/v1/albums/{}/tracks'.format(id))
            if success and response.status_code == 200:
                # then add to new_releases
                tracks = response.json()['items']
                for track in tracks:
                    track_info = filter_spotify_info(track)
                    track_info.update({
                        'album_name': album_name,
                        'album_artists': album_artists,
                        'album_art_url': album_art_url
                    })
                    new_releases.append(track_info)


        return jsonify({'tracks': new_releases, 'type': 'New Releases'})

    return make_response('Failed to get new releases.', response.status_code)



def get_spotify_playlists():
    #/v1/users/{user_id}/playlists
    #/v1/users/{user_id}/playlists/{playlist_id}
    #/v1/users/{user_id}/playlists/{playlist_id}/tracks
    return



@application.route("/searchSpotify", methods=['GET'])
def search_spotify():

    query = request.args['query']

    response, success = make_spotify_get_request('/v1/search', params={'q': query, 'type': 'track'})

    if not success:
        # failed refresh token
        return response

    if response.status_code == 200:
        content = response.json()
        items = content['tracks']['items']

        return jsonify({'tracks': [filter_spotify_info(item) for item in items]})
    else:
        return make_response('Failed to get top tracks.', response.status_code)



def youtube_search(results, query):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=KEYS['YOUTUBE_DEVELOPER_KEY'])

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
        q=query,
        part="id",
        type='video'
    ).execute()

    # video IDs
    video_ids = [search_result['id']['videoId'] for search_result in search_response.get("items", [])]
    
    # look up videos for more specific information
    video_response = youtube.videos().list(
        id=','.join(video_ids),
        part='snippet,contentDetails,statistics'
    ).execute()

    for video_result in video_response.get("items", []):
        obj = {
            'title': video_result['snippet']['title'],
            'channel': video_result['snippet']['channelTitle'],
            'channelId': video_result['snippet']['channelId'],
            'description': video_result['snippet']['description'],
            'date': video_result['snippet']['publishedAt'],
            'thumbnail': video_result['snippet']['thumbnails']['default']['url'],
            'id': video_result['id']
            }

        seconds = int(isodate.parse_duration(video_result['contentDetails']['duration']).total_seconds())

        # format
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)

        if h != 0:
            obj['duration'] = "%d:%02d:%02d" % (h, m, s)
        else:
            obj['duration'] = "%d:%02d" % (m, s)

        if 'viewCount' in video_result['statistics']:
            obj['views'] = video_result['statistics']['viewCount']

        if 'likeCount' in video_result['statistics']:
            obj['likes'] = video_result['statistics']['likeCount']

        if 'dislikeCount' in video_result['statistics']:
            obj['dislikes'] = video_result['statistics']['dislikeCount']

        results.append(obj)



@application.route("/searchYoutube", methods=['GET'])
def search_youtube():
    query = request.args['query']

    # use query to search youtube
    results = []
    youtube_search(results, query)

    return jsonify({'results': results})


def update_song_info(mp3file, info):

    if 'song_name' in info:
        mp3file.tags.add(TIT2(encoding=3, text=info['song_name']))

    if 'album_name' in info:
        mp3file.tags.add(TALB(encoding=3, text=info['album_name']))

    if len(info['artists']) != 0:
        mp3file.tags.add(TPE1(encoding=3, text=', '.join(info['artists'])))

    if len(info['album_artists']) != 0:
        mp3file.tags.add(TPE2(encoding=3, text=', '.join(info['album_artists'])))

    if 'album_art_url' in info:
        response = requests.get(info['album_art_url'])
        if response.status_code == 200:            
            mp3file.tags.add(APIC(encoding=3, mime='image/png', type=3, data=response.content))


def file_exists(s3, bucket, key):
    try:
        s3.Object(bucket, key).load()
    except ClientError as e:
        return int(e.response['Error']['Code']) != 404
    
    return True


@application.route("/download", methods=['POST'])
def download():

    id = request.json['id']
    video_info = request.json['info']

    video = pafy.new(YOUTUBE_URL + id)
    audio = video.getbestaudio()

    response = requests.get(audio.url)
    if response.status_code != 200:
        return make_response('Failed to download YouTube audio.', 400)

    sound = AudioSegment.from_file(StringIO(response.content), format='webm')

    # convert to mp3
    with tempfile.TemporaryFile() as temp: 
        sound.export(temp, format="mp3")

        temp.seek(0)

        mp3file = MP3(temp, ID3=ID3)

        try:
            mp3file.add_tags()
        except error:
            pass

        # update song info
        update_song_info(mp3file, video_info)

        temp.seek(0)
        mp3file.save(fileobj=temp)

        # make sure file is at the start
        temp.seek(0)

        # write to S3 bucket
        s3 = boto3.resource('s3')

        while True:
            filename = AWS_MP3_PATH + generate_random_string(size=32) + '.mp3'
            if not file_exists(s3, AWS_BUCKET_NAME, filename):   
                break

        s3.Object(AWS_BUCKET_NAME, filename).put(Body=temp.read())
            
        return jsonify({'download_link': AWS_BUCKET_BASE_URL + filename})


def read_keys():
    config = configparser.ConfigParser()
    config.read('keys.ini')

    for key, value in config['youtunes'].iteritems():
        # read into global keys
        KEYS[key.upper()] = value


if __name__ == "__main__":
    read_keys()
    application.run()

