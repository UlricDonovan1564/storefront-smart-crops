import json
from unittest.mock import patch
from io import BytesIO

from src.smart_crop_service import CropRequest, InfraiClient, crop_for_storefront


class FakeResponse:
    status = 200

    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def read(self):
        return self.data


def test_storefront_crops_deduplicate_aspects_and_keep_results():
    calls = []

    def opener(request, timeout):
        calls.append(json.loads(request.data))
        return FakeResponse({"ok": True, "data": {"url": f"cdn/{len(calls)}"}, "error": None, "metadata": {}})

    client = InfraiClient(api_key="test-key", opener=opener)
    result = crop_for_storefront("upload-123", ["1:1", "4:5", "1:1"], client)
    assert list(result) == ["1:1", "4:5"]
    assert result["4:5"]["url"] == "cdn/2"
    assert calls == [
        {"image": {"image_id": "upload-123"}, "aspect": "1:1"},
        {"image": {"image_id": "upload-123"}, "aspect": "4:5"},
    ]


def test_url_image_is_sent_as_url_reference():
    calls = []

    def opener(request, timeout):
        calls.append(json.loads(request.data))
        return FakeResponse({"ok": True, "data": {}, "error": None, "metadata": {}})

    with patch("src.smart_crop_service.urlopen", return_value=BytesIO(b"photo")) as fetch:
        InfraiClient(api_key="test-key", opener=opener).smart_crop(
            CropRequest("https://example.com/photo.jpg", "1:1")
        )
    fetch.assert_called_once_with("https://example.com/photo.jpg", timeout=30)
    assert calls == [{"image": {"base64": "cGhvdG8="}, "aspect": "1:1"}]
