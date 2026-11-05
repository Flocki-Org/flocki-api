from datetime import datetime

from src.app.utils.DateUtils import DateUtils


def test_get_current_datetime_returns_datetime_instance():
    result = DateUtils.get_current_datetime()
    assert isinstance(result, datetime)


def test_get_current_datetime_is_close_to_now():
    before = datetime.now()
    result = DateUtils.get_current_datetime()
    after = datetime.now()
    assert before <= result <= after
