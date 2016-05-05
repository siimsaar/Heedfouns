# -*- coding: utf-8 -*-
import app
from apscheduler.schedulers.gevent import GeventScheduler
import logging
# from models import *
import urllib2
from urllib import quote_plus
from bs4 import BeautifulSoup
import logging


def generateSuggestions(specific_user=None):
    query_s = app.datetime.now()
    if specific_user is None:
        logging.info("Generating suggestions for all users")
        users = app.User.query.all()
        for user in users:
            sug_generator(user, query_s)
    else:
        logging.info("Generating suggestions for %s" % specific_user.name)
        sug_generator(specific_user, query_s)


def sug_generator(user, query_s):
    if user.searches_num >= 3:
        user.searches_num = 0
        app.db.session.commit()
        sugg_list = []
        user_searches = user.search_str.all()
        app.Suggestion.query.filter_by(user_id=user.id).delete()
        for i in reversed(xrange(len(user_searches) - 3, len(user_searches))):
            artist_url = (
                "http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist=%s&api_key=%s&format=json" % (
                    quote_plus(user_searches[i].search_term.encode('utf-8')), app.API_KEY))
            artist = urllib2.urlopen(artist_url)
            data = app.json.load(artist)
            s_similar = []
            for similar in data['similarartists']['artist']:
                s_similar.append(similar['name'])
            try:
                sugg_list = check_existence(s_similar, sugg_list, 0, 0)
            except:
                continue
            rsug_list = sugg_list[-3:]
            print rsug_list
            for j in rsug_list:
                artist_cover_url = (
                    "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=%s&api_key=%s&format=json" % (
                        quote_plus(j.encode('utf-8')), app.API_KEY))
                artist_cover_data = urllib2.urlopen(artist_cover_url)
                cover_data = app.json.load(artist_cover_data)
                s_cover = cover_data['artist']['image'][3]['#text']
                app.db.session.add(app.Suggestion(suggestion=unicode(j), cover_url=unicode(s_cover), user=user))
                try:
                    app.db.session.commit()
                except:
                    app.db.session.rollback()
    logging.info("Suggestion update took:", app.datetime.now() - query_s)


def check_existence(data, s_list, n, num_added):
    if unicode(data[n]) in s_list:
        return check_existence(data, s_list, n + 1, num_added)
    else:
        s_list.append(unicode(data[n]))
        num_added += 1
        if num_added == 3:
            return s_list
        else:
            return check_existence(data, s_list, n + 1, num_added)


def get_upcoming_albums_from_metacritic():
    logging.info("Getting upcoming albums from metacritic")
    ureq = urllib2.Request(r'http://www.metacritic.com/browse/albums/release-date/coming-soon/date',
                           headers={
                               'User-Agent': "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"})
    site = urllib2.urlopen(ureq)
    soup = BeautifulSoup(site.read(), 'html.parser')
    soup.prettify()
    table = soup.find("table", {"class": "musicTable"})
    releaseDict = {}
    dateList = []
    for rows in table.findAll('tr'):
        try:
            dates = rows.find('th').get_text(strip=True)
            currentDate = dates
            dateList = []
        except:
            col_a = rows.findAll('td')[0].get_text(strip=True)
            col_rl = rows.findAll('td')[1].get_text(strip=True)
            dateList.append('%s - %s' % (col_a, col_rl))
        releaseDict[currentDate] = dateList
    return releaseDict


def look_for_artist(forced=False):
    if int(app.conf.automation_status) == 1 or forced is True:
        if forced is False:
            global l_a_check
            l_a_check = app.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        logging.info("Checking for upcoming albums")
        ualbums = get_upcoming_albums_from_metacritic()
        tracked_artists = app.TrackedArtists.query.all()
        for z in reversed(tracked_artists):
            for i, j in ualbums.iteritems():
                for x in j:
                    artist_n = unicode(x).split(" - ")
                    if unicode(z.artist_name).lower() == artist_n[0].lower():
                        logging.info("%s - %s (%s) added to the schedule list" % (artist_n[0], artist_n[1], unicode(i)))
                        name = artist_n[0] + " - " + artist_n[1]
                        q_al = app.QueueAlbum(album_name=name, date=unicode(i), status="0")
                        try:
                            app.db.session.add(q_al)
                            app.db.session.commit()
                            data = ({"album": name, "date": unicode(i)})
                            app.pushtoListener(data)
                        except:
                            app.db.session.rollback()
                            continue
        data = ({"album": "C_A", "date": "C_A"})
        app.pushtoListener(data)


def look_for_torrents(forced=False):
    if int(app.conf.automation_status) == 1 or forced is True:
        if forced is False:
            global l_t_check
            l_t_check = app.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        logging.info("Checking for releases in torrents")
        todays_date = app.datetime.now()
        schd_albums = app.QueueAlbum.query.all()
        for query in schd_albums:
            date = app.datetime.strptime(query.date, "%d %B %Y")
            if date <= todays_date:
                if int(query.status) == 0:
                    app.download(query.album_name)
        data = ({"album": "C_T", "date": "C_T"})
        app.pushtoListener(data)


def reschedule():
    sched.reschedule_job(job_id="auto_A", trigger='interval', minutes=int(app.conf.automation_interval) * 60)
    sched.reschedule_job(job_id="auto_T", trigger='interval', minutes=int(app.conf.automation_interval) * 60)


# ugly
l_t_check = "Never"
l_a_check = "Never"

sched = GeventScheduler()
sched.add_job(look_for_artist, 'interval', id="auto_A", minutes=int(app.conf.automation_interval) * 60)
sched.add_job(look_for_torrents, 'interval', id="auto_T", minutes=int(app.conf.automation_interval) * 60)
sched.add_job(generateSuggestions, 'interval', id="auto_S", seconds=6200)
sched.start()
