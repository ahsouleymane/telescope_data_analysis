"""
Pure-Python parsing of one Telegram message (Telethon JSON) into a typed row.
No Spark import here, so it is unit-tested without Spark and runs inside the
Spark Python workers.

CLEAN ROW (tuple, same order as CLEAN_COLUMNS):

  dest_channel    int   channel that holds the message (= the file's channel)
  msg_id          int
  ts              int   epoch seconds, UTC
  views           int   or None
  forwards        int   how many times others forwarded this message, or None
  kind            str   ''        not a forward
                        'channel' forwarded from a public channel (origin known)
                        'user'    forwarded from a user
                        'hidden'  forwarded, origin hidden by Telegram privacy
  origin_channel  int   only when kind == 'channel'
  origin_post     int   id of the original post (may be None)
  origin_ts       int   epoch seconds of the original post, or None

Dates are stored as epoch seconds on purpose: converting to calendar dates is
done in Spark under spark.sql.session.timeZone=UTC, which avoids the
local-timezone surprises of Python datetimes in PySpark.
"""

import re
from calendar import timegm
from time import strptime

try:                                    # optional speed-up
    import orjson as _json
    loads = _json.loads
except ImportError:                     # pragma: no cover
    import json as _json
    loads = _json.loads

CLEAN_COLUMNS = ["dest_channel", "msg_id", "ts", "views", "forwards", "kind",
                 "origin_channel", "origin_post", "origin_ts"]

_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})")


def to_epoch(value):
    """Any Telegram date string -> epoch seconds (UTC), or None. Timezone suffix ignored (data is UTC)."""
    if not value:
        return None
    m = _TS_RE.search(str(value))
    if not m:
        return None
    try:
        return timegm(strptime(f"{m.group(1)}T{m.group(2)}", "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def peer(p):
    """{'_':'PeerChannel','channel_id':1} -> ('channel', 1); unknown -> ('', None)."""
    if isinstance(p, dict):
        for key in ("channel_id", "user_id", "chat_id"):
            if p.get(key) is not None:
                return key[:-3], int(p[key])
    return "", None


def _int(v):
    return None if v is None else int(v)


def clean_row(line, default_channel=None):
    """
    One JSONL line -> (row | None, status), status in 'ok' / 'bad_json' / 'skipped'.
    Service messages (joins, pins...) and empty lines are 'skipped'.
    """
    line = line.strip()
    if not line:
        return None, "skipped"
    try:
        d = loads(line)
    except Exception:
        return None, "bad_json"
    if not isinstance(d, dict) or d.get("_") != "Message":
        return None, "skipped"

    kind, cid = peer(d.get("peer_id"))
    dest = cid if kind == "channel" else default_channel

    fkind, o_ch, o_post, o_ts = "", None, None, None
    fwd = d.get("fwd_from")
    if fwd:
        pk, pid = peer(fwd.get("from_id"))
        o_ts = to_epoch(fwd.get("date"))
        if pk == "channel":
            fkind, o_ch, o_post = "channel", pid, _int(fwd.get("channel_post"))
        elif pk == "user":
            fkind = "user"
        else:
            fkind = "hidden"

    return (dest, _int(d.get("id")), to_epoch(d.get("date")), _int(d.get("views")),
            _int(d.get("forwards")), fkind, o_ch, o_post, o_ts), "ok"
