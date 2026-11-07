"""
Tests that do NOT need Spark (parsing, file discovery, task balancing).

    python3 -m unittest bigdata/tests/test_clean_records.py -v
    SAMPLE_JSONL=/path/to/one_channel.jsonl python3 -m unittest bigdata/tests/test_clean_records.py -v
"""
import json
import os
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path

SPARK_DIR = Path(__file__).resolve().parent.parent / "spark"
sys.path.insert(0, str(SPARK_DIR))

from clean_records import clean_row, to_epoch   # noqa: E402
from inputs import list_inputs, open_text        # noqa: E402
from job1_clean import balanced_groups           # noqa: E402


def msg(mid, date, channel=100, views=10, forwards=0, fwd=None, kind="Message"):
    return json.dumps({"_": kind, "id": mid, "date": date,
                       "peer_id": {"_": "PeerChannel", "channel_id": channel},
                       "views": views, "forwards": forwards, "fwd_from": fwd})


def fwd(origin, post, date, peer="PeerChannel"):
    key = "channel_id" if peer == "PeerChannel" else "user_id"
    return {"_": "MessageFwdHeader", "date": date, "channel_post": post,
            "from_id": {"_": peer, key: origin} if origin is not None else None}


class TestCleanRow(unittest.TestCase):
    def test_plain_message(self):
        row, st = clean_row(msg(2, "2024-01-10T12:00:00+00:00", 100, 7, 0))
        self.assertEqual(st, "ok")
        self.assertEqual(row, (100, 2, to_epoch("2024-01-10T12:00:00"), 7, 0, "", None, None, None))

    def test_forward_from_channel(self):
        row, _ = clean_row(msg(1, "2024-01-10T10:00:00+00:00", 100, 5, 1,
                               fwd(7, 5, "2024-01-10T09:00:00+00:00")))
        self.assertEqual(row[5:], ("channel", 7, 5, to_epoch("2024-01-10T09:00:00")))
        self.assertEqual(row[2] - row[8], 3600)               # one hour after the original

    def test_forward_kinds(self):
        user, _ = clean_row(msg(2, "2024-01-11T00:00:00+00:00", 200, None, None,
                                fwd(55, None, "2024-01-01T00:00:00+00:00", "PeerUser")))
        hidden, _ = clean_row(msg(3, "2024-01-12T00:00:00+00:00", 200, 2, 1,
                                  fwd(None, None, "2024-01-02T00:00:00+00:00")))
        self.assertEqual((user[5], user[6]), ("user", None))
        self.assertEqual((hidden[5], hidden[6]), ("hidden", None))
        self.assertIsNone(user[3])                             # missing views stay None

    def test_channel_forward_without_post_id(self):
        row, _ = clean_row(msg(4, "2024-01-12T00:00:00+00:00", 100, 1, 0,
                               fwd(7, None, "2024-01-02T00:00:00+00:00")))
        self.assertEqual((row[5], row[6], row[7]), ("channel", 7, None))

    def test_ignored_lines(self):
        self.assertEqual(clean_row(msg(9, "2024-01-01T00:00:00+00:00", kind="MessageService"))[1], "skipped")
        self.assertEqual(clean_row("{not json")[1], "bad_json")
        self.assertEqual(clean_row("   ")[1], "skipped")

    def test_default_channel_when_peer_missing(self):
        d = json.loads(msg(1, "2024-01-01T00:00:00+00:00"))
        d["peer_id"] = None
        self.assertEqual(clean_row(json.dumps(d), 4242)[0][0], 4242)

    def test_date_formats(self):
        self.assertEqual(to_epoch("2024-01-25 16:13:00.000000"), to_epoch("2024-01-25T16:13:00+00:00"))
        self.assertIsNone(to_epoch(None))
        self.assertIsNone(to_epoch("garbage"))


class TestInputs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        line = msg(1, "2024-01-10T10:00:00+00:00", 111) + "\n"
        (self.tmp / "plain" / "1_to_2").mkdir(parents=True)
        (self.tmp / "plain" / "1_to_2" / "111.jsonl").write_text(line)
        (self.tmp / "plain" / "1_to_2" / "222.jsonl").write_text(line * 3)
        (self.tmp / "plain" / "1_to_2" / "notes.txt").write_text("ignore me")
        self.zip_folder = self.tmp / "lot_A.zip"                 # zip with a folder inside
        with zipfile.ZipFile(self.zip_folder, "w") as z:
            z.writestr("3_to_4/333.jsonl", line * 2)
            z.writestr("3_to_4/", "")
        self.zip_root = self.tmp / "rootzip.zip"                 # files at the root
        with zipfile.ZipFile(self.zip_root, "w") as z:
            z.writestr("444.jsonl", line)
        (self.tmp / "zips").mkdir()
        for z in (self.zip_folder, self.zip_root):
            (self.tmp / "zips" / z.name).write_bytes(z.read_bytes())

    def found(self, raw):
        return sorted((i["batch"], i["channel"]) for i in list_inputs(raw))

    def test_plain_folder(self):
        self.assertEqual(self.found(self.tmp / "plain"), [("1_to_2", 111), ("1_to_2", 222)])

    def test_zip_with_folder(self):
        self.assertEqual(self.found(self.zip_folder), [("3_to_4", 333)])

    def test_zip_with_root_files(self):
        self.assertEqual(self.found(self.zip_root), [("rootzip", 444)])

    def test_folder_of_zips(self):
        self.assertEqual(self.found(self.tmp / "zips"), [("3_to_4", 333), ("rootzip", 444)])

    def test_zip_member_reads_same_as_plain(self):
        item = next(iter(list_inputs(self.zip_folder)))
        fin, closer = open_text(item["src"], item["member"])
        try:
            self.assertEqual(len(fin.read().splitlines()), 2)
        finally:
            closer.close()


class TestBalancing(unittest.TestCase):
    def test_every_file_assigned_once_and_load_is_even(self):
        sizes = [2000, 900, 800, 700, 100, 90, 80, 70, 10, 5, 5, 1]
        items = [{"src": f"f{i}", "member": None, "channel": i, "size": s}
                 for i, s in enumerate(sizes)]
        groups = balanced_groups(items, 3)
        self.assertEqual(len(groups), 3)
        by_src = {i["src"]: i["size"] for i in items}
        assigned = [t[0] for g in groups for t in g]
        self.assertEqual(sorted(assigned), sorted(by_src))           # nothing lost, nothing twice
        totals = sorted(sum(by_src[t[0]] for t in g) for g in groups)
        self.assertEqual(totals[-1], 2000)                            # the biggest file sits alone
        self.assertLessEqual(totals[-1] - totals[0], 2000 - 1260)    # others are close to each other

    def test_fewer_files_than_groups(self):
        items = [{"src": "a", "member": None, "channel": 1, "size": 5}]
        self.assertEqual(len(balanced_groups(items, 12)), 1)


@unittest.skipUnless(os.environ.get("SAMPLE_JSONL") and Path(os.environ["SAMPLE_JSONL"]).exists(),
                     "set SAMPLE_JSONL to a real .jsonl file")
class TestRealSample(unittest.TestCase):
    def test_counts_match_independent_computation(self):
        path = Path(os.environ["SAMPLE_JSONL"])
        exp = Counter()
        rows = Counter()
        for line in path.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            if d.get("_") == "Message":
                exp["messages"] += 1
                f = d.get("fwd_from")
                if f:
                    exp["forwards"] += 1
                    fid = f.get("from_id") or {}
                    if fid.get("_") == "PeerChannel":
                        exp["channel_forwards"] += 1
                        if f.get("channel_post") is not None:
                            exp["with_post"] += 1
                exp["views"] += d.get("views") or 0
            row, st = clean_row(line, path.stem and int(path.stem) if path.stem.isdigit() else None)
            rows[st] += 1
            if row:
                rows["rows"] += 1
                rows["views"] += row[3] or 0
                if row[5]:
                    rows["forwards"] += 1
                if row[5] == "channel":
                    rows["channel_forwards"] += 1
                    if row[7] is not None:
                        rows["with_post"] += 1
        self.assertEqual(rows["rows"], exp["messages"])
        self.assertEqual(rows["forwards"], exp["forwards"])
        self.assertEqual(rows["channel_forwards"], exp["channel_forwards"])
        self.assertEqual(rows["with_post"], exp["with_post"])
        self.assertEqual(rows["views"], exp["views"])


if __name__ == "__main__":
    unittest.main()
