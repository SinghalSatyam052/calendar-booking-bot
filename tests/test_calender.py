import os, datetime as dt
from app.calendar_client import is_free

ISO = "%Y-%m-%dT%H:%M:%S+05:30"  # adjust for IST

def test_is_free_future():
    start = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)).strftime(ISO)
    end = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2, minutes=30)).strftime(ISO)
    assert isinstance(is_free(start, end), bool)