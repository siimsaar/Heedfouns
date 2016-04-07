# -*- coding: utf-8 -*-
import app
from apscheduler.schedulers.gevent import GeventScheduler
import logging
# from models import *
import urllib2
from bs4 import BeautifulSoup


def get_upcoming_albums_from_metacritic():
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
        print "Checking for upcoming albums"
        ualbums = get_upcoming_albums_from_metacritic()
        tracked_artists = app.TrackedArtists.query.all()
        for z in reversed(tracked_artists):
            for i, j in ualbums.iteritems():
                for x in j:
                    artist_n = unicode(x).split(" - ")
                    if unicode(z.artist_name).lower() == artist_n[0].lower():
                        print ("%s - %s (%s)" % (artist_n[0], artist_n[1], unicode(i)))
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
        data = ({"album": "EOF_A", "date": "EOF_A"})
        app.pushtoListener(data)


def look_for_torrents(forced=False):
    if int(app.conf.automation_status) == 1 or forced is True:
        if forced is False:
            global l_t_check
            l_t_check = app.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        print "Checking for release torrents"
        todays_date = app.datetime.now()
        schd_albums = app.QueueAlbum.query.all()
        for query in schd_albums:
            date = app.datetime.strptime(query.date, "%d %B %Y")
            if date <= todays_date:
                if int(query.status) == 0:
                    app.download(query.album_name)
        data = ({"album": "EOF_T", "date": "EOF_T"})
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
sched.start()
