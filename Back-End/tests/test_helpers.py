from app.utils.helpers import (
    normalize,
    extract_duration_minutes
)


def test_normalize():

    assert normalize(" Python Developer ") == (
        "python developer"
    )


def test_normalize_empty():

    assert normalize("") == ""


def test_extract_duration_minutes():

    assert (
        extract_duration_minutes("45 minutes")
        == 45
    )


def test_extract_duration_invalid():

    assert (
        extract_duration_minutes("unknown")
        == 0
    )