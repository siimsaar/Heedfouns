# -*- coding: utf-8 -*-
import transmissionrpc
import ast
import os
import sys
import time
from retry import retry
import requests
import traceback
from urllib import quote_plus
from selenium import webdriver
from qbittorrent import Client
from selenium.common.exceptions import NoSuchElementException

driver = webdriver.PhantomJS(desired_capabilities={'phantomjs.page.settings.loadImages': "false"})
magnet_prefix = "magnet:?xt=urn:btih:"
types = {"FLAC", "ALAC", "AAC", "MP3"}

albums = []
jlogged = False

class TorrentDl():
    def __init__(self, user_rutracker=None,
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

    def logIn(self):
        driver.get('http://login.rutracker.org/forum/login.php')
        username = driver.find_element_by_xpath(
            r'//*[@id="login-form-full"]/table/tbody/tr[2]/td/div/table/tbody/tr[1]/td[2]/input')
        password = driver.find_element_by_xpath(
            r'//*[@id="login-form-full"]/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td[2]/input')

        username.send_keys(self.user_rutracker)
        password.send_keys(self.password_rutracker)

        if self.check_exists_by_xpath(
                r'//*[@id="login-form"]/table/tbody/tr[2]/td/div/table/tbody/tr[3]/td[2]/div[1]/img'):
            print "✗ Too many invalid logins, captcha found."
            self.tearDown()
        else:
            driver.find_element_by_xpath(
                r'//*[@id="login-form-full"]/table/tbody/tr[2]/td/div/table/tbody/tr[4]/td/input').click()
        if driver.get_cookie("bb_data") is not None:
            print "✓ Successfully logged in, saving cookie"
            open("cookie.dat", 'w').write(str(driver.get_cookie("bb_data")))
        else:
            print "✗ Invalid ruTracker login data"
            raise ValueError("Unable to log in")

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
                seedcount.append(
                    driver.find_element_by_xpath("//*[@id='tor-tbl']/tbody/tr[" + str(y) + "]/td[7]/b").text)
            except NoSuchElementException:
                seedcount.append("DEAD")
        for i in xrange(0, len(torrents)):
            for k in types:
                if album.encode('utf-8').lower() in torrents[i].text.encode(
                        'utf-8').lower():  # filter everything out that doesnt match the exact searched string
                    if k in torrents[i].text:
                        if seedcount[i] is not "DEAD":
                            print "%d | %s [QUALITY = %s | SEEDS = %s | SIZE = %s]" % (
                                i + 1, torrents[i].text, k, seedcount[i], size[i].text)
        try:
            torrents[0].click()
            dl_link = "magnet:?xt=urn:btih:" + driver.find_element_by_xpath(r'//*[@id="tor-hash"]').text
            try:
                self.establishRPC(dl_link, client)
            except:
                #traceback.print_exc()
                print "✗ Unable to establish connection"
                raise IOError
        except IOError:
            raise IOError  # real ugly stuff
        except:
            print "✗ No torrents found in ruTracker"
            if self.fallback:
                try:
                    self.fallback_tracker(client, album)
                except ReferenceError:
                    raise ReferenceError # real ugly stuff
                except:
                    print "✗ Unable to establish connection"
                    raise IOError

    def fallback_tracker(self, client, album):
        print "• Searching from Kickass"
        try:
            uq_artist = quote_plus(album.split(" - ")[0].encode('utf-8'))
            uq_album = quote_plus(album.split(" - ")[1].encode('utf-8'))
            driver.get('https://kat.cr/usearch/' + uq_artist + '%20' + uq_album + '%20category:music/')
            try:
                seed_count = driver.find_element_by_css_selector('.green.center')
            except:
                print "✗ No torrents found in Kickass"
                raise Exception
            if seed_count <= 0:
                print "Torrents are all dead"
                raise Exception
            magnet_hash = driver.find_elements_by_class_name('icon16')
            magnet_hash_href = magnet_hash[0].get_attribute('href')
            if magnet_hash_href.split(":")[0] == "magnet":
                print "successfully obtained magnet"
                try:
                    self.establishRPC(magnet_hash_href, client)
                except:
                    traceback.print_exc()
                    raise IOError
            else:
                raise Exception
        except IOError:
            raise IOError
        except:
            #traceback.print_exc()
            print "✗ No torrents found in Kickass"
            try:
                print "• Searching from Jpopsuki"
                global jlogged
                if jlogged is False:
                    self.login_forjpop()
                self.jpopsuki(client, album)
            except:
                print "✗ No torrents found in jpopsuki"
                #traceback.print_exc()
                raise ReferenceError

    def establishRPC(self, magnet_link, client, type="magnet"):
        print "• Establishing connection to", client
        if client == "transmission":
            tc = transmissionrpc.Client(self.transmission_url.split(":")[0],
                                        port=self.transmission_url.split(":")[1],
                                        user=self.transmission_user,
                                        password=self.transmission_password)
            if type == "magnet":
                print "• Adding magnet to", client
                tc.add_torrent(magnet_prefix + magnet_link.text)
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

    def tearDown(self):
        driver.quit()

    def getCookies(self):
        try:
            driver.get('http://rutracker.org')
        except:
            try:
                self.getCookies()
            except:
                pass
        if os.path.exists('cookie.dat'):
            f = open('cookie.dat', "r")
            cookie = ast.literal_eval(f.read())
            driver.add_cookie(cookie)
            print "✓ Cookie added successfully"
        else:
            print "✗ No cookie found, generating one"
            self.logIn()

    #@retry(tries=5)
    def jpopsuki(self, client, album):
        driver.get('http://jpopsuki.eu/torrents.php')
        srch_field = driver.find_element_by_xpath('//*[@id="search_box"]/div/div/table[1]/tbody/tr[1]/td[2]/input')
        srch_field.send_keys(album.replace("-", ""))
        album_chooser = driver.find_element_by_xpath('//*[@id="cat_1"]')
        album_chooser.click()
        search = driver.find_element_by_xpath('//*[@id="search_box"]/div/div/div/input[1]')
        search.click()
        while True:
            if "none" in str(driver.find_element_by_xpath('//*[@id="ajax_torrents"]').get_attribute('style')):
                continue
            else:
                break
        try:
            torrent_loc = driver.find_element_by_xpath('//*[@id="torrent_table"]/tbody/tr[3]/td[1]/a')
            torrent_loc.click()
            dl_link = driver.find_element_by_xpath(
            '//*[@id="content"]/div/div[2]/table/tbody/tr[2]/td[1]/span/a[1]').get_attribute('href')
        except:
            dl_link = driver.find_element_by_xpath('//*[@id="torrent_table"]/tbody/tr[2]/td[4]/span/a[1]').get_attribute('href')
        #print dl_link
        f = open('cookie_jpop.dat', "r")
        cookie = ast.literal_eval(f.read())
        tfile = requests.get(dl_link, cookies=f)
        with open('torrent.torrent', 'wb') as output:
            output.write(tfile.content)
        self.establishRPC(magnet_link=None, client=client, type="torrent")

    @retry(tries=2)
    def login_forjpop(self):
        driver.get("http://jpopsuki.eu/login.php")
        usr_field = driver.find_element_by_xpath('//*[@id="username"]')
        pwd_field = driver.find_element_by_xpath('//*[@id="password"]')
        rmb_field = driver.find_element_by_xpath('//*[@id="loginform"]/table/tbody/tr[3]/td/input')
        smbit = driver.find_element_by_xpath('//*[@id="loginform"]/table/tbody/tr[4]/td/input')
        usr_field.send_keys(self.jpopsuki_user)
        pwd_field.send_keys(self.jpopsuki_password)
        rmb_field.click()
        smbit.click()
        if(str(driver.current_url) == "http://jpopsuki.eu/index.php"):
            print "Successfully logged into jpopsuki"
            open("cookie_jpop.dat", 'w').write(str(driver.get_cookie("PHPSESSID")))
            global jlogged
            jlogged = True
        else:
            print "Jpopsuki login failed"
            raise Exception

    def check_exists_by_xpath(self, xpath):
        try:
            driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True
