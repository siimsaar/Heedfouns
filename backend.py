# -*- coding: utf-8 -*-
import transmissionrpc
import urllib2
from bs4 import BeautifulSoup
import os
import traceback
import ast
import requests
from KickassAPI import * # fix magnet_link var in KickassAPI.py for it to work
from selenium import webdriver
from qbittorrent import Client
from lxml import etree
from selenium.common.exceptions import NoSuchElementException
driver = webdriver.PhantomJS(desired_capabilities={'phantomjs.page.settings.loadImages': "false"})
magnet_prefix = "magnet:?xt=urn:btih:"
types = {"FLAC", "ALAC", "AAC", "MP3"}

albums = []

class ruTracker():

    def __init__(self, user_rutracker,
                 password_rutracker,
                 transmission_user=None,
                 transmission_password=None,
                 qbittorrent_user=None,
                 qbittorrent_password=None,
                 fallback=True,
                 qbittorrent_url=None,
                 transmission_url=None):
        self.user_rutracker = user_rutracker
        self.password_rutracker = password_rutracker
        self.transmission_user = transmission_user
        self.transmission_password = transmission_password
        self.qbittorrent_user = qbittorrent_user
        self.qbittorrent_password = qbittorrent_password
        self.fallback = fallback
        self.qbittorrent_url = qbittorrent_url
        self.transmission_url = transmission_url

    def logIn(self):
        driver.get('http://login.rutracker.org/forum/login.php')
        username = driver.find_element_by_xpath(
            r'//*[@id="login-form"]/table/tbody/tr[2]/td/div/table/tbody/tr[1]/td[2]/input')
        password = driver.find_element_by_xpath(
            r'//*[@id="login-form"]/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td[2]/input')

        username.send_keys(self.user_rutracker)
        password.send_keys(self.password_rutracker)

        if self.check_exists_by_xpath(r'//*[@id="login-form"]/table/tbody/tr[2]/td/div/table/tbody/tr[3]/td[2]/div[1]/img'):
            print "✗ keked"
            self.tearDown()
        else:
            driver.find_element_by_css_selector(
                r'#login-form > table > tbody > tr:nth-child(2) > td > div > table > tbody > tr:nth-child(3) > td > input').click()
        print "✓ Successfully logged in, saving cookie"
        open("cookie.dat", 'w').write(str(driver.get_cookie("bb_data")))

    def getAlbums(self, album, client):
        print "• Searching for torrents"
        driver.get('http://rutracker.org')
        try:
            search = driver.find_element_by_css_selector('#search-text')
        except:
            print "✗ Corrupt or expired cookie"
            self.logIn()
            search = driver.find_element_by_css_selector('#search-text')
        search_bttn = driver.find_element_by_css_selector('#search-submit')
        search.send_keys(album)
        search_bttn.click()
        torrents = driver.find_elements_by_xpath("//a[@class='med tLink hl-tags bold']")
        size = driver.find_elements_by_xpath("//a[@class='small tr-dl dl-stub']")
        seedcount = list()
        for y in xrange(1, len(torrents) + 1):
            try:
                seedcount.append(driver.find_element_by_xpath("//*[@id='tor-tbl']/tbody/tr[" + str(y) + "]/td[7]/b").text)
            except NoSuchElementException:
                seedcount.append("DEAD")
        for i in xrange(0, len(torrents)):
                    for k in types:
                        if album.encode('utf-8').lower() in torrents[i].text.encode('utf-8').lower(): # filter everything out that doesnt match the exact searched string
                            if k in torrents[i].text:
                                if seedcount[i] is not "DEAD":
                                    print "%d | %s [QUALITY = %s | SEEDS = %s | SIZE = %s]" % (i+1, torrents[i].text, k, seedcount[i], size[i].text)
        try:
            torrents[0].click()
            dl_link = driver.find_element_by_xpath(r'//*[@id="tor-hash"]')
            try:
                self.establishRPC(dl_link, client)
            except:
                print "✗ Unable to establish connection"
        except:
            print "✗ No torrents found in ruTracker"
            if self.fallback:
                try:
                    self.fallback_tracker(client, album)
                except:
                    print "✗ Unable to establish connection"

    def fallback_tracker(self, client, album):
        print "• Searching from fallback"
        album = album.replace("-", "")
        try:
            t = Search(album).page(1).order(ORDER.SEED).list()
            print "✓ Found %s" % t[0].__getattribute__("name")
            self.establishRPC(t[0].__getattribute__('magnet_link'), client)
        except ValueError:
            print "✗ No torrents found in Kat"

    def establishRPC(self, magnet_link, client):
        print "• Establishing connection to", client
        if client == "transmission":
            tc = transmissionrpc.Client(self.transmission_url,
                                        port=9091,
                                        user=self.transmission_user,
                                        password=self.transmission_password)
            print "• Adding magnet to", client
            tc.add_torrent(magnet_prefix + magnet_link.text)
        elif client == "qbittorrent":
            qb = Client(self.qbittorrent_url)
            qb.login(self.qbittorrent_user, self.qbittorrent_password)
            if qb._is_authenticated is True:
                print "• Adding magnet to", client
                qb.download_from_link(magnet_prefix + magnet_link.text)

    def tearDown(self):
        driver.quit()

    def getCookies(self):
        driver.get('http://rutracker.org')
        if os.path.exists('cookie.dat'):
            f = open('cookie.dat', "r")
            cookie = ast.literal_eval(f.read())
            driver.add_cookie(cookie)
            print "✓ Cookie added successfully"
        else:
            print "✗ No cookie found, generating one"
            self.logIn()

    def check_exists_by_xpath(self, xpath):
        try:
            driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True