# Bible Reading Newsletter

매일 정해진 성경 읽기 범위를 **개역개정(왼쪽)**과 **NIV(오른쪽)** 두 열로 구성해 이메일로 보내는 GitHub Actions 프로젝트입니다. 발송 후 생성된 HTML과 JSON을 저장소에 자동으로 기록합니다.

## 동작 방식

1. `.github/workflows/bible-reading-newletter.yml`이 매일 `20:00 UTC`(한국 시간 오전 5시)에 실행됩니다.
2. `scripts/send_bible_reading_email.py`가 해당 날짜의 읽기표를 찾습니다.
3. 개역개정 통합 TXT와 책별 NIV TXT에서 필요한 장과 절을 읽습니다.
4. 개역개정/NIV를 좌우 두 열로 배치한 HTML 이메일을 Gmail SMTP로 발송합니다.
5. 마지막 생성 결과를 `output/bible_reading_newsletter/latest.html`과 `latest.json`에 저장하고 Actions가 자동 커밋합니다.

`개별통독` 날짜에는 성경 본문 대신 개별통독 안내문을 발송합니다.

## 데이터 구조

```text
data/bible/
├─ 개역개정4판.txt
└─ niv/
   ├─ old_testament/
   │  ├─ 01-Genesis (창세기).txt
   │  └─ ...
   └─ new_testament/
      ├─ 40-Matthew (마태복음).txt
      └─ ...
```

- 개역개정: CP949 인코딩, `창1:1 본문` 형식의 통합 파일
- NIV: UTF-8/ASCII 호환 인코딩, `1:1 text` 형식의 책별 파일

성경 번역문을 공개 저장소에 올리거나 배포하기 전에는 해당 번역본의 이용·배포 권한을 확인해야 합니다.

## 읽기표 수정

`scripts/send_bible_reading_email.py`의 `READING_PLAN`에 날짜별 항목을 추가합니다.

```python
"2026-10-07": [{"book": "mat", "start": 1, "end": 3}],
"2026-10-09": [{"label": "개별통독"}],
```

새 책을 처음 사용할 때는 같은 파일의 `BOOK_META`에 책 이름, 개역개정 약어, 영문 이름, NIV 파일명, 구약/신약 구분을 등록합니다.

## 로컬 테스트

메일을 보내지 않고 결과만 생성하려면 저장소 루트에서 실행합니다.

```bash
python scripts/send_bible_reading_email.py --date 2026-10-07 --dry-run
```

결과는 다음 파일에 생성됩니다.

- `output/bible_reading_newsletter/latest.html`
- `output/bible_reading_newsletter/latest.json`

## GitHub Secrets

저장소의 **Settings → Secrets and variables → Actions**에 아래 값을 등록해야 합니다.

- `GMAIL_USERNAME`: 발신 Gmail 주소
- `GMAIL_APP_PASSWORD`: Gmail 앱 비밀번호

수신 주소는 워크플로의 `BIBLE_READING_EMAIL_TO` 값으로 설정합니다.

## 수동 실행

GitHub 저장소의 **Actions → Bible Reading Newsletter → Run workflow**에서 실행할 수 있습니다. `target_date`에 `YYYY-MM-DD` 날짜를 넣으면 해당 날짜를 시험 발송합니다.
