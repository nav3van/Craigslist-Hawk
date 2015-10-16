import smtplib

class CL_Email:
    def __init__(self, email_obj):
        self.data = email_obj
        self.sender = self.data['sender']
        self.recipient =  self.data['recipients']
        self.server_pwd = self.data['server_pwd']
        self.message = ''
    def write(self, craigslist_listings):
        self.message += 'Subject: Craigslist Bot (' + str(len(craigslist_listings)) + ' new posts)\n\n'
        for post in craigslist_listings:
            self.message += '$' + str(post.price) + ' ' + post.title + \
                            '\nKeyword matches: ' + str([k for k in post.key_matches]) + \
                            '\n' + post.id + \
                            '\n' + post.summary + \
                            '\n\n------------------\n\n'
    def send(self):
        server = smtplib.SMTP('smtp.gmail.com',587) #port 465 or 587
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.sender, self.server_pwd)
        server.sendmail(self.sender, self.recipient, self.message.encode('utf-8'))
        server.close()