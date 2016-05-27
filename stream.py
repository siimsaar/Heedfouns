# -*- coding: utf-8 -*-

from googleapiclient.discovery import build
import os
from googleapiclient.errors import HttpError

DEVELOPER_KEY = os.environ["YT_KEY"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def youtube_search(term, failed_playlist=False):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    if failed_playlist is True:
        term = term + " full album"

    search_response = youtube.search().list(
        q=term,
        part="id,snippet",
        maxResults=25
    ).execute()

    videos = []
    playlists = []


    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append("%s" % (search_result["id"]["videoId"]))
        elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append("%s" % (search_result["id"]["playlistId"]))

    if len(playlists) > 0 and failed_playlist is False:
        playlistitems_list_request = youtube.playlistItems().list(playlistId=playlists[0], part="snippet",
                                                                  maxResults=50).execute()
        title = playlistitems_list_request["items"][0]["snippet"]["title"]
        video_id = playlistitems_list_request["items"][0]["snippet"]["resourceId"]["videoId"]
        return "https://www.youtube.com/embed/%s?list=%s&autoplay=1&loop=1&iv_load_policy=3" % (video_id, playlists[0])
    elif len(playlists) == 0 and failed_playlist is False:
        return youtube_search(term, failed_playlist=True)
    else:
        return "https://www.youtube.com/embed/%s?rel=0&autoplay=1&iv_load_policy=3" % (videos[0])

