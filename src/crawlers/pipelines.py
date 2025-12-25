# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import hashlib
import pathlib
from urllib.parse import urlparse
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import Request
from PIL import Image
import os


class CleaningCrawlerPipeline:
    """Basic pipeline for processing items."""
    def process_item(self, item, spider):
        return item


class CleaningImagesPipeline(ImagesPipeline):
    """
    Custom image pipeline that downloads images and organizes them by domain/page_id.
    
    Features:
    - Downloads images from URLs in item['image_urls']
    - Organizes images by domain and page_id for traceability
    - Extracts metadata: width, height, file_size
    - Handles download failures gracefully
    """

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        Generate file path for downloaded image.
        
        Format: images/{domain}/{page_id}/{image_hash}.jpg
        
        Args:
            request: The image request
            response: The image response (if available)
            info: Scrapy info object
            item: The item being processed
            
        Returns:
            Relative path for the image file
        """
        # Get image URL
        image_url = request.url

        # Extract domain from item URL
        if item and 'url' in item:
            page_url = item['url']
            parsed = urlparse(page_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '_')
        else:
            # Fallback: extract from image URL
            parsed = urlparse(image_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '_')

        # Generate page_id from page URL hash
        if item and 'url' in item:
            page_id = hashlib.md5(item['url'].encode(), usedforsecurity=False).hexdigest()[:8]
        else:
            page_id = 'unknown'

        # Generate image hash from URL
        image_hash = hashlib.sha1(image_url.encode(), usedforsecurity=False).hexdigest()[:16]

        # Determine file extension from URL or content type
        ext = 'jpg'  # default
        if response:
            content_type = response.headers.get('Content-Type', b'').decode().lower()
            if 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            elif 'gif' in content_type:
                ext = 'gif'
        else:
            # Try to get from URL
            url_lower = image_url.lower()
            if url_lower.endswith('.png'):
                ext = 'png'
            elif url_lower.endswith('.webp'):
                ext = 'webp'
            elif url_lower.endswith('.gif'):
                ext = 'gif'

        # Return path: images/{domain}/{page_id}/{hash}.{ext}
        return f"images/{domain}/{page_id}/{image_hash}.{ext}"

    def get_media_requests(self, item, info):
        """
        Generate requests for images to download.
        
        Args:
            item: The item containing image_urls
            info: Scrapy info object
            
        Returns:
            List of Request objects for images
        """
        adapter = ItemAdapter(item)
        image_urls = adapter.get('image_urls', [])

        # Limit number of images per page (from config if available)
        max_images = getattr(info.spider, 'max_images_per_page', 20)
        if len(image_urls) > max_images:
            image_urls = image_urls[:max_images]
            info.spider.logger.info(f"Limited images to {max_images} for {item.get('url', 'unknown')}")

        for image_url in image_urls:
            yield Request(image_url)

    def item_completed(self, results, item, info):
        """
        Process completed image downloads and add metadata.
        
        Args:
            results: List of (success, image_info_or_failure) tuples
            item: The item being processed
            info: Scrapy info object
            
        Returns:
            Item with image metadata added
        """
        adapter = ItemAdapter(item)

        # Process results from image downloads
        image_results = []
        for success, result in results:
            if success:
                # Image downloaded successfully
                # result is a dict with image info
                image_info = {
                    'url': result.get('url', ''),
                    'path': result.get('path', ''),
                    'checksum': result.get('checksum', ''),
                }

                # Try to extract dimensions and file size from downloaded file
                try:
                    image_path = pathlib.Path(info.spider.settings.get(
                        'IMAGES_STORE', 'data/images')) / image_info['path']
                    if image_path.exists():
                        # Get file size
                        image_info['file_size'] = image_path.stat().st_size

                        # Get dimensions using PIL
                        try:
                            with Image.open(image_path) as img:
                                image_info['width'] = img.width
                                image_info['height'] = img.height
                        except Exception as e:
                            info.spider.logger.warning(f"Could not read image dimensions for {image_info['path']}: {e}")
                            image_info['width'] = None
                            image_info['height'] = None
                    else:
                        image_info['file_size'] = None
                        image_info['width'] = None
                        image_info['height'] = None
                except Exception as e:
                    info.spider.logger.warning(f"Could not extract metadata for {image_info['path']}: {e}")
                    image_info['file_size'] = None
                    image_info['width'] = None
                    image_info['height'] = None

                image_results.append(image_info)
            else:
                # Image download failed
                # result is a Twisted Failure object, not a dict
                from twisted.python.failure import Failure

                if isinstance(result, Failure):
                    # Extract error information from Failure object
                    error_msg = str(result.value) if result.value else str(result)
                    error_type = type(result.value).__name__ if result.value else 'UnknownError'

                    # Try to get URL from the request if available
                    url = 'unknown'
                    if hasattr(result, 'request') and result.request:
                        url = result.request.url
                    elif hasattr(result, 'value') and hasattr(result.value, 'request'):
                        url = result.value.request.url if result.value.request else 'unknown'

                    info.spider.logger.warning(
                        f"Image download failed for {url}: {error_type}: {error_msg}"
                    )

                    # Add failure info to item (optional - you can skip this if you don't want failed images)
                    image_results.append({
                        'url': url,
                        'error': f"{error_type}: {error_msg}",
                        'path': None,
                    })
                else:
                    # Fallback for unexpected failure types
                    info.spider.logger.warning(
                        f"Image download failed with unknown error type: {type(result)}"
                    )
                    image_results.append({
                        'url': 'unknown',
                        'error': str(result),
                        'path': None,
                    })

        # Add processed image results to item
        adapter['images'] = image_results

        return item
