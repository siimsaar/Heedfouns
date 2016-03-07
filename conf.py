# -*- coding: utf-8 -*-
import ConfigParser
import os

config = ConfigParser.RawConfigParser()

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
    config.set('general', 'rutracker_user', '')
    config.set('general', 'rutracker_password', '')
    with open('config.cfg', 'wb') as configfile:
        config.write(configfile)
    print "• Configure in config.cfg and rerun"
    os._exit(0)
else:
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