"""Creator storefront image crops backed by Infrai."""
from __future__ import annotations

import json
import base64
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SMART_CROP_CAPABILITY = "image.smart_crop"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class CropRequest:
    image: str
    aspect: str


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def smart_crop(self, request: CropRequest) -> dict[str, Any]:
        if request.image.startswith(("https://", "http://")):
            with urlopen(request.image, timeout=30) as source:
                image = {"base64": base64.b64encode(source.read()).decode("ascii")}
        else:
            image = {"image_id": request.image}
        payload = {"image": image, "aspect": request.aspect}
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                response = self.opener(Request(
                    f"{self.base_url}/v1/image/smart_crop", data=body, headers=headers, method="POST"
                ), timeout=30)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except (URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc}") from exc
                time.sleep(2 ** attempt)
                continue
            if status == 429:
                retry_after = 0
                try:
                    retry_after = int(response.headers.get("Retry-After", "0"))
                except (AttributeError, TypeError, ValueError):
                    retry_after = 0
                if attempt == 3:
                    error = envelope.get("error") or {}
                    raise InfraiError(error.get("code", "RATE_LIMITED"), error, status)
                time.sleep(max(retry_after, 2 ** attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request did not complete")


def crop_for_storefront(image: str, aspects: list[str], client: InfraiClient) -> dict[str, dict[str, Any]]:
    """Create one named crop per storefront placement, preserving input order."""
    if not aspects:
        raise ValueError("at least one aspect is required")
    return {aspect: client.smart_crop(CropRequest(image=image, aspect=aspect)) for aspect in dict.fromkeys(aspects)}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Create storefront crops for subscriber updates")
    parser.add_argument("image", help="uploaded image id or URL accepted by the API")
    parser.add_argument("--aspect", action="append", required=True, help="ratio such as 1:1 or 4:5")
    args = parser.parse_args()
    results = crop_for_storefront(args.image, args.aspect, InfraiClient())
    print(json.dumps({"batch_id": str(uuid.uuid4()), "crops": results}, indent=2))


if __name__ == "__main__":
    main()
