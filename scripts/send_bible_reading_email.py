from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
BIBLE_DIR = BASE_DIR / "data" / "bible"
KOREAN_BIBLE_PATH = BIBLE_DIR / "개역개정4판.txt"
NIV_OLD_TESTAMENT_DIR = BIBLE_DIR / "niv" / "old_testament"
NIV_NEW_TESTAMENT_DIR = BIBLE_DIR / "niv" / "new_testament"
OUTPUT_DIR = BASE_DIR / "output" / "bible_reading_newsletter"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON_PATH = OUTPUT_DIR / "latest.json"
LATEST_HTML_PATH = OUTPUT_DIR / "latest.html"
KST = timezone(timedelta(hours=9))


BOOK_META = {
    "job": ("욥기", "욥", "Job", "18-Job (욥기).txt", "old"),
    "psa": ("시편", "시", "Psalms", "19-Psalms (시편).txt", "old"),
    "pro": ("잠언", "잠", "Proverbs", "20-Proverbs (잠언).txt", "old"),
    "ecc": ("전도서", "전", "Ecclesiastes", "21-Ecclesiastes (전도서).txt", "old"),
    "sol": ("아가", "아", "Song of Songs", "22-Song of Songs (아가서).txt", "old"),
    "isa": ("이사야", "사", "Isaiah", "23-Isaiah (이사야).txt", "old"),
    "jer": ("예레미야", "렘", "Jeremiah", "24-Jeremiah (예레미야).txt", "old"),
    "lam": ("예레미야애가", "애", "Lamentations", "25-Lamentations (예레미야애가).txt", "old"),
    "eze": ("에스겔", "겔", "Ezekiel", "26-Ezekiel (에스겔).txt", "old"),
    "dan": ("다니엘", "단", "Daniel", "27-Daniel (다니엘).txt", "old"),
    "hos": ("호세아", "호", "Hosea", "28-Hosea (호세아).txt", "old"),
    "joe": ("요엘", "욜", "Joel", "29-Joel (요엘).txt", "old"),
    "amo": ("아모스", "암", "Amos", "30-Amos (아모스).txt", "old"),
    "oba": ("오바댜", "옵", "Obadiah", "31-Obadiah (오바댜).txt", "old"),
    "jon": ("요나", "욘", "Jonah", "32-Jonah (요나).txt", "old"),
    "mic": ("미가", "미", "Micah", "33-Micah (미가).txt", "old"),
    "nah": ("나훔", "나", "Nahum", "34-Nahum (나훔).txt", "old"),
    "hab": ("하박국", "합", "Habakkuk", "35-Habakkuk (하박국).txt", "old"),
    "zep": ("스바냐", "습", "Zephaniah", "36-Zephaniah (스바냐).txt", "old"),
    "hag": ("학개", "학", "Haggai", "37-Haggai (학개).txt", "old"),
    "zec": ("스가랴", "슥", "Zechariah", "38-Zechariah (스가랴).txt", "old"),
    "mal": ("말라기", "말", "Malachi", "39-Malachi (말라기).txt", "old"),
    "mat": ("마태복음", "마", "Matthew", "40-Matthew (마태복음).txt", "new"),
    "mar": ("마가복음", "막", "Mark", "41-Mark (마가복음).txt", "new"),
    "luk": ("누가복음", "눅", "Luke", "42-Luke (누가복음).txt", "new"),
}


READING_PLAN: dict[str, list[dict[str, Any]]] = {
    "2026-06-08": [{"book": "job", "start": 29, "end": 33}],
    "2026-06-09": [{"book": "job", "start": 34, "end": 38}],
    "2026-06-10": [{"book": "job", "start": 39, "end": 42}],
    "2026-06-11": [{"book": "psa", "start": 1, "end": 5}],
    "2026-06-12": [{"book": "psa", "start": 6, "end": 10}],
    "2026-06-13": [{"book": "psa", "start": 11, "end": 15}],
    "2026-06-14": [{"book": "psa", "start": 16, "end": 20}],
    "2026-06-15": [{"book": "psa", "start": 21, "end": 25}],
    "2026-06-16": [{"book": "psa", "start": 26, "end": 30}],
    "2026-06-17": [{"book": "psa", "start": 31, "end": 35}],
    "2026-06-18": [{"book": "psa", "start": 36, "end": 40}],
    "2026-06-19": [{"book": "psa", "start": 41, "end": 45}],
    "2026-06-20": [{"book": "psa", "start": 46, "end": 50}],
    "2026-06-21": [{"book": "psa", "start": 51, "end": 55}],
    "2026-06-22": [{"book": "psa", "start": 56, "end": 60}],
    "2026-06-23": [{"book": "psa", "start": 61, "end": 65}],
    "2026-06-24": [{"book": "psa", "start": 66, "end": 70}],
    "2026-06-25": [{"book": "psa", "start": 71, "end": 75}],
    "2026-06-26": [{"book": "psa", "start": 76, "end": 80}],
    "2026-06-27": [{"book": "psa", "start": 81, "end": 85}],
    "2026-06-28": [{"book": "psa", "start": 86, "end": 89}],
    "2026-06-29": [{"book": "psa", "start": 90, "end": 94}],
    "2026-06-30": [{"book": "psa", "start": 95, "end": 100}],
    "2026-07-01": [{"book": "psa", "start": 101, "end": 106}],
    "2026-07-02": [{"book": "psa", "start": 107, "end": 109}],
    "2026-07-03": [{"book": "psa", "start": 110, "end": 114}],
    "2026-07-04": [{"book": "psa", "start": 115, "end": 118}],
    "2026-07-05": [{"book": "psa", "start": 119, "end": 119}],
    "2026-07-06": [{"book": "psa", "start": 120, "end": 127}],
    "2026-07-07": [{"book": "psa", "start": 128, "end": 134}],
    "2026-07-08": [{"book": "psa", "start": 135, "end": 140}],
    "2026-07-09": [{"book": "psa", "start": 141, "end": 145}],
    "2026-07-10": [{"book": "psa", "start": 146, "end": 150}],
    "2026-07-11": [{"book": "pro", "start": 1, "end": 3}],
    "2026-07-12": [{"book": "pro", "start": 4, "end": 6}],
    "2026-07-13": [{"book": "pro", "start": 7, "end": 9}],
    "2026-07-14": [{"book": "pro", "start": 10, "end": 14}],
    "2026-07-15": [{"book": "pro", "start": 15, "end": 18}],
    "2026-07-16": [{"book": "pro", "start": 19, "end": 21}],
    "2026-07-17": [{"book": "pro", "start": 22, "end": 24}],
    "2026-07-18": [{"book": "pro", "start": 25, "end": 27}],
    "2026-07-19": [{"book": "pro", "start": 28, "end": 31}],
    "2026-07-20": [{"book": "ecc", "start": 1, "end": 4}],
    "2026-07-21": [{"book": "ecc", "start": 5, "end": 8}],
    "2026-07-22": [{"book": "ecc", "start": 9, "end": 12}],
    "2026-07-23": [{"book": "sol", "start": 1, "end": 8}],
    "2026-07-24": [{"book": "isa", "start": 1, "end": 4}],
    "2026-07-25": [{"book": "isa", "start": 5, "end": 8}],
    "2026-07-26": [{"book": "isa", "start": 9, "end": 12}],
    "2026-07-27": [{"book": "isa", "start": 13, "end": 16}],
    "2026-07-28": [{"book": "isa", "start": 17, "end": 20}],
    "2026-07-29": [{"book": "isa", "start": 21, "end": 24}],
    "2026-07-30": [{"book": "isa", "start": 25, "end": 29}],
    "2026-07-31": [{"book": "isa", "start": 30, "end": 33}],
    "2026-08-01": [{"book": "isa", "start": 34, "end": 37}],
    "2026-08-02": [{"book": "isa", "start": 38, "end": 41}],
    "2026-08-03": [{"book": "isa", "start": 42, "end": 44}],
    "2026-08-04": [{"book": "isa", "start": 45, "end": 48}],
    "2026-08-05": [{"book": "isa", "start": 49, "end": 52}],
    "2026-08-06": [{"book": "isa", "start": 53, "end": 57}],
    "2026-08-07": [{"book": "isa", "start": 58, "end": 62}],
    "2026-08-08": [{"book": "isa", "start": 63, "end": 66}],
    "2026-08-09": [{"book": "jer", "start": 1, "end": 4}],
    "2026-08-10": [{"book": "jer", "start": 5, "end": 9}],
    "2026-08-11": [{"book": "jer", "start": 10, "end": 13}],
    "2026-08-12": [{"book": "jer", "start": 14, "end": 17}],
    "2026-08-13": [{"book": "jer", "start": 18, "end": 20}],
    "2026-08-14": [{"book": "jer", "start": 21, "end": 23}],
    "2026-08-15": [{"book": "jer", "start": 24, "end": 27}],
    "2026-08-16": [{"book": "jer", "start": 28, "end": 30}],
    "2026-08-17": [{"label": "개별통독"}],
    "2026-08-18": [{"book": "jer", "start": 31, "end": 33}],
    "2026-08-19": [{"book": "jer", "start": 34, "end": 36}],
    "2026-08-20": [{"book": "jer", "start": 37, "end": 40}],
    "2026-08-21": [{"book": "jer", "start": 41, "end": 44}],
    "2026-08-22": [{"book": "jer", "start": 45, "end": 48}],
    "2026-08-23": [{"book": "jer", "start": 49, "end": 50}],
    "2026-08-24": [{"book": "jer", "start": 51, "end": 52}],
    "2026-08-25": [{"book": "lam", "start": 1, "end": 5}],
    "2026-08-26": [{"book": "eze", "start": 1, "end": 3}],
    "2026-08-27": [{"book": "eze", "start": 4, "end": 6}],
    "2026-08-28": [{"book": "eze", "start": 7, "end": 9}],
    "2026-08-29": [{"book": "eze", "start": 10, "end": 12}],
    "2026-08-30": [{"book": "eze", "start": 13, "end": 15}],
    "2026-08-31": [{"book": "eze", "start": 16, "end": 17}],
    "2026-09-01": [{"book": "eze", "start": 18, "end": 20}],
    "2026-09-02": [{"book": "eze", "start": 21, "end": 22}],
    "2026-09-03": [{"book": "eze", "start": 23, "end": 25}],
    "2026-09-04": [{"book": "eze", "start": 26, "end": 28}],
    "2026-09-05": [{"book": "eze", "start": 29, "end": 32}],
    "2026-09-06": [{"book": "eze", "start": 33, "end": 35}],
    "2026-09-07": [{"book": "eze", "start": 36, "end": 38}],
    "2026-09-08": [{"book": "eze", "start": 39, "end": 40}],
    "2026-09-09": [{"book": "eze", "start": 41, "end": 42}],
    "2026-09-10": [{"book": "eze", "start": 43, "end": 45}],
    "2026-09-11": [{"book": "eze", "start": 46, "end": 48}],
    "2026-09-12": [{"book": "dan", "start": 1, "end": 4}],
    "2026-09-13": [{"book": "dan", "start": 5, "end": 8}],
    "2026-09-14": [{"book": "dan", "start": 9, "end": 12}],
    "2026-09-15": [{"book": "hos", "start": 1, "end": 5}],
    "2026-09-16": [{"book": "hos", "start": 6, "end": 10}],
    "2026-09-17": [{"book": "hos", "start": 11, "end": 14}],
    "2026-09-18": [{"book": "joe", "start": 1, "end": 3}],
    "2026-09-19": [{"book": "amo", "start": 1, "end": 4}],
    "2026-09-20": [{"book": "amo", "start": 5, "end": 9}],
    "2026-09-21": [
        {"book": "oba", "start": 1, "end": 1},
        {"book": "jon", "start": 1, "end": 4},
    ],
    "2026-09-22": [{"book": "mic", "start": 1, "end": 3}],
    "2026-09-23": [{"book": "mic", "start": 4, "end": 7}],
    "2026-09-24": [{"label": "개별통독"}],
    "2026-09-25": [{"label": "개별통독"}],
    "2026-09-26": [{"label": "개별통독"}],
    "2026-09-27": [{"book": "nah", "start": 1, "end": 3}],
    "2026-09-28": [{"book": "hab", "start": 1, "end": 3}],
    "2026-09-29": [
        {"book": "zep", "start": 1, "end": 3},
        {"book": "hag", "start": 1, "end": 2},
    ],
    "2026-09-30": [{"book": "zec", "start": 1, "end": 3}],
    "2026-10-01": [{"book": "zec", "start": 4, "end": 6}],
    "2026-10-02": [{"book": "zec", "start": 7, "end": 10}],
    "2026-10-03": [{"label": "개별통독"}],
    "2026-10-04": [{"book": "zec", "start": 11, "end": 14}],
    "2026-10-05": [{"label": "개별통독"}],
    "2026-10-06": [{"book": "mal", "start": 1, "end": 4}],
    "2026-10-07": [{"book": "mat", "start": 1, "end": 3}],
    "2026-10-08": [{"book": "mat", "start": 4, "end": 6}],
    "2026-10-09": [{"label": "개별통독"}],
    "2026-10-10": [{"book": "mat", "start": 7, "end": 9}],
    "2026-10-11": [{"book": "mat", "start": 10, "end": 12}],
    "2026-10-12": [{"book": "mat", "start": 13, "end": 15}],
    "2026-10-13": [{"book": "mat", "start": 16, "end": 18}],
    "2026-10-14": [{"book": "mat", "start": 19, "end": 21}],
    "2026-10-15": [{"book": "mat", "start": 22, "end": 24}],
    "2026-10-16": [{"book": "mat", "start": 25, "end": 26}],
    "2026-10-17": [{"book": "mat", "start": 27, "end": 28}],
    "2026-10-18": [{"book": "mar", "start": 1, "end": 3}],
    "2026-10-19": [{"book": "mar", "start": 4, "end": 5}],
    "2026-10-20": [{"book": "mar", "start": 6, "end": 8}],
    "2026-10-21": [{"book": "mar", "start": 9, "end": 11}],
    "2026-10-22": [{"book": "mar", "start": 12, "end": 13}],
    "2026-10-23": [{"book": "mar", "start": 14, "end": 16}],
    "2026-10-24": [{"book": "luk", "start": 1, "end": 2}],
    "2026-10-25": [{"book": "luk", "start": 3, "end": 5}],
    "2026-10-26": [{"book": "luk", "start": 6, "end": 7}],
    "2026-10-27": [{"book": "luk", "start": 8, "end": 9}],
    "2026-10-28": [{"book": "luk", "start": 10, "end": 11}],
    "2026-10-29": [{"book": "luk", "start": 12, "end": 13}],
    "2026-10-30": [{"book": "luk", "start": 14, "end": 15}],
    "2026-10-31": [{"book": "luk", "start": 16, "end": 17}],
}


@dataclass(frozen=True)
class Verse:
    number: int
    text: str


@dataclass(frozen=True)
class BilingualChapter:
    book: str
    korean_book_name: str
    english_book_name: str
    chapter_number: int
    korean_verses: list[Verse]
    niv_verses: list[Verse]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(f"{name} is not set.")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a daily Korean/NIV Bible reading email.")
    parser.add_argument("--date", default="", help="Target date in YYYY-MM-DD. Defaults to today in KST.")
    parser.add_argument("--recipient", default="", help="Recipient email override.")
    parser.add_argument("--dry-run", action="store_true", help="Generate output only without sending email.")
    return parser.parse_args()


def resolve_target_date(date_arg: str) -> str:
    if date_arg.strip():
        return date_arg.strip()
    return datetime.now(UTC).astimezone(KST).strftime("%Y-%m-%d")


def get_plan_for_date(target_date: str) -> list[dict[str, Any]]:
    plan = READING_PLAN.get(target_date)
    if not plan:
        raise KeyError(f"No reading plan configured for {target_date}.")
    return plan


def read_korean_bible() -> str:
    if not KOREAN_BIBLE_PATH.exists():
        raise FileNotFoundError(f"Korean Bible text not found: {KOREAN_BIBLE_PATH}")
    return KOREAN_BIBLE_PATH.read_text(encoding="cp949")


def parse_korean_chapter(source: str, book_abbreviation: str, chapter_number: int) -> list[Verse]:
    marker = re.compile(r"(?<![가-힣])([가-힣]{1,4})(\d+):(\d+)\s+")
    matches = list(marker.finditer(source))
    verses: list[Verse] = []
    for index, match in enumerate(matches):
        if match.group(1) != book_abbreviation or int(match.group(2)) != chapter_number:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        text = re.sub(r"\s+", " ", source[match.end():end]).strip()
        verses.append(Verse(number=int(match.group(3)), text=text))
    if not verses:
        raise ValueError(f"No Korean verses found for {book_abbreviation} {chapter_number}.")
    return verses


def niv_book_path(book: str) -> Path:
    _, _, _, filename, testament = BOOK_META[book]
    directory = NIV_OLD_TESTAMENT_DIR if testament == "old" else NIV_NEW_TESTAMENT_DIR
    return directory / filename


def parse_niv_chapter(book: str, chapter_number: int) -> list[Verse]:
    path = niv_book_path(book)
    if not path.exists():
        raise FileNotFoundError(f"NIV text not found: {path}")
    pattern = re.compile(r"^(\d+):(\d+)\s+(.*)$")
    verses: list[Verse] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = pattern.match(line.strip())
        if match and int(match.group(1)) == chapter_number:
            verses.append(Verse(number=int(match.group(2)), text=match.group(3).strip()))
    if not verses:
        raise ValueError(f"No NIV verses found for {book} {chapter_number}.")
    return verses


def load_chapter(korean_source: str, book: str, chapter_number: int) -> BilingualChapter:
    korean_name, korean_abbreviation, english_name, _, _ = BOOK_META[book]
    return BilingualChapter(
        book=book,
        korean_book_name=korean_name,
        english_book_name=english_name,
        chapter_number=chapter_number,
        korean_verses=parse_korean_chapter(korean_source, korean_abbreviation, chapter_number),
        niv_verses=parse_niv_chapter(book, chapter_number),
    )


def expand_plan_entries(plan_entries: list[dict[str, Any]]) -> list[BilingualChapter]:
    if all("label" in entry for entry in plan_entries):
        return []
    korean_source = read_korean_bible()
    chapters: list[BilingualChapter] = []
    for entry in plan_entries:
        if "label" in entry:
            continue
        for chapter_number in range(entry["start"], entry["end"] + 1):
            chapters.append(load_chapter(korean_source, entry["book"], chapter_number))
    return chapters


def build_reference_text(plan_entries: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for entry in plan_entries:
        if "label" in entry:
            parts.append(entry["label"])
            continue
        book_name = BOOK_META[entry["book"]][0]
        chapter_range = str(entry["start"]) if entry["start"] == entry["end"] else f"{entry['start']}-{entry['end']}"
        parts.append(f"{book_name} {chapter_range}장")
    return ", ".join(parts)


def render_verse(number: int, text: str) -> str:
    return (
        "<div style='margin-top:5px;line-height:1.65;font-size:14px;color:#222'>"
        f"<strong style='color:#666'>{number}</strong>&nbsp;{escape(text)}"
        "</div>"
    )


def render_chapter_html(chapter: BilingualChapter) -> str:
    korean = {verse.number: verse.text for verse in chapter.korean_verses}
    niv = {verse.number: verse.text for verse in chapter.niv_verses}
    verse_numbers = sorted(set(korean) | set(niv))
    verse_rows = "".join(
        (
            "<tr>"
            "<td width='50%' valign='top' style='padding:2px 14px 7px 0;border-right:1px solid #e1e1e1'>"
            f"{render_verse(number, korean.get(number, ''))}</td>"
            "<td width='50%' valign='top' style='padding:2px 0 7px 14px'>"
            f"{render_verse(number, niv.get(number, ''))}</td>"
            "</tr>"
        )
        for number in verse_numbers
    )
    return (
        "<section style='margin-top:24px;padding-top:18px;border-top:1px solid #d9d9d9'>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' style='table-layout:fixed;border-collapse:collapse'>"
        "<tr>"
        "<td width='50%' valign='top' style='padding:0 14px 0 0;border-right:1px solid #e1e1e1'>"
        f"<div style='font-size:18px;font-weight:700;color:#111'>{escape(chapter.korean_book_name)} {chapter.chapter_number}장</div>"
        "<div style='margin-top:3px;font-size:12px;color:#777'>개역개정</div>"
        "</td>"
        "<td width='50%' valign='top' style='padding:0 0 0 14px'>"
        f"<div style='font-size:18px;font-weight:700;color:#111'>{escape(chapter.english_book_name)} {chapter.chapter_number}</div>"
        "<div style='margin-top:3px;font-size:12px;color:#777'>NIV</div>"
        "</td>"
        "</tr>"
        f"{verse_rows}"
        "</table>"
        "</section>"
    )


def render_email_html(payload: dict[str, Any]) -> str:
    if payload["chapters"]:
        content = "".join(render_chapter_html(chapter) for chapter in payload["chapters"])
        intro = "금일 성경읽기 본문을 개역개정과 NIV로 함께 전달드립니다."
    else:
        content = (
            "<div style='margin-top:24px;padding:28px 20px;border:1px solid #e1e1e1;text-align:center;"
            "font-size:16px;color:#333'>오늘은 개별통독 일정입니다.</div>"
        )
        intro = "금일은 개별통독 일정입니다."
    return (
        "<html><body style='margin:0;background:#ffffff;color:#111;font-family:Arial,Apple SD Gothic Neo,sans-serif'>"
        "<div style='max-width:1100px;margin:0 auto;padding:24px 20px 40px'>"
        f"<div style='font-size:14px;line-height:1.7'>일자: {escape(payload['target_date'])}<br>본문: {escape(payload['reference'])}</div>"
        f"<div style='margin-top:16px;font-size:14px;line-height:1.7'>안녕하세요.<br><br>{escape(intro)}</div>"
        f"{content}"
        "<div style='margin-top:24px;padding-top:16px;border-top:1px solid #d9d9d9;font-size:13px;line-height:1.7;color:#555'>감사합니다.</div>"
        "</div></body></html>"
    )


def build_payload(target_date: str) -> dict[str, Any]:
    plan_entries = get_plan_for_date(target_date)
    return {
        "target_date": target_date,
        "reference": build_reference_text(plan_entries),
        "chapters": expand_plan_entries(plan_entries),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def save_outputs(payload: dict[str, Any], html_body: str) -> None:
    serializable = {
        "target_date": payload["target_date"],
        "reference": payload["reference"],
        "generated_at": payload["generated_at"],
        "chapters": [
            {
                "book": chapter.book,
                "book_name": chapter.korean_book_name,
                "english_book_name": chapter.english_book_name,
                "chapter_number": chapter.chapter_number,
                "korean_verses": [vars(verse) for verse in chapter.korean_verses],
                "niv_verses": [vars(verse) for verse in chapter.niv_verses],
            }
            for chapter in payload["chapters"]
        ],
    }
    LATEST_JSON_PATH.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_HTML_PATH.write_text(html_body, encoding="utf-8")


def send_email(subject: str, html_body: str, recipient_override: str) -> None:
    sender = require_env("GMAIL_USERNAME")
    password = require_env("GMAIL_APP_PASSWORD")
    recipient = recipient_override.strip() or os.getenv("BIBLE_READING_EMAIL_TO", "").strip() or sender
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.attach(MIMEText(html_body, "html", "utf-8"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, [recipient], message.as_string())


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date)
    payload = build_payload(target_date)
    html_body = render_email_html(payload)
    save_outputs(payload, html_body)
    if args.dry_run:
        print(f"Generated Bible reading email for {target_date}.")
        return 0
    subject = f"성경읽기 안내 {target_date} {payload['reference']}"
    send_email(subject, html_body, args.recipient)
    print(f"Sent Bible reading email for {target_date}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
