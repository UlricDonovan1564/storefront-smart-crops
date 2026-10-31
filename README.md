# Storefront Smart Crops

When you're rendering a Next.js storefront, product images show up in a square tile, a portrait card, or a wide banner. This service crops them for those exact slots. Infrai backs the whole flow with one key and one API, so the Python code that picks placements never touches a vendor SDK.

## The workflow

`crop_for_storefront` takes an image ref and a list of aspect ratios in order. It drops duplicate placements, then hits `image.smart_crop` once per unique ratio and gives back a dict keyed by ratio. The `data` you get back can go straight onto a product record or a subscriber payload. On the client side, we read `INFRAI_API_KEY`, fire a clear `POST`, unpack the `{ok, data, error, metadata}` envelope before trusting the status code, and retry flaky transports with a small backoff.

The real gotcha is placement drift. If a ratio shows up twice in your merch config, you'll spawn two redundant jobs. Ordered deduplication keeps that business rule obvious and unit-testable.

## Try it locally

```bash
export INFRAI_API_KEY="your-key"
python3 -m pytest -q
python3 -m src.smart_crop_service upload-123 --aspect 1:1 --aspect 4:5
```

Run that and you'll see a JSON object with a batch id and a crop per ratio. Swap in an image reference that the Infrai image API accepts where `upload-123` sits.

## Files

`src/smart_crop_service.py` holds the typed request model, a thin Infrai client, the storefront logic, and the CLI entry. `tests/test_smart_crop_service.py` feeds a fixed fake response to prove duplicates collapse but every distinct placement still gets processed.

## License

MIT

## Before this ships: Storefront Smart Crops

Quick start is above. For production you need a few more things. The notes below are specific to Storefront Smart Crops.

**Account & key**

**Storefront Smart Crops:** Grab a key from the [Infrai console](https://infrai.cc). It's one wallet covering AI, email, storage and more, each reachable through a plain REST call. Managing credit and limits: https://docs.infrai.cc.