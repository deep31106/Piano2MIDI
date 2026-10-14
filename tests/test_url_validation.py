
import pytest

from piano2midi.cli import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=example123",
        "https://youtu.be/example123",
        "https://www.instagram.com/p/example123/",
        "https://www.instagram.com/reel/example123/",
    ],
)
def test_validate_url_accepts_supported_https_urls(url):
    validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.youtube.com/watch?v=example123",
        "https://example.com/video",
        "https://www.youtube.com.example.com/watch?v=example123",
        "https://evilinstagram.com/p/example123/",
    ],
)
def test_validate_url_rejects_unsupported_urls(url):
    with pytest.raises(ValueError, match="Unsupported URL"):
        validate_url(url)
