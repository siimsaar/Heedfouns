# -*- coding: utf-8 -*-
import ConfigParser
import os

config = ConfigParser.RawConfigParser()

def setvars():
    global transmission_url, transmission_password, transmission_user, qbittorrent_url,\
        qbittorrent_password, qbittorrent_url, qbittorrent_user, use_fallback, torrent_client,\
        rutracker_user, rutracker_password, default_search_api, jpopsuki_user, jpopsuki_password, \
        automation_status, automation_interval, reg_enabled
    config.read('config.cfg')
    transmission_user = config.get("transmission", "user")
    transmission_password = config.get("transmission", "password")
    transmission_url = config.get("transmission", "url")
    qbittorrent_user = config.get("qbittorrent", "user")
    qbittorrent_password = config.get("qbittorrent", "password")
    qbittorrent_url = config.get("qbittorrent", "url")
    use_fallback = config.getint("general", "use_fallback")
    torrent_client = config.get("general", "torrent_client")
    rutracker_user = config.get("general", "rutracker_user")
    rutracker_password = config.get("general", "rutracker_password")
    default_search_api = config.get("general", "default_search_api")
    jpopsuki_user = config.get("general", "jpopsuki_user")
    jpopsuki_password = config.get("general", "jpopsuki_password")
    automation_status = config.get("auto", "enable")
    automation_interval = config.get("auto", "check_int")
    reg_enabled = config.get("general", "reg_enabled")

if not os.path.exists('config.cfg'):
    print "• No configuration detected, generating config file"
    config.add_section('transmission')
    config.set('transmission', 'user', '')
    config.set('transmission', 'password', '')
    config.set('transmission', 'url', '')
    config.add_section('qbittorrent')
    config.set('qbittorrent', 'user', '')
    config.set('qbittorrent', 'password', '')
    config.set('qbittorrent', 'url', '')
    config.add_section('general')
    config.set('general', 'torrent_client', 'transmission')
    config.set('general', 'use_fallback', '1')
    config.set('general', 'default_search_api', 'lastfm')
    config.set('general', 'rutracker_user', '')
    config.set('general', 'rutracker_password', '')
    config.set('general', 'jpopsuki_user', '')
    config.set('general', 'jpopsuki_password', '')
    config.set('general', 'reg_enabled', '1')
    config.add_section('auto')
    config.set('auto', 'enable', '0')
    config.set('auto', 'check_int', '24')
    with open('config.cfg', 'wb') as configfile:
        config.write(configfile)
    print "• Configure in config.cfg or web"
    setvars()
else:
    setvars()

def updateConf(*args):
    print "• Writing new config"
    config.set('transmission', 'user', args[0])
    config.set('transmission', 'password', args[1])
    config.set('transmission', 'url', args[2])
    config.set('qbittorrent', 'user', args[3])
    config.set('qbittorrent', 'password', args[4])
    config.set('qbittorrent', 'url', args[5])
    config.set('general', 'torrent_client', args[6])
    config.set('general', 'use_fallback', '1')
    config.set('general', 'default_search_api', 'lastfm')
    config.set('general', 'rutracker_user', args[7])
    config.set('general', 'rutracker_password', args[8])
    config.set('general', 'jpopsuki_user', args[9])
    config.set('general', 'jpopsuki_password', args[10])
    with open('config.cfg', 'wb') as configfile:
        config.write(configfile)


def updateAutomation(*args):
    config.set('auto', 'enable', args[0])
    config.set('auto', 'check_int', args[1])
    with open('config.cfg', 'wb') as configfile:
        config.write(configfile)

def updateRegistration(*args):
    config.set('general', 'reg_enabled', args[0])
    with open('config.cfg', 'wb') as configfile:
        config.write(configfile)

