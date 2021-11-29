
SCORE_FNS = {
    # MEETUPS/CONFERENCES
    "developer_conversation": lambda hours, audience=1: 1 * hours * audience,
    "influencer_conversation": lambda hours, audience=1: 10 * hours * audience,
    # CONTENT
    "vod": lambda views: 0.1 * views,
    "live_video": lambda hours_watched: 0.3 * hours_watched,
    "podcast": lambda hours_watched: 0.2 * hours_watched,
    # TWITTER
    "twitter_thread": lambda views: 0.05 * views,
    "tweet": lambda views: 0.05 * views,
    # MISC
    "blog": lambda views_1yr: 0.05 * views_1yr,
    "tutorials": lambda views: 0.05 * views,
    "press_mentions": lambda mentions: 100 * mentions,
    "git_stars": lambda stars: 10 * stars,
}