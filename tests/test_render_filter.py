"""Filter-path escaping: pure string tests, no ffmpeg.

The expected literals below were verified against a live ffmpeg 6.1 run:
subtitles=filename=<escaped> parsed and rendered a path containing an
apostrophe, a comma, and a colon.
"""

from speko_captions.render import escape_filter_path


def test_apostrophe_comma_colon_two_level_escape():
    out = escape_filter_path("/tmp/o'brien/clip, final:v2.ass")
    assert out == "/tmp/o\\\\\\'brien/clip\\, final\\\\:v2.ass"


def test_plain_path_survives():
    assert escape_filter_path("/tmp/plain/file.ass") == "/tmp/plain/file.ass"
