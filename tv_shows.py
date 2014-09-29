# -*- coding=utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

from collections import defaultdict
import operator
import os

from themylog.rules_tree import RecordField as F

subtitle_providers = {"subliminal": "en",
                      "notabenoid": "ru",
                      "sp_fan": "ru"}

feeds = {"torrent_files": {"rules_tree": (operator.and_, (operator.eq, F("application"), "tv_shows"),
                                                         (operator.eq, F("logger"), "torrent_file_seeker"))},
         "video_files": {"rules_tree": (operator.and_, (operator.eq, F("application"), "tv_shows"),
                                                       (operator.eq, F("logger"), "torrent_downloader"))},
         "views": {"rules_tree": (operator.and_, (operator.eq, F("application"), "theMediaShell"),
                                                 (operator.and_, (operator.eq, F("logger"), "movie"),
                                                                 (operator.eq, F("msg"), "end")))}}
for subtitle_provider in subtitle_providers:
    logger = "%s_subtitle_provider" % subtitle_provider
    feeds[logger] = {"rules_tree": (operator.and_, (operator.eq, F("application"), "tv_shows"),
                                                   (operator.eq, F("logger"), logger))}


def analyze(torrent_files, video_files, views, **kwargs):
    shows = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"subtitles": set()}))))

    for torrent_file in torrent_files:
        args = torrent_file.args
        show = shows[args["show"]][args["season"]][args["episode"]][args["quality"]]
        show["state"] = "downloading"

    for video_file in video_files:
        args = video_file.args
        show = shows[args["show"]][args["season"]][args["episode"]][args["quality"]]
        show["state"] = "downloaded"

        path = os.path.relpath(args["path"], "/media/storage/Torrent/downloads")
        for watched in views:
            if os.path.relpath(watched.args["movie"], "/home/themylogin/Storage/Torrent/downloads") == path:
                show["state"] = "watched"
                show["duration"] = watched.args["duration"]
                show["progress"] = watched.args["progress"]
                break

    for subtitle_provider in subtitle_providers:
        logger = "%s_subtitle_provider" % subtitle_provider
        for subtitle in kwargs[logger]:
            args = subtitle.args
            show = shows[args["show"]][args["season"]][args["episode"]][args["quality"]]
            show["subtitles"].add(subtitle_providers[subtitle_provider])

    return shows
