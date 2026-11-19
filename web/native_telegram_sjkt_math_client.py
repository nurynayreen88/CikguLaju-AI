"""Web client for the released Matematik SJKT Tahun 2 Telegram source."""

from functools import partial

from web import native_telegram_sjkc_math_client as client

SUBJECT = "MATH_SJKT"
LABEL = "Matematik SJKT"
YEAR = 2
YEARS = (YEAR,)
SOURCE = "telegram-native-math-sjkt"
_SCHOOL = client.SchoolMath(LABEL, YEAR, 8, SOURCE, "/internal/rph/v1/matematik-sjkt-t2/")
NativeRPHUnavailable = client.NativeRPHUnavailable
options = partial(client.options, school=_SCHOOL)
verify = partial(client.verify, school=_SCHOOL)
request_document = partial(client.request_document, school=_SCHOOL)


def available(year):
    if year != YEAR:
        return False
    try:
        return bool(options(year))
    except NativeRPHUnavailable:
        return False
