# Source Research

## Source Status Summary

| Source | Status | Use In Phase 1 | Notes |
| --- | --- | --- | --- |
| OpenStreetMap / Overpass | Automated | Yes | Good for cafe POIs, names, coordinates, addresses, websites, phones, and opening-hours tags. Weak for work-friendly details. |
| Google Places API | Optional automated | Yes if API key is available | Strong for place IDs, addresses, coordinates, hours, ratings, price level, and website URI. Requires key/billing and field masks. |
| Public blogs/articles | Semi-automated/manual | Yes | Good for work-friendly claims such as unlimited time, outlets, Wi-Fi, quietness, and minimum order. Use links and manual review. |
| Dcard public posts | Manual/semi-automated | Yes with caution | Useful user-generated evidence. Treat as manual review source; avoid aggressive scraping. |
| PTT public posts | Semi-automated/manual | Yes with caution | Static pages are accessible; many posts are old. Use source date and low confidence for stale records. |
| Catcha Cafes | Manual/reference | Yes as source discovery | Public site is directly relevant and has work-friendly tags. Do not bulk-copy its dataset; use as competitor/source reference unless permission is obtained. |
| Instagram public pages/posts | Manual/optional | Not automated in Phase 1 | Do not bypass login or anti-bot protections. Prefer official cafe profile URLs submitted manually. |
| Threads public posts | Manual/optional | Not automated in Phase 1 | Do not use unofficial APIs or scrape blocked content. Track useful public URLs manually. |
| Official cafe websites/social pages | Manual/API-assisted | Yes | Best for authoritative hours, rules, and social links when available. |
| Travel/listing sites | Manual/semi-automated | Yes with caution | Useful discovery sources, but usually weaker for work-friendly attributes unless explicitly stated. |

## Researched Public Sources

### OpenStreetMap / Overpass

Useful fields:

- `amenity=cafe`
- `name`
- `addr:*`
- `opening_hours`
- `website` / `contact:website`
- `phone` / `contact:phone`
- `internet_access`
- `outdoor_seating`

Automation status: automated collector implemented in `scripts/collectors/collect_overpass.py`.

### Google Places API

Useful fields:

- `id`
- `displayName`
- `formattedAddress`
- `location`
- `types`
- `googleMapsUri`
- `websiteUri`
- `regularOpeningHours`
- `priceLevel`
- `rating`
- `userRatingCount`

Automation status: optional collector implemented in `scripts/collectors/collect_google_places.py`. It requires `GOOGLE_MAPS_API_KEY`.

### Blogs And Articles

High-value Chinese search terms:

- `不限時咖啡廳`
- `插座咖啡廳`
- `讀書咖啡廳`
- `工作咖啡廳`
- `適合辦公 咖啡廳`
- `有 wifi 插座 咖啡廳`
- `數位遊牧 咖啡廳 台北`

Seed source examples:

- `https://catcha-cafes.com/`
- `https://dryad.tw/socketcafe/`
- `https://www.georgeleelife.com/recommended-cafes-in-taipei-for-digital-nomads-daan-district`
- `https://www.dcard.tw/f/food/p/241838488`
- `https://www.ptt.cc/bbs/Food/M.1673532797.A.5FA.html`
- `https://www.ptt.cc/bbs/Food/M.1458021159.A.8BA.html`

Automation status: source queue tooling only. Full article extraction remains manual/semi-automated to avoid copyright, platform, and data-quality issues.

### Dcard, PTT, Forums

Use only public, accessible pages. Do not log in, bypass age gates, solve CAPTCHAs, or use hidden/private APIs. Forum and social posts should normally be treated as human-review evidence, not authoritative current truth.

### Instagram And Threads

For Phase 1, Instagram and Threads are not scraped. Accepted use:

- manually entered public cafe profile/post URLs
- official cafe links from OSM, Google Places, cafe websites, or blog posts
- optional future API path if official permissions are granted

Rejected use:

- login-required scraping
- unofficial API scraping
- proxy-based scraping
- CAPTCHA/anti-bot bypass
- downloading private or protected content

## Coverage Limitations

- Work-friendly attributes are often not present in structured POI APIs.
- Many blog/forum posts become stale quickly because store rules, outlets, Wi-Fi, and opening hours change.
- Chain cafes require branch-level records; franchise-level claims are not enough.
- "Unlimited time" can be conditional by weekday, crowding, branch, or minimum spend.
- Quietness and meeting suitability are subjective and should be stored with source confidence.

## Phase 1 Coverage Snapshot

Generated on 2026-06-01:

- Overpass Taipei sample: 2,388 raw cafe POIs collected and normalized.
- Manual curated seed: 8 records from public Dcard/PTT-style sources.
- Manual source discovery queue: 11 search rows across Taipei, New Taipei, Taichung, Tainan, Kaohsiung, Dcard, PTT, Instagram, and Threads.
- Google Places: collector implemented, dry-run verified, live collection blocked until `GOOGLE_MAPS_API_KEY` is configured.
- Instagram/Threads: documented as manual/optional only; no automated scraper implemented.
