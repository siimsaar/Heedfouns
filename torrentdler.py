# -*- coding: utf-8 -*-

import requests
import itertools
from lxml import etree
import traceback
import urllib2
from urllib import quote_plus
from bs4 import BeautifulSoup
import transmissionrpc
from qbittorrent import Client
import os


class Downloader:

    def __init__(self, client, magnet_link=None, user_rutracker=None,
                 password_rutracker=None,
                 transmission_user=None,
                 transmission_password=None,
                 qbittorrent_user=None,
                 qbittorrent_password=None,
                 fallback=True,
                 qbittorrent_url=None,
                 transmission_url=None,
                 jpopsuki_user=None,
                 jpopsuki_password=None):
        self.user_rutracker = user_rutracker
        self.password_rutracker = password_rutracker
        self.transmission_user = transmission_user
        self.transmission_password = transmission_password
        self.qbittorrent_user = qbittorrent_user
        self.qbittorrent_password = qbittorrent_password
        self.fallback = fallback
        self.qbittorrent_url = qbittorrent_url
        self.transmission_url = transmission_url
        self.jpopsuki_user = jpopsuki_user
        self.jpopsuki_password = jpopsuki_password
        self.magnet_link = magnet_link
        self.client = client

    def handleDl(self, album):
        if self.user_rutracker != "" or self.password_rutracker != "":
            print "RuTracker search..."
            ru = Rutracker(quality="ANY", search_term=album, user=self.user_rutracker,
                           password=self.password_rutracker)
            try:
                ru.log_in()
                ru.search()
                self.establishRPC(client=self.client, type="torrent")
            except ReferenceError:
                try:
                    if self.fallback:
                        print "Kickass search..."
                        kat = Kickass(quality="ANY", search_term=album)
                        kat_mag = kat.search()
                        self.establishRPC(client=self.client, magnet_link=kat_mag)
                except ReferenceError:
                    if self.jpopsuki_password != "" or self.jpopsuki_user != "":
                        try:
                            print "Jpopsuki search..."
                            jp = Jpop(quality="ANY", search_term=album,
                                      user=self.jpopsuki_user, password=self.jpopsuki_password)
                            jp.log_in()
                            jp.search()
                            self.establishRPC(client=self.client, type="torrent")
                        except ReferenceError:
                            print "Couldnt find anything"
                            raise ReferenceError
        else:
            print "Conf prob"
            raise ValueError

    def establishRPC(self, client, magnet_link=None, type="magnet"):
        print "• Establishing connection to", client
        try:
            if client == "transmission":
                tc = transmissionrpc.Client(self.transmission_url.split(":")[0],
                                            port=self.transmission_url.split(":")[1],
                                            user=self.transmission_user,
                                            password=self.transmission_password)
                if type == "magnet":
                    print "• Adding magnet to", client
                    tc.add_torrent(magnet_link)
                else:
                    print "• Adding torrent to", client
                    tc.add_torrent('file://' + os.path.abspath('torrent.torrent'))
            elif client == "qbittorrent":
                qb = Client(self.qbittorrent_url)
                qb.login(self.qbittorrent_user, self.qbittorrent_password)
                if qb._is_authenticated is True:
                    if type == "magnet":
                        print "• Adding magnet to", client
                        qb.download_from_link(magnet_link)
                    else:
                        print "• Adding torrent to", client
                        qb.download_from_file(file('torrent.torrent'))
        except:
            traceback.print_exc()
            raise IOError


class Rutracker:

    def __init__(self, quality, search_term, user, password):
        self.quality = quality
        self.search_term = search_term
        self.user = user
        self.password = password


    sess = requests.session()
    sort = "prev_new=0&prev_oop=0&f%5B%5D=-1&o=10&s=2&pn="  # sort by seeds

    def log_in(self):
        loginpage = 'http://login.rutracker.org/forum/login.php'
        post_params = {
            'login_username': self.user,
            'login_password': self.password,
            'login': b'\xc2\xf5\xee\xe4'
        }
        post_l = self.sess.post(loginpage, post_params)
        try:
            self.sess.cookies['bb_data']
        except:
            print "Unable to log in"

    def search(self):
        uq_artist = ""
        try:
            uq_artist = self.search_term.split(" - ")[0].decode('ascii')
        except:
            for c in self.search_term.split(" - ")[0]:
                if ord(c) > 128:
                    uq_artist += format(" %s " % str(ord(c)))
                else:
                    uq_artist += c
        print uq_artist
        uq_album = quote_plus(self.search_term.split(" - ")[1].encode('utf-8'))
        url = "http://rutracker.org/forum/tracker.php?&" + self.sort + "&nm="
        search = self.sess.get(url + uq_artist + " " + uq_album).text
        print url+uq_artist+" "+uq_album
        parser = etree.HTMLParser()
        tree = etree.fromstring(search, parser)
        # print search
        results = {}
        results_len = len(tree.xpath("//a[@class='med tLink hl-tags bold']"))
        for i in xrange(1, results_len + 1):
            try:
                if results_len == 1:
                    title = tree.xpath('//*[@id="tor-tbl"]/tbody/tr/td[4]/div[1]/a')[0].text
                else:
                    title = tree.xpath('//*[@id="tor-tbl"]/tbody/tr[%s]/td[4]/div[1]/a' % (i))[0].text
                try:
                    if results_len == 1:
                        dl_link = tree.xpath('//*[@id="tor-tbl"]/tbody/tr/td[6]/a//@href')[0]
                    else:
                        dl_link = tree.xpath('//*[@id="tor-tbl"]/tbody/tr[%s]/td[6]/a//@href' % (i))[0]
                except:
                    traceback.print_exc()
                    dl_link = "DEAD"
                results[i] = {"title": title,
                              "dl_link": "http://rutracker.org/forum/" + dl_link}
            except:
                traceback.print_exc()
        if len(results) == 0:
            raise ReferenceError
        for i in xrange(1, len(results) + 1):
            if self.quality in results[i]['title'] or self.quality == "ANY":
                if self.search_term.lower() in results[1]['title'].lower():
                    print results[i]['title']
        if self.search_term.lower() in results[1]['title'].lower():
            self.downloadTorrent(results[1]['dl_link'])
        else:
            raise ReferenceError

    def downloadTorrent(self, url):
        try:
            print url
            tfile = self.sess.get(url)
            with open('torrent.torrent', 'wb') as output:
                output.write(tfile.content)
        except:
            traceback.print_exc()

class Kickass:

    def __init__(self, quality, search_term):
        self.quality = quality
        self.search_term = search_term

    sess = requests.session()

    def search(self):
        for c in self.search_term:
            if ord(c) > 255:
                print "Kickass can't fucking search anything beyond extended ASCII"
                raise ReferenceError
        uq_artist = quote_plus(self.search_term.split(" - ")[0].encode('utf-8'))
        uq_album = quote_plus(self.search_term.split(" - ")[1].encode('utf-8'))
        url = 'http://kat.cr/usearch/' + uq_artist + '%20' + uq_album + '%20category:music/'
        print url
        search = self.sess.get(url).text
        results = {}
        soup = BeautifulSoup(search, 'html.parser')
        table = soup.find("table", {"class": "data"})
        try:
            rows = table.findAll('tr')
        except:
            raise ReferenceError
        for row in rows:
            try:
                album_n = row.findAll("a", {"class", "cellMainLink"})
                album_m = row.findAll("a", {"class", "icon16"})
                results[album_n[0].get_text()] = album_m[0]['href']
            except AttributeError:
                raise ReferenceError
            except:
                continue
        for i,j in results.iteritems():
            print i + j
        return results.values()[0]


class Jpop:

    def __init__(self, quality, search_term, user, password):
        self.quality = quality
        self.search_term = search_term
        self.user = user
        self.password = password

    sess = requests.session()

    def log_in(self):
        loginpage = 'http://jpopsuki.eu/login.php'
        post_params = {
            'username': self.user,
            'password': self.password,
            'login': "Log+In%21"
        }
        post_l = self.sess.post(loginpage, post_params, allow_redirects=True)
        try:
            self.sess.cookies['PHPSESSID']
        except:
            print "Unable to log in"

    def search(self):
        uq_artist = quote_plus(self.search_term.split(" - ")[0].encode('utf-8'))
        uq_album = quote_plus(self.search_term.split(" - ")[1].encode('utf-8'))
        url = "http://jpopsuki.eu/torrents.php?order_by=s6&order_way=DESC&searchstr="\
              + uq_artist + "%20" + uq_album + "&filter_cat%5B1%5D=1"
        search = self.sess.get(url).text
        results = {}
        soup = BeautifulSoup(search, 'html.parser')
        table = soup.find("table", {"id": "torrent_table"})
        try:
            rows = table.findAll('tr', {'class': 'group_redline'})
        except:
            rows = ""
        if len(rows) == 0:
            try:
                rows = table.findAll('tr', {'class': 'torrent_redline'})
                for row in rows:
                    data = row.find('a', {'rel': 'shadowbox'})
                    name = data['title']
                    dl_link = row.find('a', {'title': "Download"})['href']
                    quality = row.find('a', {'title': "View Torrent"}).next_sibling.split("[")[1].split("/ ")[0]
                    if len(results) == 0:
                        results[name] = {"link_" + quality: "http://jpopsuki.eu/" + dl_link}
                    else:
                        results[name].update({"link_" + quality: "http://jpopsuki.eu/" + dl_link})
            except:
                raise ReferenceError
        else:
            for row in rows:
                try:
                    data = row.find('a', {'rel': 'shadowbox'})
                    group_id = data['href'].split("/")[3].split(".")[0]
                    name = data['title']
                    try:
                        class_name = "groupid_" + group_id
                        links = table.findAll('tr', {'class': class_name})
                        for i in links:
                            dl_data = i.findAll('a')
                            quality = dl_data[2].get_text(strip=True).split(" ")[0]
                            dl_link = dl_data[0]['href']
                            if len(results) == 0:
                                results[name] = {"link_" + quality: "http://jpopsuki.eu/" + dl_link}
                            else:
                                results[name].update({"link_" + quality: "http://jpopsuki.eu/" + dl_link})
                    except:
                        continue
                except:
                    raise ReferenceError
        if len(results) == 0:
            raise ReferenceError
        else:
            try:
                results.values()[0]['link_MP3']     # TODO
            except:
                raise ReferenceError
            self.downloadTorrent(results.values()[0]['link_MP3'])

    def downloadTorrent(self, url):
        try:
            print url
            tfile = self.sess.get(url)
            with open('torrent.torrent', 'wb') as output:
                output.write(tfile.content)
        except:
            traceback.print_exc()