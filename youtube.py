import requests
import datetime, isodate
from config import SCORE_FNS


  
API_KEY = "AIzaSyDDmdohErTs_HtpfUmfxuhWBmKRMDsbI40"
API_URL = "https://www.googleapis.com/youtube/v3/"


def get_youtube_id(url):
    """Returns Video_ID extracting from the given url of Youtube
    https://gist.github.com/kmonsoor/2a1afba4ee127cce50a0
    
    Examples of URLs:
    Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
    
    Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """
    from urllib.parse import urlparse, parse_qs
    if url.startswith(('youtu', 'www')):
        url = 'http://' + url
    query = urlparse(url)
    if 'playlist' in url:
        return parse_qs(query.query)['list'][0]
    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        raise ValueError

def get_playlist_video_ids(url):
    """Returns comma-separated video ids of playlist videos"""
    pl_id = get_youtube_id(url)
    params = {
        "maxResults": "1000",
        "part": "contentDetails",
        "playlistId": pl_id,
        "key": API_KEY
    }
    endpoint = API_URL + "playlistItems"
    response = requests.get(endpoint, params=params).json()
    try:
        yt_ids = ','.join([item['contentDetails']['videoId'] for item in response['items']])
    except KeyError:
        print("ERROR", response) 
    return yt_ids

def get_metrics(url):
    """Returns metrics for video or playlist url"""

    if 'playlist' in url:
        yt_id = get_playlist_video_ids(url)
    else:
        yt_id = get_youtube_id(url)

    params = {
        "part" : "statistics,contentDetails,liveStreamingDetails,snippet",
        "id" : yt_id,
        "key": API_KEY
    }
    endpoint = API_URL + "videos"
    response = requests.get(endpoint, params=params).json()
    return response

def get_kscore(metrics):
    results = []
    for item in metrics['items']:
        res = {}
        res['url'] = "https://youtube.com/watch?v=" + item['id']
        res['metadata'] = {}
        res['metadata']['title'] = item['snippet']['title']
        res['metadata']['published'] = item['snippet']['publishedAt']
        views = int(item['statistics']['viewCount'])

        if 'liveStreamingDetails' in item.keys():
            res['type'] = 'live'
            hours = isodate.parse_duration(item['contentDetails']['duration']).total_seconds() / 3600
            hours_watched = hours * views
            kscore = SCORE_FNS['live_video'](hours_watched)
            res['kscore_inputs'] = {
                "duration (hours)": hours, 
                "views": views, 
                "hours_watched": hours_watched
                }
        else:
            res['type'] = 'vod'
            kscore = SCORE_FNS['vod'](views)
            res['kscore_inputs'] = {"views": views}
        
        res['kscore'] = round(kscore)
        results.append(res)
    return results


def run(list_of_urls):
    """
    Returns
    [
        {
            'url': ...,
            'kscore': ...,
            'kscore_inputs': {...},
            'metadata': {...}
        }
    ]

    """
    response = []
    for url in list_of_urls:
        metrics = get_metrics(url)
        result = get_kscore(metrics)
        response.extend(result)
    return response

        
if __name__ == "__main__":
    from pprint import pprint
    pprint(main(["https://www.youtube.com/watch?v=Ge5T6eZ2WY4", "https://www.youtube.com/playlist?list=PL_lsbAsL_o2D9gCMeAK89MD02E6sBeHMi"]))
