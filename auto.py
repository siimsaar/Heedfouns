# -*- coding: utf-8 -*-
from app import db, QueueAlbum, TrackedArtists
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


def look_for_artist():
    print "Checking for upcoming albums"
    ualbums = get_upcoming_albums_from_metacritic()
    tracked_artists = TrackedArtists.query.all()
    for z in reversed(tracked_artists):
        for i, j in ualbums.iteritems():
            for x in j:
                artist_n = unicode(x).split(" - ")
                if unicode(z.artist_name).lower() == artist_n[0].lower():
                    print ("%s - %s (%s)" % (artist_n[0], artist_n[1], unicode(i)))
                    name = artist_n[0] + " - " + artist_n[1]
                    q_al = QueueAlbum(album_name=name, date=unicode(i), status="0")
                    try:
                        db.session.add(q_al)
                        db.session.commit()
                    except:
                        db.session.rollback()
                        continue


def look_for_torrents():
    print "todo"
