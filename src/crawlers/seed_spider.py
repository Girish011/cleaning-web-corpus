import pathlib
import scrapy


class SeedSpider(scrapy.Spider):
    name = "seed_spider"
    source = "seed_spider"  # label for this crawler

    def start_requests(self):
        # Path to seeds.txt relative to project root
        root = pathlib.Path(__file__).resolve().parents[2]  # Updated: 2 levels up (was 3)
        seeds_file = root / "data" / "seeds.txt"  # Updated: new location

        with seeds_file.open() as f:
            for line in f:
                url = line.strip()
                if not url:
                    continue
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        title = response.xpath("//title/text()").get() or ""
        
        images = response.css("img")
        image_urls = []
        image_details = []
        for idx, img in enumerate(images):
            src = img.attrib.get("src")
            if not src:
                continue
            full_url = response.urljoin(src)
            alt = img.attrib.get("alt", "").strip()
            image_urls.append(full_url)
            image_details.append({
                "url": full_url,
                "alt": alt,
                "position": idx,
        })

        videos = response.css("video")
        video_urls = []
        video_metadata = []
        for idx, video in enumerate(videos):
            src = video.attrib.get("src")
            if not src:
                # Some sites use <source> children
                src = video.css("source::attr(src)").get()
            if not src:
                continue
            full_url = response.urljoin(src)
            video_urls.append(full_url)
            video_metadata.append({
                "url": full_url,
                "position": idx,
        })
        
        yield {
            "url": response.url,
            "title": title.strip(),
            "status": response.status,
            "source": self.source,
            "image_urls": image_urls,
            "video_urls": video_urls,
            "image_details": image_details,
            "video_metadata": video_metadata,
        }
