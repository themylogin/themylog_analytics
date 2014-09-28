# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

from datetime import datetime
import operator

from themylog.rules_tree import Param as P, RecordField as F

feeds = {"last_sleep_track": {"rules_tree": (operator.and_, (operator.eq, F("logger"), "sleep_tracker"),
                                                            (operator.or_, (operator.eq, F("msg"), "woke_up"),
                                                                           (operator.eq, F("msg"), "fall_asleep"))),
                              "limit": 1},
         "odometer_logs": {"rules_tree": (operator.and_, (operator.eq, F("application"), "usage_stats"),
                                                         (operator.gt, F("datetime"), P("last_sleep_track_datetime"))),
                           "params": {"last_sleep_track_datetime": lambda last_sleep_track: last_sleep_track.args["at"]
                                                                                            if last_sleep_track.msg == "woke_up"
                                                                                            else datetime.max}}}


def analyze(last_sleep_track, odometer_logs, now):
    if last_sleep_track.msg == "woke_up":
        woke_up_at = last_sleep_track.args["at"]
        seconds_up = (now - woke_up_at).total_seconds()

        seconds_pc = 0
        for prev_log, log in zip(odometer_logs, [None] + odometer_logs)[1:]:
            if log.args["keys"] > 0 or log.args["pixels"] > 0:
                seconds_pc += (log.datetime - prev_log.datetime).total_seconds()

        return {"state": "up",
                "seconds_up": seconds_up,
                "seconds_pc": seconds_pc}
    else:
        return {"state": "down"}
