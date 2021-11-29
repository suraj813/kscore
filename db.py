from tinydb import TinyDB, Query
import datetime
import argparse
import youtube
import twitter

db = TinyDB('subramen-kscore.json')

MAPPING_FN = {
    "twitter-threads": twitter.get_threads_kscore,
    "twitter-timeline": twitter.get_timeline_kscore,
    "youtube": youtube.run,
}

def insert(platform, url, data, args=None):
    x = {
            "platform": platform,
            "url": url,
            "date_added": datetime.datetime.now().isoformat(), 
            "data": data,
            "args": args
        }
    db.insert(x)


def update(platform, url):
    entry = db.search(Query().fragment({'platform': platform, 'url': url}))
    fn = MAPPING_FN[entry['platform']]
    args = entry['args']
    if args is not None:
        entry['data'] = fn(url, **args)
    else:
        entry['data'] = fn(url)
    entry['date_updated'] = datetime.datetime.now().isoformat()
    db.update(entry, Query().fragment({'platform': platform, 'url': url}))


def main():
    parser = argparse.ArgumentParser("k-score calc")
    parser.add_argument("-y", "--youtube", nargs='*', type=str, default=[], help="Space separated Youtube URLs")
    parser.add_argument("-t", "--tweet", nargs='*', type=str, default=[], help="Space separated Tweet / Thread OP URLs")
    parser.add_argument("-c", "--custom", nargs=3, default=[], help="Manually add content; -c <url1> <type> <reach>")
    args = parser.parse_args()

    if len(args.youtube) > 0: 
        yt_data = MAPPING_FN["youtube"](args.youtube)
        for entry in yt_data:
            insert('youtube', entry['url'], entry)
    
    if len(args.tweet) > 0:
        thread_data = twitter.get_threads_kscore(args.thread)
        for entry in thread_data:
            insert('twitter-threads', entry['thread_url'], entry)
    
    


    print()
    for k in MAPPING_FN.keys():
        entries = db.search(Query().fragment({'platform': k}))
        score = 0
        for e in entries:
            score += e['data']['kscore']
        print(k, ": ", score)
        


if __name__ == "__main__":
    main()

    

