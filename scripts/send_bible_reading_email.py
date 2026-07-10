from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]
TEXT_DIR = BASE_DIR / "data" / "community_bible" / "rkb_text"
OUTPUT_DIR = BASE_DIR / "output" / "bible_reading_newsletter"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON_PATH = OUTPUT_DIR / "latest.json"
LATEST_HTML_PATH = OUTPUT_DIR / "latest.html"
KST = timezone(timedelta(hours=9))


BOOK_META = {
    "job": ("욥기", "18_job"),
    "psa": ("시편", "19_psa"),
    "pro": ("잠언", "20_pro"),
    "ecc": ("전도서", "21_ecc"),
    "sol": ("아가", "22_sol"),
    "isa": ("이사야", "23_isa"),
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
}


@dataclass
class Verse:
    number: str
    text: str


@dataclass
class Chapter:
    title: str
    subtitles: list[str]
    verses: list[Verse]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(f"{name} is not set.")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send daily Korean Bible reading email.")
    parser.add_argument("--date", default="", help="Target date in YYYY-MM-DD. Defaults to today in KST.")
    parser.add_argument("--recipient", default="", help="Recipient email override.")
    parser.add_argument("--dry-run", action="store_true", help="Generate output only without sending email.")
    return parser.parse_args()


def resolve_target_date(date_arg: str) -> str:
    if date_arg.strip():
        return date_arg.strip()
    kst_now = datetime.now(UTC).astimezone(KST)
    return kst_now.strftime("%Y-%m-%d")


def get_plan_for_date(target_date: str) -> list[dict[str, Any]]:
    plan = READING_PLAN.get(target_date)
    if not plan:
        raise KeyError(f"No reading plan configured for {target_date}.")
    return plan


def chapter_file_path(book: str, chapter_number: int) -> Path:
    _, prefix = BOOK_META[book]
    return TEXT_DIR / f"{prefix}_ch_{chapter_number:03d}.html"


def load_chapter(book: str, chapter_number: int) -> Chapter:
    path = chapter_file_path(book, chapter_number)
    raw_html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw_html, "html.parser")

    title = soup.find("cn")
    subtitles = [node.get_text(strip=True) for node in soup.select("div.s1, div.s2, div.s3") if node.get_text(strip=True)]
    verses: list[Verse] = []
    for verse in soup.find_all("verse"):
        number_node = verse.find("ver")
        body_node = verse.find("verse_body")
        if not number_node or not body_node:
            continue
        verses.append(
            Verse(
                number=number_node.get_text(strip=True),
                text=body_node.get_text(strip=True),
            )
        )
    return Chapter(
        title=title.get_text(" ", strip=True) if title else f"{BOOK_META[book][0]} {chapter_number}",
        subtitles=subtitles,
        verses=verses,
    )


def expand_plan_entries(plan_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for entry in plan_entries:
        for chapter_number in range(entry["start"], entry["end"] + 1):
            expanded.append(
                {
                    "book": entry["book"],
                    "book_name": BOOK_META[entry["book"]][0],
                    "chapter_number": chapter_number,
                    "chapter": load_chapter(entry["book"], chapter_number),
                }
            )
    return expanded


def build_reference_text(plan_entries: list[dict[str, Any]]) -> str:
    parts = []
    for entry in plan_entries:
        book_name = BOOK_META[entry["book"]][0]
        if entry["start"] == entry["end"]:
            parts.append(f"{book_name} {entry['start']}장")
        else:
            parts.append(f"{book_name} {entry['start']}-{entry['end']}장")
    return ", ".join(parts)


def render_chapter_html(chapter: Chapter) -> str:
    subtitles_html = "".join(
        f"<div style='margin:6px 0 0;color:#444;font-size:13px;font-weight:600'>{escape(subtitle)}</div>"
        for subtitle in chapter.subtitles
    )
    verses_html = "".join(
        (
            "<div style='margin-top:4px;line-height:1.7;font-size:14px;color:#222'>"
            f"{escape(verse.number)}&nbsp;{escape(verse.text)}"
            "</div>"
        )
        for verse in chapter.verses
    )
    return (
        "<section style='margin-top:20px;padding-top:16px;border-top:1px solid #d9d9d9'>"
        f"<div style='font-size:18px;font-weight:700;color:#111'>{escape(chapter.title)}</div>"
        f"{subtitles_html}"
        f"<div style='margin-top:10px'>{verses_html}</div>"
        "</section>"
    )


def render_email_html(payload: dict[str, Any]) -> str:
    chapter_sections = "".join(render_chapter_html(item["chapter"]) for item in payload["chapters"])
    return (
        "<html><body style='margin:0;background:#ffffff;color:#111;font-family:Arial,Apple SD Gothic Neo,sans-serif'>"
        "<div style='max-width:920px;margin:0 auto;padding:24px 20px 40px'>"
        f"<div style='margin-top:10px;font-size:14px;line-height:1.7'>일자: {escape(payload['target_date'])}<br>본문: {escape(payload['reference'])}</div>"
        "<div style='margin-top:16px;font-size:14px;line-height:1.7'>"
        "안녕하세요.<br><br>"
        "금일 성경읽기 본문을 아래와 같이 전달드립니다.<br>"
        "</div>"
        f"{chapter_sections}"
        "<div style='margin-top:24px;padding-top:16px;border-top:1px solid #d9d9d9;font-size:13px;line-height:1.7;color:#555'>"
        "감사합니다."
        "</div>"
        "</div></body></html>"
    )


def build_payload(target_date: str) -> dict[str, Any]:
    plan_entries = get_plan_for_date(target_date)
    chapters = expand_plan_entries(plan_entries)
    payload = {
        "target_date": target_date,
        "reference": build_reference_text(plan_entries),
        "chapters": chapters,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return payload


def save_outputs(payload: dict[str, Any], html_body: str) -> None:
    serializable = {
        "target_date": payload["target_date"],
        "reference": payload["reference"],
        "generated_at": payload["generated_at"],
        "chapters": [
            {
                "book": item["book"],
                "book_name": item["book_name"],
                "chapter_number": item["chapter_number"],
                "title": item["chapter"].title,
                "subtitles": item["chapter"].subtitles,
                "verses": [{"number": verse.number, "text": verse.text} for verse in item["chapter"].verses],
            }
            for item in payload["chapters"]
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
