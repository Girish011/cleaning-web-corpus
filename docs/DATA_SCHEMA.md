# Data Schema Documentation

## Raw Data Schema (from Crawler)

After Phase 2 implementation, the raw crawled data has the following structure:

```json
{
  "url": "https://example.com/how-to-clean-pillows",
  "title": "How to Clean Pillows - Complete Guide",
  "status": 200,
  "source": "seed_spider",
  "image_urls": [
    "https://example.com/images/pillow-before.jpg",
    "https://example.com/images/pillow-after.jpg"
  ],
  "video_urls": [
    "https://example.com/videos/cleaning-demo.mp4"
  ],
  "image_details": [
    {
      "url": "https://example.com/images/pillow-before.jpg",
      "alt": "Dusty pillow before cleaning",
      "position": 0
    }
  ],
  "video_metadata": [
    {
      "url": "https://example.com/videos/cleaning-demo.mp4",
      "position": 0
    }
  ],
  "images": [
    {
      "url": "https://example.com/images/pillow-before.jpg",
      "path": "images/example_com/abc12345/def67890.jpg",
      "checksum": "abc123def456...",
      "width": 800,
      "height": 600,
      "file_size": 125000
    },
    {
      "url": "https://example.com/images/pillow-after.jpg",
      "path": "images/example_com/abc12345/ghi11111.jpg",
      "checksum": "xyz789uvw012...",
      "width": 800,
      "height": 600,
      "file_size": 118000
    }
  ]
}
```

## Field Descriptions

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | The URL of the crawled page |
| `title` | string | Page title extracted from `<title>` tag |
| `status` | integer | HTTP status code (200, 404, etc.) |
| `source` | string | Source identifier (e.g., "seed_spider") |
| `image_urls` | array[string] | List of image URLs found on the page |
| `video_urls` | array[string] | List of video URLs found on the page |
| `image_details` | array[object] | Metadata about images (alt text, position) |
| `video_metadata` | array[object] | Metadata about videos (position) |
| `images` | array[object] | **NEW**: Downloaded image information with metadata |

### Image Object Fields

The `images` array contains objects with the following fields (added by `CleaningImagesPipeline`):

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Original image URL |
| `path` | string | Relative path to downloaded image file |
| `checksum` | string | SHA1 hash of the image file |
| `width` | integer\|null | Image width in pixels (extracted from file) |
| `height` | integer\|null | Image height in pixels (extracted from file) |
| `file_size` | integer\|null | File size in bytes |

**Note**: If image download fails, the object may contain an `error` field instead of `path`, `width`, `height`, etc.

## Image Storage Structure

Images are organized in the following directory structure:

```
data/images/
├── example_com/          # Domain (dots replaced with underscores)
│   ├── abc12345/         # Page ID (hash of page URL)
│   │   ├── def67890.jpg  # Image hash + extension
│   │   └── ghi11111.jpg
│   └── xyz99999/         # Another page from same domain
│       └── mno22222.png
└── another_domain_com/
    └── ...
```

### Path Format

```
images/{domain}/{page_id}/{image_hash}.{ext}
```

Where:
- `{domain}`: Domain name with dots replaced by underscores (e.g., `example_com`)
- `{page_id}`: First 8 characters of MD5 hash of page URL
- `{image_hash}`: First 16 characters of SHA1 hash of image URL
- `{ext}`: File extension (jpg, png, webp, gif)

## Processed Data Schema

After processing through `text_processor.py`, the data includes additional fields:

```json
{
  "url": "https://example.com/how-to-clean-pillows",
  "title": "How to Clean Pillows - Complete Guide",
  "source_type": "pillows_bedding",
  "raw_html": "<html>...</html>",
  "main_text": "Extracted article text...",
  "language": "en",
  "fetched_at": "2024-01-15T10:30:00Z",
  "http_status": 200,
  "surface_type": "pillows_bedding",
  "dirt_type": "dust",
  "cleaning_method": "vacuum",
  "image_urls": [...],
  "video_urls": [...],
  "image_details": [...],
  "video_metadata": [...],
  "images": [...]  # Downloaded image metadata
}
```

## Image Download Behavior

### Success Case
- Image is downloaded to `data/images/{domain}/{page_id}/{hash}.{ext}`
- Metadata (width, height, file_size) is extracted
- Image info is added to `item['images']`

### Failure Case
- Download failure is logged
- Error information is added to `item['images']` with `error` field
- Item processing continues (does not fail)

### Filtering
- Images smaller than `IMAGES_MIN_WIDTH` x `IMAGES_MIN_HEIGHT` are rejected
- Maximum `max_images_per_page` images are downloaded per page
- Images are validated for format compatibility

## Configuration

Image download behavior is controlled by settings in `configs/default.yaml`:

```yaml
crawler:
  download_images: true
  max_images_per_page: 20
  images_store: "data/images"
  images_expires_days: 90
  images_min_height: 110
  images_min_width: 110
```

These settings are also available in Scrapy settings (`src/crawlers/settings.py`):
- `IMAGES_STORE`
- `IMAGES_EXPIRES`
- `IMAGES_MIN_HEIGHT`
- `IMAGES_MIN_WIDTH`
- `IMAGES_URLS_FIELD`
- `IMAGES_RESULT_FIELD`
