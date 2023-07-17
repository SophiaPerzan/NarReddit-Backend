import praw


class Scraper:
    def __init__(self, env):
        self.env = env

        # Read-only instance
        self.reddit = praw.Reddit(client_id=env['CLIENT_ID'],
                                  client_secret=env['CLIENT_SECRET'],
                                  user_agent=env['USER_AGENT'])
        self.reddit.read_only = True

    def getHotPosts(self, params):
        hotPosts = []
        subreddit = self.reddit.subreddit(params['SUBREDDIT'])
        minPostLength = int(params['MIN_POST_LENGTH'])
        maxPostLength = int(params['MAX_POST_LENGTH'])
        for post in subreddit.hot():
            if not post.stickied and post.is_self and (minPostLength <= len(post.selftext) <= maxPostLength) and len(hotPosts) < 2:
                hotPosts.append(post)
            if len(hotPosts) >= 2:
                break

        hotPosts = hotPosts[:1]
        post = hotPosts[0]
        return (post.title, post.title+"\n"+post.selftext)
