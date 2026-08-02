import ytmusicapi;
import yt_dlp;

searcher = ytmusicapi.YTMusic();

      
def playlist(search):
    res=search.split("list=")[1].split("&si")[0]
    res=searcher.get_playlist(res,limit=None)
    songList=[]
    if len(res.get("tracks",[]))>0 :
        tracks=res["tracks"]
        for song in tracks:
            song_info={
                "status":"success",
                "title": song["title"],
                "id": song["videoId"],
                "duration": song["duration_seconds"],
                "thumbnails": song["thumbnails"],
                "artists": song["artists"]
            }
            songList.append(song_info)
        
        return songList
    else:
        song_info={
            "status":"error",
            "title": "Not found",
            "id": "",
            "duration": "",
            "thumbnails": "",
            "artists": ""
        }
        songList.append(song_info)
    return songList

def songs(search):
    res=searcher.search(search,filter="songs")
    if len(res)>0 :
        song={
            "status":"success",
            "title": res[0]["title"],
            "id": res[0]["videoId"],
            "duration": res[0]["duration_seconds"],
            "thumbnails": res[0]["thumbnails"],
            "artists": res[0]["artists"]
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
    
def songsLink(search):
    res=search.split("v=")[1].split("&si")[0]
    res=searcher.search(res)
    if len(res)>0 :
        song={
            "status":"success",
            "title": res[0]["title"],
            "id": res[0]["videoId"],
            "duration": res[0]["duration_seconds"],
            "thumbnails": res[0]["thumbnails"],
            "artists": res[0]["artists"]
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


def searchBar(search):
    if "youtube" in search and "list=" in search:
        result=playlist(search)
    elif "youtube" in search and "v=" in search:
        result=songsLink(search)
    else:
        result=songs(search)
    return result
    
fetcherOpt={
        "format":"bestaudio",
        "noplaylist":True,
        "quiet":False,
    }
    
def fetch(res):
    with yt_dlp.YoutubeDL(fetcherOpt) as fetcher:
        info=fetcher.extract_info(res,download=False)
        url=info["url"]
        return url
    
