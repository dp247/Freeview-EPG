import unittest
from datetime import timedelta

import pytest

pytz = pytest.importorskip("pytz")
etree = pytest.importorskip("lxml.etree")

from src.xmltv import build_xmltv, clean_text, parse_duration, remove_control_characters


class TestXmltvHelpers(unittest.TestCase):
    def test_remove_control_characters(self):
        self.assertEqual(remove_control_characters("Hello\x00World\n"), "HelloWorld")

    def test_clean_text_removes_tags_and_episode_info(self):
        self.assertEqual(clean_text("Show [HD]"), "Show")
        self.assertEqual(clean_text("Show S3 Ep5"), "Show")

    def test_parse_duration_valid(self):
        self.assertEqual(parse_duration("PT1H30M"), timedelta(hours=1, minutes=30))

    def test_parse_duration_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("P1Y2M")


class TestBuildXmltv(unittest.TestCase):
    def test_build_xmltv_sorting_and_structure(self):
        tz = pytz.timezone("Europe/London")
        channels = [
            {"xmltv_id": "b", "name": "Bravo", "lang": "en", "icon_url": None},
            {"xmltv_id": "a", "name": "Alpha", "lang": "en", "icon_url": "http://img/a.png"},
        ]
        programmes = [
            {
                "channel": "b",
                "start": 20,
                "stop": 40,
                "title": "Late",
                "description": "Drama [HD]",
                "icon": None,
                "premiere": False,
            },
            {
                "channel": "a",
                "start": 10,
                "stop": 20,
                "title": "Early",
                "description": "Intro\n",
                "icon": "http://img/show.png",
                "premiere": True,
                "season": "2",
                "episode": "3",
            },
            {
                "channel": "a",
                "start": 5,
                "stop": 15,
                "title": "Earlier",
                "description": None,
                "icon": None,
                "premiere": False,
            },
        ]

        xml_bytes = build_xmltv(channels, programmes, tz)
        root = etree.fromstring(xml_bytes)

        channel_ids = [el.get("id") for el in root.findall("channel")]
        self.assertEqual(channel_ids, ["a", "b"])

        programme_titles = [el.findtext("title") for el in root.findall("programme")]
        self.assertEqual(programme_titles, ["Earlier", "Early", "Late"])

        desc_text = root.findall("programme")[2].findtext("desc")
        self.assertEqual(desc_text, "Drama")

        early_programme = root.findall("programme")[1]
        episode_nums = [el.text for el in early_programme.findall("episode-num")]
        self.assertEqual(episode_nums, ["1.2.0", "S2E3"])
        self.assertIsNotNone(early_programme.find("premiere"))


if __name__ == "__main__":
    unittest.main()
