import ytmusicapi
import yt_dlp
import urllib.parse

searcher = ytmusicapi.YTMusic()

      
def playlist_data(playlist_id):
    raw_playlist=searcher.get_playlist(playlist_id,limit=None)
    song_list=[]
    if len(raw_playlist.get("tracks",[]))>0 :
        tracks=raw_playlist["tracks"]
        for song in tracks:
            formatted_song=music_data(song)
            if formatted_song["status"]=="error":
                continue
            song_list.append(formatted_song)
        if len(song_list)==0:
                song_list.append(music_data(None))
        return song_list
    else:
        formatted_song=music_data(None)
        song_list.append(formatted_song)
        return song_list

def song_data(song_id):
    raw_song=searcher.search(song_id,filter="songs")
    if raw_song:
        formatted_song=music_data(raw_song[0])
        return formatted_song
    else:
        formatted_song=music_data(None)
        return formatted_song

def song_link_data(song_link_id):
    raw_song_link=searcher.search(song_link_id)
    if raw_song_link:
        try:
            formatted_song=music_data(raw_song_link[0])
            return formatted_song
        except Exception as e:
            error_message = str(e)
            print(error_message)
    else:
        formatted_song=music_data(None)
        return formatted_song

def music_data(raw_song):
    if raw_song:
        song={
            "status":"success",
            "title": raw_song["title"],
            "id": raw_song["videoId"],
            "duration": raw_song["duration_seconds"],
            "thumbnails": raw_song["thumbnails"],
            "artists": raw_song["artists"]
        }
        return song
    else:
        song={
            "status":"error",
            "title": "Not found",
            "id": "",
            "duration": "",
            "thumbnails": "",
            "artists": ""
        }
        return song

def search_bar(user_input):
    if "http" in user_input:
        result=None
        parsed_url=urllib.parse.urlparse(user_input)
        params=urllib.parse.parse_qs(parsed_url.query)
        if "list" in params:
            result=playlist_data(params["list"][0])
        elif "v" in params:
            result=song_link_data(params["v"][0])
        else:
            result=song_data(user_input)
    else:
        result=song_data(user_input)
    return result
    
fetcher_options={
        "format":"bestaudio",
        "noplaylist":True,
        "quiet":False,
    }
    
def fetch(video_id):
    with yt_dlp.YoutubeDL(fetcher_options) as fetcher:
        try:
            info=fetcher.extract_info(video_id,download=False)
            fetch_result={"url": info["url"],
                         "status": "success"}
            return fetch_result
        except Exception as e:
            error_message = str(e)
            fetch_result={"error": error_message,
                         "status": "error"}
            return fetch_result