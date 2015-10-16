import feedparser
from datetime import datetime
import time
import socket
from threading import Thread
import json
import os

from cl_email import CL_Email
from cl_post import CL_Post
from log import Logging


def CheckNotityInterval(notification_intervals):
    for interval, flag in notification_intervals.items():
        ut = UnixTime(interval)
        if flag:
            if ut <= int(time.time()):
                notification_intervals[interval] = not flag
                return True
    return False

def NewPost(post, data_config, cl_listings):
    timestamp = UnixTime(post['published'])

    for stored_post in cl_listings:
        if post['id'] == stored_post.id:
            Log.log('Duplicate ' + data_config['title'])
            return False

    intervals = [(k, v) for k, v in data_config['notification_intervals'].items()]
    intervals = sorted(intervals, key=lambda x: (UnixTime(x[0])))

    first_interval = intervals[0]
    last_interval = intervals[len(intervals) - 1]

    for interval, flag in intervals:
        if flag:
            if interval != first_interval[0]:
                prior_interval = interval[interval.index((interval, flag)) - 1]
                if not prior_interval[1] and flag:
                    if timestamp > UnixTime(prior_interval[0]):
                        return True
            elif interval == first_interval[0]:
                if timestamp >= UnixTime(last_interval[0]) - 86400:
                    return True
            elif timestamp >= UnixTime(interval):
                return True
    return False

def UnixTime(time_element):
    try:
        ts = datetime.strptime(''.join(time_element.rsplit(':', 1)), '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        today = datetime.now().strftime('%Y-%m-%d') + 'T' + time_element
        ts = datetime.strptime(''.join(today.rsplit(':', 1)), '%Y-%m-%dT%H:%M:%S%z')
    return int(ts.strftime("%s"))

def ImageFilter(post, data_config):
    if data_config['require_image']:
        if 'enc_enclosure' not in post:
            Log.log('Filtered ' + post['title'] + ' // enc_enclosure missing')
            return False
        if 'resource' not in post['enc_enclosure']:
            Log.log('Filtered ' + post['title'] + ' // enc_enclosure/resource missing')
            return False
        if 'images' not in post['enc_enclosure']['resource']:
            Log.log('Filtered ' + post['title'] + ' // enc_enclosure/resource/images missing')
            return False
    return True

def PriceFilter(post, data_config):
    split_title = post['title'].rsplit(';', 1)
    if len(split_title) > 1:
        price = int(split_title[len(split_title) - 1])

        if int(data_config['minimum_price']) > price:
            Log.log('Filtered ' + post['title'] + ' // Price too low, $' + str(price))
            return False
        elif int(data_config['maximum_price']) < price:
            Log.log('Filtered ' + post['title'] + ' // Price too high, $' + str(price))
            return False
        else:
            post['price'] = price
            return True
    Log.log('Filtered ' + post['title'] + ' // no price in post')
    return False

def KeywordFilter(post, data_config):
    keyword_matches = []
    for keyword in data_config['keywords']:
        if keyword.lower() in post['title'].lower():
            if keyword.lower() not in keyword_matches:
                keyword_matches.append(keyword.lower())
        if keyword.lower() in post['summary'].lower():
            if keyword.lower() not in keyword_matches:
                keyword_matches.append(keyword.lower())
    if len(keyword_matches) >= int(data_config['minimum_keyword_match']) or len(keyword_matches) == len(data_config['keywords']):
        post['keyword_matches'] = keyword_matches
        return True
    else:
        Log.log('Filtered ' + post['title'] + ', insufficient keyword matches')
        return False

def ParseFeed(feed, data_config, cl_listings):
    new_posts = 0
    for post in feed['items']:
        if ImageFilter(post, data_config):
            if PriceFilter(post, data_config):
                if NewPost(post, data_config, cl_listings):
                    if KeywordFilter(post, data_config):
                        post['title'] = post['title'].split('&#x', 1)[0]
                        new_post = CL_Post(post)
                        cl_listings.append(new_post)
                        new_posts += 1
    Log.log(str(new_posts) + ' new posts detected')

def PullFeeds(location, category, result, index):
    feed = feedparser.parse('http://' + location +'.craigslist.org/search/' + category + '?format=rss')
    result[index] = feed

def UpdateIntervals(intervals):
    interval_dict = {}
    for interval, flag in intervals.items():
        if UnixTime(interval) <= time.time():
            interval_dict[interval] = False
        else:
            interval_dict[interval] = True
    return interval_dict

def LoadJson(file_path):
    try:
        with open(file_path, 'r') as f:
            content = json.load(f)
        f.close()
        return content
    except IOError as err:
        print(err)

def WriteJson(file_path, content):
    with open(file_path, 'w') as f:
        if type(content) == list:
            f.write(json.dumps([j.__dict__ for j in content], indent=4, sort_keys=True))
        elif type(content) == str:
            str_as_json = json.loads(content)
            content = json.dumps(str_as_json, indent=4, sort_keys=True)
            f.write(content)
        elif type(content) == dict:
            content = json.dumps(content, indent=4, sort_keys=True)
            f.write(content)
    f.close()

def IsEmpty(file_path):
    if os.stat(file_path).st_size == 0:
        return True
    return False

def MakeEmpty(file_path):
    with open(file_path, 'w') as f:
        pass
    f.close()

def main():
    data_config_file = 'data_config.json'
    email_config_file = 'email_config.json'
    stored_posts_file = 'stored_posts.json'
    log_file = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z') + '.log'

    global Log
    Log = Logging(log_file)

    data_config = LoadJson(data_config_file)
    email_config = LoadJson(email_config_file)

    if int(data_config['logging_enabled']):
        Log.start()

    cl_listings = []

    if not IsEmpty(stored_posts_file):
        sp = LoadJson(stored_posts_file)
        [cl_listings.append(CL_Post(stored_post)) for stored_post in sp]
        Log.log('Imported ' + str(len(cl_listings)) + ' saved posts')

    socket.setdefaulttimeout(10)

    threads_required = 0
    for _ in data_config['locations']:
        for __ in data_config['categories']:
            threads_required += 1

    threads = [None] * threads_required
    results = [None] * threads_required

    index = 0
    for location in data_config['locations']:
        for category in data_config['categories']:
            threads[index] = Thread(target=PullFeeds, args=(location, category, results, index))
            threads[index].start()
            index += 1

    [threads[i].join() for i in range(threads_required)]
    [ParseFeed(feed, data_config, cl_listings) for feed in results]

    if len(cl_listings) > 0:
        if CheckNotityInterval(data_config['notification_intervals']):
            email = CL_Email(email_config)
            email.write(cl_listings)
            email.send()
            Log.log('Email sent to ' + str(email.recipient))

            if not IsEmpty(stored_posts_file):
                MakeEmpty(stored_posts_file)
                Log.log('Emptied contents of ' + str(stored_posts_file))
        else:
            Log.log('Storing posts to ' + str(stored_posts_file))
            WriteJson(stored_posts_file, cl_listings)
            Log.log('Successful write to ' + str(stored_posts_file))
    else:
        Log.log('No new posts detected')

    data_config['notification_intervals'] = UpdateIntervals(data_config['notification_intervals'])
    WriteJson(data_config_file, data_config)
    Log.log('Updated contents of ' + str(data_config_file))

if __name__ == '__main__':
    while True:
        main()
        time.sleep(3600)