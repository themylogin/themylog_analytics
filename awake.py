# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

from datetime import datetime
import operator

from themylog.rules_tree import Param as P, RecordField as F

since_awake = (operator.ge, F("datetime"), P("last_sleep_track_datetime"))
since_awake_params = {"last_sleep_track_datetime": lambda last_sleep_track: last_sleep_track.args["end"]
                                                                            if last_sleep_track.msg == "woke_up"
                                                                            else datetime.max}

feeds = {"last_sleep_track": {"rules_tree": (operator.and_, (operator.eq, F("logger"), "sleep_tracker"),
                                                            (operator.or_, (operator.eq, F("msg"), "woke_up"),
                                                                           (operator.eq, F("msg"), "fall_asleep"))),
                              "limit": 1},
         "odometer_logs": {"rules_tree": (operator.and_, (operator.eq, F("application"), "usage_stats"),
                                                         since_awake),
                           "params": since_awake_params},
         "theMediaShell": {"rules_tree": (operator.and_, (operator.and_, (operator.eq, F("application"), "theMediaShell"),
                                                                         (operator.eq, F("msg"), "progress")),
                                                         since_awake),
                           "params": since_awake_params},
         "smarthome": {"rules_tree": (operator.and_, (operator.and_, (operator.eq, F("application"), "smarthome"),
                                                                     (operator.and_, (operator.or_, (operator.eq, F("logger"), "all_lightning_except_projector"),
                                                                                                    (operator.eq, F("logger"), "projector")),
                                                                                     (operator.eq, F("msg"), "on_changed"))),
                                                     since_awake),
                       "params": since_awake_params}}


def analyze(last_sleep_track, odometer_logs, theMediaShell, smarthome, now):
    if last_sleep_track.msg == "woke_up":
        woke_up_at = last_sleep_track.args["end"]
        seconds_up = (now - woke_up_at).total_seconds()

        seconds_pc = 0
        for prev_log, log in zip(odometer_logs, [None] + odometer_logs)[1:]:
            if log.args["keys"] > 0 or log.args["pixels"] > 0:
                seconds_pc += (log.datetime - prev_log.datetime).total_seconds()

        seconds_tv_on = 0
        segments = [(datetime.min, {"all_lightning_except_projector": False, "projector": False})]
        for item in reversed(smarthome):
            segments.append((item.datetime, dict(segments[-1][1], **{item.logger: item.args["value"]})))
        segments.append((now, segments[-1][1]))
        for enter, exit in zip(segments, segments[1:]):
            if enter[1] == {"all_lightning_except_projector": False, "projector": True}:
                seconds_tv_on += (exit[0] - enter[0]).total_seconds()

        return {"state": "up",
                "seconds_up": seconds_up,
                "seconds_pc": seconds_pc,
                "seconds_tv": len(theMediaShell),
                "seconds_tv_on": seconds_tv_on}
    else:
        fall_asleep_at = last_sleep_track.args["start"]
        seconds_down = (now - fall_asleep_at).total_seconds()
        return {"state": "down",
                "seconds_down": seconds_down}
