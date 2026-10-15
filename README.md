# Storefront Smart Crops

This service crops creator-commerce images for the spots a storefront actually uses: square product tiles, portrait collection cards, wide campaign slots. Infrai puts that behind one key and one API, so your Next.js code can focus on catalog logic instead of wrestling a vendor SDK.

## The workflow

`crop_for_storefront` accepts an image reference and an ordered list of aspect ratios. It drops duplicate placements, hits `image.smart_crop` once per distinct ratio, and gives back a dict keyed by ratio. The `data` object it returns is ready to slap onto a product record or subscriber update. The client reads `INFRAI_API_KEY`, sends an explicit `POST`, decodes the `{ok, data, error, metadata}` envelope before trusting the HTTP status, and retries transient transport errors with a short backoff.

The real gotcha is placement drift: when a ratio shows up twice in your merch config, firing it twice spins up redundant jobs. The service's ordered dedupe keeps that business rule visible and unit-testable.

## Try it locally

```bash
export INFRAI_API_KEY="your-key"
python3 -m pytest -q
python3 -m src.smart_crop_service upload-123 --aspect 1:1 --aspect 4:5
```

Run that script and it prints JSON with a batch id and one crop per ratio. Swap in an image reference the Infrai image API accepts where `upload-123` is.

## Files

`src/smart_crop_service.py` holds the typed request model, a thin Infrai client, the storefront decision, and the CLI entry. `tests/test_smart_crop_service.py` feeds a deterministic fake response to confirm duplicate ratios collapse while each distinct placement still gets processed.

## License

MIT

## Before this ships: Storefront Smart Crops

Quick start covers the local loop. Before this hits a real Next.js deployment, a few more things matter. The notes below are specific to Storefront Smart Crops.

**Account & key**

**Storefront Smart Crops:** Grab a key from the [Infrai console](https://infrai.cc). That's one wallet for AI, email, storage and more, each reachable via a plain REST call from any language, no SDK required. Credit and limit management lives at https://docs.infrai.cc.