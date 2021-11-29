import requests
import datetime, isodate
from urllib.parse import urlparse
from config import SCORE_FNS

API_KEY = "Q7dElJttMK5bvDcsvxpditsFM"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAItrVQEAAAAAIuxXNihUSR4c4xALwkGoWDh%2Fp9A%3Dwq5ZiBEiEynPxc1jfzjUJFpsrnmochBzEHfVAsjDgbtjZAvktM"
HEADER = {"Authorization": f"Bearer {BEARER_TOKEN}"}

def string_to_datetime(s_date):
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

def isoformat_for_twitter(dt):
    dt = string_to_datetime(dt)
    dt = isodate.datetime_isoformat(dt)
    if dt[-1] != 'Z':
        dt += 'Z'
    return dt

def get_account_id(url):
    query = urlparse(url)
    username = query.path.split('/')[1]
    response = requests.get(f"https://api.twitter.com/2/users/by?usernames={username}", headers=HEADER).json()
    return response['data'][0]['id']

def get_tweet_id(url):
    query = urlparse(url)
    return query.path.split('/')[-1]

def _get_tweet_metrics(url):   
    tweet_ids = get_tweet_id(url)
    params = {
        "ids": tweet_ids, 
        "tweet.fields": "non_public_metrics,author_id,created_at"
    }
    endpoint = 'https://api.twitter.com/2/tweets'
    response = requests.get(endpoint, params=params, headers=HEADER).json()
    return response

def get_thread_tweets(op_url):
    op_tweet = _get_tweet_metrics(op_url)
    tweet_id = op_tweet['data'][0]['id']
    op_author = op_tweet['data'][0]['author_id']
    publish_dt = string_to_datetime(op_tweet['data'][0]['created_at'])
    timeline_tweets, _, _ = get_timeline_tweets(op_author, start_dt=publish_dt, end_dt=(publish_dt + datetime.timedelta(days=1)))
    thread_tweets = [tweet for tweet in timeline_tweets if tweet['conversation_id']==tweet_id]
    for thread_tweet in thread_tweets:
        thread_tweet['tweet_url'] = f"https://twitter.com/{thread_tweet['author_id']}/status/{thread_tweet['id']}"
    return thread_tweets

def get_timeline_tweets(account, start_dt=None, end_dt=None):
    all_responses = []

    if 'https' in account:
            account = get_account_id(account)
    if end_dt is None:
        end_dt = datetime.datetime.today()
    if start_dt is None:
        start_dt = string_to_datetime(end_dt) - datetime.timedelta(days=1*365)
    end_dt = isoformat_for_twitter(end_dt)
    start_dt = isoformat_for_twitter(start_dt)
    
    params = {
        "end_time": end_dt, 
        "max_results": 100,
        "start_time": start_dt,
        "tweet.fields" : "public_metrics,conversation_id,author_id",
        "exclude": "retweets"
        }
    endpoint = f"https://api.twitter.com/2/users/{account}/tweets"
    response = requests.get(endpoint, params=params, headers=HEADER).json()
    all_responses.extend(response['data'])
    while 'next_token' in response['meta'].keys():
        params["pagination_token"] = response['meta']['next_token']
        response = requests.get(endpoint, params=params, headers=HEADER).json()
        all_responses.extend(response['data'])
    
    return all_responses, start_dt, end_dt

def aggregate_metrics(tweets):    
    """TODO: K-Score calculation logic"""
    aggregate = tweets[0]['public_metrics']
    for tweet in tweets[1:]:
        for k in aggregate.keys():
            aggregate[k] += tweet['public_metrics'][k]
    return aggregate    

def get_threads_kscore(list_thread_url):
    """
    Returns 
    [
        {
            'thread_url': ..., 
            'kscore_inputs' : {...}, 
            'metadata':[{...},...], 
            'kscore': #TODO,
            'date_updated': ...
        },
        ...
    ]
    """
    result = []
    for thread_url in list_thread_url:
        print("Running for... ", thread_url)
        res = {}
        thread_tweets = get_thread_tweets(thread_url)
        res["thread_url"] = thread_url
        res["metadata"] = thread_tweets
        res["kscore_inputs"] = aggregate_metrics(thread_tweets)
        res['date_updated'] = datetime.date.today().isoformat()
        result.append(res)
    return result
    

def get_timeline_kscore(timeline_url, start_dt=None, end_dt=None):
    """
    Returns
    {
        'timeline_url': ..., 
        start_dt: ..., 
        end_dt: ..., 
        'kscore_inputs' : {...}, 
        'tweets':[{...},...],
        'kscore': #TODO,
        date_updated: ...
    }
    """
    result = {}
    timeline_tweets, start_dt, end_dt = get_timeline_tweets(timeline_url, start_dt, end_dt)
    result["timeline_url"] = timeline_url
    result["start_dt"] = start_dt
    result["end_dt"] = end_dt
    result["kscore_inputs"] = aggregate_metrics(timeline_tweets)
    result["metadata"] = timeline_tweets
    result['date_updated'] = datetime.date.today().isoformat()
    return [result]


if __name__ == "__main__":
    from pprint import pprint
    pprint(get_threads_kscore(["https://twitter.com/PyTorch/status/1456662989977923587", "https://twitter.com/MetaOpenSource/status/1450493483844661252", "https://twitter.com/PyTorch/status/1437838231505096708"]))
    # pprint(get_timeline_kscore("https://twitter.com/MetaOpenSource", start_dt="2021-07-01", end_dt="2021-07-15"))
