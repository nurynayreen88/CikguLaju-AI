"""Forward authenticated Web uploads to the existing private backend."""
import base64
import json
from urllib.error import HTTPError
from urllib.request import Request, build_opener

from web.native_telegram_rph_client import BlockRedirects, NativeRPHUnavailable
from web.native_verified_rpt_rph_client import _backend
from web.timetable_upload import (
    MAX_RESULT, READER_PATH, TimetableReaderUnavailable, UnreadableTimetable,
    upload_mime, validate_result,
)


def read_uploaded_timetable(data, classes):
    mime = upload_mime(data)
    try:
        base, token = _backend()
        encoded = base64.b64encode(json.dumps(classes, ensure_ascii=False).encode()).decode()
        req = Request(base + READER_PATH, data=data, headers={
            "Authorization": "Bearer " + token,
            "Content-Type": mime,
            "Accept": "application/json",
            "X-Timetable-Classes": encoded,
            "X-Timetable-Review": "1",
        }, method="POST")
        with build_opener(BlockRedirects()).open(req, timeout=18) as response:
            payload = response.read(MAX_RESULT + 1)
        if len(payload) > MAX_RESULT:
            raise TimetableReaderUnavailable
        return validate_result(json.loads(payload))
    except HTTPError as exc:
        with exc:
            if exc.code in (400, 422):
                try:
                    message = json.loads(exc.read(2048))["error"]
                    if isinstance(message, str) and 0 < len(message) <= 200:
                        raise UnreadableTimetable(message) from None
                except (KeyError, TypeError, json.JSONDecodeError, UnicodeError):
                    pass
            if exc.code == 429:
                raise TimetableReaderUnavailable("Pembaca jadual sedang digunakan. Cuba semula sekejap lagi.") from None
        raise TimetableReaderUnavailable from None
    except (NativeRPHUnavailable, OSError, ValueError):
        raise TimetableReaderUnavailable from None
