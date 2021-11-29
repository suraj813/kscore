import requests
import datetime, isodate
from collections import Counter
from urllib.parse import urlparse, parse_qs

score_fns = {
    "developer_conversation": lambda hours, audience=1: 1 * hours * audience,
    "influencer_conversation": lambda hours, audience=1: 10 * hours * audience,
    "vod": lambda views: 0.1 * views,
    "live_video": lambda hours_watched: 0.3 * hours_watched,
    "podcast": lambda hours_watched: 0.2 * hours_watched,
    "blog": lambda views_1yr: 0.05 * views_1yr,
    "press_mentions": lambda mentions: 100 * mentions,
    "git_stars": lambda stars: 10 * stars,
    "tutorials": lambda views: 0.05 * views
}



def YOUTUBE(url):
    """URL can be a single video or a playlist"""
    GOOGLE_API = "AIzaSyDDmdohErTs_HtpfUmfxuhWBmKRMDsbI40"
    
    def _get_yt_id(url):
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

    def _get_playlist_video_ids(url):
        """Returns comma-separated video ids of playlist videos"""
        pl_id = _get_yt_id(url)
        params = {
            "maxResults": "1000",
            "part": "contentDetails",
            "playlistId": pl_id,
            "key": GOOGLE_API
        }
        endpoint = f"https://www.googleapis.com/youtube/v3/playlistItems"
        response = requests.get(endpoint, params=params).json()
        try:
            yt_ids = ','.join([item['contentDetails']['videoId'] for item in response['items']])
        except KeyError:
            print("ERROR", response) 
        return yt_ids
        
    def get_yt_metrics(url):
        """Returns metrics for video or playlist url"""
    
        if 'playlist' in url:
            yt_id = _get_playlist_video_ids(url)
        else:
            yt_id = _get_yt_id(url)

        params = {
            "part" : "statistics,contentDetails,liveStreamingDetails,snippet",
            "id" : yt_id,
            "key": GOOGLE_API
        }
        endpoint = f"https://www.googleapis.com/youtube/v3/videos"
        response = requests.get(endpoint, params=params).json()
        return response

    def get_yt_kscore(metrics):
        results = []
        for item in metrics['items']:
            res = {}
            res['meta'] = {}
            res['meta']['title'] = item['snippet']['title']
            res['meta']['published'] = item['snippet']['publishedAt']
            res['meta']['live'] = False
            views = int(item['statistics']['viewCount'])

            if 'liveStreamingDetails' in item.keys():
                res['live'] = True
                hours = isodate.parse_duration(item['contentDetails']['duration']).total_seconds() / 3600
                hours_watched = hours * views
                kscore = score_fns['live_video'](hours_watched)
            else:
                kscore = score_fns['vod'](views)

            res['kscore'] = round(kscore)
            results.append(res)
        return results

    metrics = get_yt_metrics(url)
    return get_yt_kscore(metrics)


def TWITTER(url, is_thread=False, start_dt=None, end_dt=None):
    """URL can be for 
    - tweet
    - account (include start_dt or end_dt. by default, end_dt is today and start_dt is last year this day.)"""
    
    TWITTER_API = "Q7dElJttMK5bvDcsvxpditsFM"
    TWITTER_SECRET = "R5npgE0H3xHKfubGfFT5ZZAOSKdg2v1I6NgkHTCQIgKJ9eFvW2"
    TWITTER_BEARER = "AAAAAAAAAAAAAAAAAAAAAItrVQEAAAAAIuxXNihUSR4c4xALwkGoWDh%2Fp9A%3Dwq5ZiBEiEynPxc1jfzjUJFpsrnmochBzEHfVAsjDgbtjZAvktM"

    headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}

    def _get_date(s_date):
        if isinstance(s_date, datetime.datetime):
            return s_date

        s_date = s_date.split('T')[0]
        date_patterns = ["%d-%m-%Y", "%Y-%m-%d"]
        for pattern in date_patterns:
            try:
                return datetime.datetime.strptime(s_date, pattern)
            except:
                pass
        print(f"Date {s_date} is not in expected formats {date_patterns}")

    def _isoformat_for_twitter(dt):
        dt = _get_date(dt)
        dt = isodate.datetime_isoformat(dt)
        if dt[-1] != 'Z':
            dt += 'Z'
        return dt

    def _get_account_id(url):
        query = urlparse(url)
        username = query.path.split('/')[1]
        response = requests.get(f"https://api.twitter.com/2/users/by?usernames={username}", headers=headers).json()
        return response['data'][0]['id']

    def _get_tweet_id(url):
        query = urlparse(url)
        return query.path.split('/')[-1]

    def get_tweet_metrics(url):   
        if isinstance(url, list):
            tweet_ids = ','.join(_get_tweet_id(u) for u in url)   
        tweet_ids = _get_tweet_id(url)
        params = {
            "ids": tweet_ids, 
            "tweet.fields": "public_metrics,author_id,created_at"
        }
        endpoint = 'https://api.twitter.com/2/tweets'
        response = requests.get(endpoint, params=params, headers=headers).json()
        return response

    def get_thread_metrics(op_url):
        op_tweet = get_tweet_metrics(op_url)
        tweet_id = op_tweet['data'][0]['id']
        op_author = op_tweet['data'][0]['author_id']
        publish_dt = _get_date(op_tweet['data'][0]['created_at'])
        timeline_tweets = get_timeline_metrics(op_author, start_dt=publish_dt, end_dt=(publish_dt + datetime.timedelta(days=1)))
        thread_tweets = [tweet for tweet in timeline_tweets if tweet['conversation_id']==tweet_id]
        for thread_tweet in thread_tweets:
            thread_tweet['tweet_url'] = f"https://twitter.com/{thread_tweet['author_id']}/status/{thread_tweet['id']}"
        return thread_tweets
    
    def get_timeline_metrics(account, start_dt=None, end_dt=None):
        all_responses = []

        if 'https' in account:
            account = _get_account_id(account)
        if end_dt is None:
            end_dt = datetime.datetime.today()
        if start_dt is None:
            start_dt = _get_date(end_dt) - datetime.timedelta(days=1*365)
        end_dt = _isoformat_for_twitter(end_dt)
        start_dt = _isoformat_for_twitter(start_dt)
        
        params = {
            "end_time": end_dt, 
            "max_results": 10,
            "start_time": start_dt,
            "tweet.fields" : "public_metrics,non_public_metrics,conversation_id,author_id",
            "exclude": "retweets"
            }
        endpoint = f"https://api.twitter.com/2/users/{account}/tweets"
        response = requests.get(endpoint, params=params, headers=headers).json()
        all_responses.extend(response['data'])
        while 'next_token' in response['meta'].keys():
            params["pagination_token"] = response['meta']['next_token']
            response = requests.get(endpoint, params=params, headers=headers).json()
            all_responses.extend(response['data'])
        
        return all_responses


    """TODO: Include impressions in the metrics."""
    """TODO: get_twitter_kscore() aggregating function"""

    if 'status' in url:  # this is a tweet url
        if is_thread:
            return get_thread_metrics(url)
        return get_tweet_metrics(url)
    return get_timeline_metrics(url)

    
# TODO Defauly function that is like the excel spreadsheet

# TODO Pipeline for stateful json

"""
(url, kscore, metadata)
playlist: {tuple1, tuple2, ... }
tweet thread: {tuple1, tuple2, ....}
"""
    
def example_yt():
    print("Kscore for single video: \n", YOUTUBE("https://www.youtube.com/watch?v=Ge5T6eZ2WY4"))
    print()
    print("Kscore for playlist: \n", YOUTUBE("https://www.youtube.com/playlist?list=PL_lsbAsL_o2D9gCMeAK89MD02E6sBeHMi"))

def example_twitter():
    print("Single tweet\n", TWITTER("https://twitter.com/PyTorch/status/1437838231505096708"))
    print()
    print("Tweet thread\n", TWITTER("https://twitter.com/PyTorch/status/1437838231505096708", is_thread=True)) 
    print()
    print("Timeline for Q3\n", TWITTER("https://twitter.com/MetaOpenSource", start_dt="2021-07-01", end_dt="2021-10-01"))

if __name__ == "__main__":
    example_yt()
    example_twitter()