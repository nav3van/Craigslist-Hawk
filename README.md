# Craigslist Post Notification Bot
## About
Python bot to search Craisglist for posts that match the criteria specified and send out email notifications on a predefined schedule. 

##### data_config.json
- categories: enter any number of category id's to include in search. Found in the url when viewing that category in your browser. Ex: sporting='sga', boats='boo'
- keywords: enter keywords to look for when searching posts
- locations: areas of the country to include in your search
- logging_enabled: true/false, outputs a log file after each search if true
- maximum_price: excludes posts with asking price greater than dollar amount entered
- minimum_keyword_match: minimum number of keywords that must be matched before being included in an email notification
- minimum_price: excludes posts with asking price less than dollar amount entered
- notification_intervals: enter time of day (in 24 hr format) that notifications should be sent out
- require_image: true/false, excludes posts that do not include an image if true

##### email_config.json
- sender: gmail address of your craiglist bot
- server_pwd: gmail account password for sender
- recipients: list of all email addresses to include when sending notifications

## Usage
```
$ python3 cl.py
```

## Notes
- If minimum_keyword_match is greater than the number of keywords entered, posts containing all keywords are considered a match
- Bot will search Craigslist every hour but only sends out notifications if the current time is after the next notification interval
- Any posts detected before the next interval are stored and included in that next intervals notification