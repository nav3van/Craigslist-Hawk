class CL_Post:
    def __init__(self, post):
        self.published = post['published']
        self.title = post['title']
        self.summary = post['summary']
        self.id = post['id']
        self.keyword_matches = post['keyword_matches']
        self.price = post['price']