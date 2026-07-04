# tests/test_attachments.py
"""Download-response hardening — filename sanitisation for Content-Disposition.

User-uploaded filenames flow into the `Content-Disposition` header; a name with
quotes or CR/LF could corrupt the header or enable response splitting. These
tests pin the sanitiser and the forced-download behaviour shared by the
resources / assignments / messaging download endpoints.
"""

from gateway.http.attachments import attachment_response, safe_filename


def test_safe_filename_strips_quotes_and_control_chars():
    assert safe_filename('a"b.pdf') == "a_b.pdf"
    assert safe_filename("evil\r\nSet-Cookie: x=1") == "evil__Set-Cookie: x=1"
    assert safe_filename("back\\slash.txt") == "back_slash.txt"


def test_safe_filename_defaults_when_empty_or_dotty():
    assert safe_filename(None) == "download"
    assert safe_filename("") == "download"
    assert safe_filename("...") == "download"


def test_safe_filename_keeps_ordinary_names():
    assert safe_filename("Week 1 - notes.pdf") == "Week 1 - notes.pdf"


def test_attachment_response_is_forced_download_with_clean_header():
    r = attachment_response(b"data", "text/html", 'x".html\r\n')
    cd = r.headers["content-disposition"]
    assert cd.startswith("attachment")
    assert "\r" not in cd and "\n" not in cd
    # the injected quote is neutralised
    assert cd == 'attachment; filename="x_.html"'


def test_attachment_response_defaults_media_type():
    r = attachment_response(b"data", None, "f.bin")
    assert r.media_type == "application/octet-stream"
