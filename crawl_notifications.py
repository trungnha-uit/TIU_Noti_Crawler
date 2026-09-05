import os
import re
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from supabase import create_client, Client

class PortalCrawler:
    def __init__(self):
        # Get base URLs from environment (required)
        self.portal_base = os.getenv('PORTAL_BASE_URL')
        self.ctsv_base = os.getenv('CTSV_BASE_URL')
        self.khtc_base = os.getenv('KHTC_BASE_URL')

        if not self.portal_base or not self.ctsv_base or not self.khtc_base:
            raise ValueError("Missing required environment variables: PORTAL_BASE_URL, CTSV_BASE_URL, KHTC_BASE_URL")

        self.portal_url = f"{self.portal_base}/bai-viet"
        self.ctsv_url = f"{self.ctsv_base}/thong-bao"
        self.khtc_url = f"{self.khtc_base}/thongbao"

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Categories to exclude
        self.excluded_categories = [
            "Liên thông CQ",
            "Thông báo Nghỉ - Bù",
            "Thông báo nghỉ - bù"
        ]

        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if supabase_url and supabase_key:
            self.supabase: Optional[Client] = create_client(supabase_url, supabase_key)
        else:
            self.supabase = None
            print("Warning: Supabase credentials not found. Will skip database operations.")

    def sanitize_text(self, text: str) -> str:
        """Remove personal and school-specific information"""
        if not text:
            return text

        # Remove student IDs (8 digits)
        text = re.sub(r'\b\d{8}\b', '[ID]', text)

        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

        # Remove phone numbers
        text = re.sub(r'\b0\d{9,10}\b', '[PHONE]', text)
        text = re.sub(r'\(0\d{2,3}\)\s*\d{3}\s*\d{4}', '[PHONE]', text)

        return text

    def should_include_notification(self, categories: List[str]) -> bool:
        """Check if notification should be included based on categories"""
        for cat in categories:
            if cat in self.excluded_categories:
                return False
        return True

    def crawl_portal(self, page: int = 1) -> List[Dict]:
        """Crawl notifications from url/bai-viet"""
        try:
            url = self.portal_url
            if page > 1:
                url += f"?page={page}"

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            notifications = []

            # Find all article cards
            articles = soup.find_all('a', class_=lambda x: x and 'group' in x and 'flex' in x and 'flex-col' in x)

            for article in articles:
                try:
                    # Get title
                    title_elem = article.find('h3')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # Get link
                    link = article.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"{self.portal_base}{link}"

                    # Get date
                    date = ''
                    all_p = article.find_all('p', class_='mt-3 text-xs text-muted-foreground')
                    if all_p:
                        date = all_p[-1].get_text(strip=True)

                    # Get categories
                    categories = []
                    category_spans = article.find_all('span', class_=lambda x: x and 'rounded-full' in x and 'border' in x)
                    for span in category_spans:
                        cat_text = span.get_text(strip=True)
                        if cat_text and cat_text != 'Nổi bật':
                            categories.append(cat_text)

                    # Check if should include based on categories
                    if not self.should_include_notification(categories):
                        continue

                    # Check if featured
                    featured_badge = article.find('span', class_=lambda x: x and 'bg-warning' in x)
                    is_featured = featured_badge is not None

                    notifications.append({
                        'title': self.sanitize_text(title),
                        'link': link,
                        'date': date,
                        'categories': categories,
                        'featured': is_featured,
                        'source': self.portal_base,
                        'crawled_at': datetime.now(timezone(timedelta(hours=7))).isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue

            return notifications

        except Exception as e:
            print(f"Error getting notifications from url: {e}")
            return []

    def crawl_ctsv(self, page: int = 0) -> List[Dict]:
        """Crawl notifications from url/thong-bao"""
        try:
            url = self.ctsv_url
            if page > 0:
                url += f"?page={page}"

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            notifications = []

            # Find all article elements
            articles = soup.find_all('article', class_='node-baiviet')

            for article in articles:
                try:
                    # Get title
                    title_elem = article.find('h2')
                    if not title_elem:
                        continue

                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"{self.ctsv_base}{link}"

                    # Get date from submitted section
                    date = ''
                    date_elem = article.find('span', property='dc:date dc:created')
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        # Extract date from format "Mon, 26/08/2026 - 09:51"
                        parts = date_text.split(',')
                        if len(parts) > 1:
                            date_parts = parts[1].strip().split(' - ')
                            if date_parts:
                                date = date_parts[0].strip()

                    # Check if sticky (featured)
                    is_featured = 'node-sticky' in article.get('class', [])

                    # CTSV doesn't have category tags in the list view, but we can infer from content
                    categories = []

                    notifications.append({
                        'title': self.sanitize_text(title),
                        'link': link,
                        'date': date,
                        'categories': categories,
                        'featured': is_featured,
                        'source': self.ctsv_base,
                        'crawled_at': datetime.now(timezone(timedelta(hours=7))).isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing CTSV article: {e}")
                    continue

            return notifications

        except Exception as e:
            print(f"Error getting notifications from url: {e}")
            return []

    def crawl_khtc(self, page: int = 0) -> List[Dict]:
        """Crawl notifications from url/thongbao"""
        try:
            url = self.khtc_url
            if page > 0:
                url += f"?page={page}"

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            notifications = []

            # Find all article elements
            articles = soup.find_all('article', class_='node')

            for article in articles:
                try:
                    # Get link and title - link is directly inside article
                    link_elem = article.find('a')
                    if not link_elem:
                        continue

                    # Get h2 inside the link
                    h2_elem = link_elem.find('h2')
                    if not h2_elem:
                        continue

                    title = h2_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"{self.khtc_base}{link}"

                    # Get date from submitted section
                    date = ''
                    date_elem = article.find('div', class_='submitted')
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        # Format: "T6, 14/08/2026 - 08:49"
                        parts = date_text.split(',')
                        if len(parts) > 1:
                            date_parts = parts[1].strip().split(' - ')
                            if date_parts:
                                date = date_parts[0].strip()

                    # KHTC doesn't have featured/sticky posts
                    is_featured = False

                    # No categories in KHTC list view
                    categories = []

                    notifications.append({
                        'title': self.sanitize_text(title),
                        'link': link,
                        'date': date,
                        'categories': categories,
                        'featured': is_featured,
                        'source': self.khtc_base,
                        'crawled_at': datetime.now(timezone(timedelta(hours=7))).isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing KHTC article: {e}")
                    continue

            return notifications

        except Exception as e:
            print(f"Error getting notifications from khtc.url: {e}")
            return []

    def get_notifications(self, page: int = 1) -> List[Dict]:
        """Crawl notifications from all configured sources"""
        all_notifications = []

        # Crawl portal.url
        print(f"Fetching from url (page {page})...")
        portal_notifs = self.crawl_portal(page=page)
        all_notifications.extend(portal_notifs)
        print(f"  Found {len(portal_notifs)} notifications")

        # Crawl ctsv.url (page numbering starts at 0)
        ctsv_page = page - 1 if page > 0 else 0
        print(f"Fetching from ctsv.url (page {ctsv_page})...")
        ctsv_notifs = self.crawl_ctsv(page=ctsv_page)
        all_notifications.extend(ctsv_notifs)
        print(f"  Found {len(ctsv_notifs)} notifications")

        # Crawl khtc.url (page numbering starts at 0)
        khtc_page = page - 1 if page > 0 else 0
        print(f"Fetching from khtc.url (page {khtc_page})...")
        khtc_notifs = self.crawl_khtc(page=khtc_page)
        all_notifications.extend(khtc_notifs)
        print(f"  Found {len(khtc_notifs)} notifications")

        return all_notifications

    def load_previous_notifications(self) -> List[Dict]:
        """Load previous notifications from Supabase"""
        if not self.supabase:
            print("Supabase not configured, returning empty list")
            return []

        try:
            response = self.supabase.table('notification').select('title, link').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
            return []

    def save_notifications(self, notifications: List[Dict]):
        """Save new notifications to Supabase"""
        if not self.supabase:
            print("Supabase not configured, skipping save")
            return

        if not notifications:
            return

        try:
            # Prepare data for Supabase
            records = []
            for notif in notifications:
                # Parse date string to timestamp
                date_str = notif.get('date', '')
                date_timestamp = None
                if date_str:
                    try:
                        # Parse DD/MM/YYYY format
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                        date_timestamp = date_obj.isoformat()
                    except ValueError:
                        pass

                # Convert categories list to comma-separated string
                categories_str = ','.join(notif.get('categories', []))

                records.append({
                    'title': notif['title'],
                    'link': notif['link'],
                    'date': date_timestamp,
                    'categories': categories_str,
                    'featured': notif.get('featured', False),
                    'source': notif.get('source', ''),
                    'crawled_at': notif.get('crawled_at')
                })

            # Try lowercase table name first
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                self.supabase.table('notification').insert(batch).execute()


            print(f"Saved {len(records)} notifications to Supabase")
        except Exception as e:
            print(f"Error saving to Supabase: {e}")

    def get_source_info(self, source_url: str) -> Dict[str, str]:
        """Get source identification (icon and name) with portal prioritized"""
        if self.portal_base in source_url:
            return {
                "icon": "🏛️",
                "name": "Portal",
                "color": 15844367,  # Gold/Orange for portal (highest priority)
                "priority": 1
            }
        elif self.ctsv_base in source_url:
            return {
                "icon": "👥",
                "name": "CTSV",
                "color": 5793266,  # Green
                "priority": 2
            }
        elif self.khtc_base in source_url:
            return {
                "icon": "📊",
                "name": "KHTC",
                "color": 3447003,  # Blue
                "priority": 3
            }
        else:
            return {
                "icon": "📢",
                "name": "Unknown",
                "color": 9807270,  # Gray
                "priority": 4
            }

    def send_start_notification(self, webhook_url: str, new_count: int):
        """Send start notification with count of new notifications"""
        # Vietnam timezone (UTC+7)
        vietnam_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(vietnam_tz).strftime("%d/%m/%Y %H:%M:%S")

        embed = {
            "title": "🔔 Bắt đầu kiểm tra thông báo mới",
            "description": f"**Tìm thấy: {new_count} thông báo mới**" if new_count > 0 else "Đang kiểm tra thông báo...",
            "color": 3066993,  # Dark green
            "fields": [
                {
                    "name": "⏰ Thời gian",
                    "value": current_time,
                    "inline": True
                }
            ],
            "footer": {
                "text": "Portal Notification System"
            },
            "timestamp": datetime.now(vietnam_tz).isoformat()
        }

        payload = {"embeds": [embed]}

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send start notification to Discord: {e}")

    def send_end_notification(self, webhook_url: str, new_count: int, total_checked: int):
        """Send end notification with summary"""
        # Vietnam timezone (UTC+7)
        vietnam_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(vietnam_tz).strftime("%d/%m/%Y %H:%M:%S")

        if new_count > 0:
            description = f"✅ Đã gửi **{new_count}** thông báo mới"
            color = 3066993  # Green
        else:
            description = "✅ Không có thông báo mới"
            color = 9807270  # Gray

        embed = {
            "title": "🏁 Hoàn thành kiểm tra",
            "description": description,
            "color": color,
            "fields": [
                {
                    "name": "📋 Tổng số đã kiểm tra",
                    "value": str(total_checked),
                    "inline": True
                },
                {
                    "name": "⏰ Thời gian",
                    "value": current_time,
                    "inline": True
                }
            ],
            "footer": {
                "text": "Portal Notification System"
            },
            "timestamp": datetime.now(vietnam_tz).isoformat()
        }

        payload = {"embeds": [embed]}

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send end notification to Discord: {e}")

    def send_to_discord(self, webhook_url: str, notifications: List[Dict]):
        """Send new notifications to Discord with source identification"""
        if not notifications:
            return

        # Sort notifications by priority (portal first)
        sorted_notifications = sorted(
            notifications,
            key=lambda n: (self.get_source_info(n.get('source', ''))['priority'], n.get('featured', False) == False)
        )

        for notif in sorted_notifications:
            # Get source info
            source_info = self.get_source_info(notif.get('source', ''))

            # Build category tags
            category_text = ""
            if notif.get('categories'):
                category_text = " | ".join(notif['categories'])

            # Build fields
            fields = []
            fields.append({
                "name": f"{source_info['icon']} Nguồn",
                "value": source_info['name'],
                "inline": True
            })
            if notif.get('date'):
                fields.append({
                    "name": "📅 Ngày đăng",
                    "value": notif['date'],
                    "inline": True
                })
            if category_text:
                fields.append({
                    "name": "🏷️ Danh mục",
                    "value": category_text,
                    "inline": True
                })
            if notif.get('featured'):
                fields.append({
                    "name": "⭐",
                    "value": "Bài viết nổi bật",
                    "inline": False
                })

            # Use source-specific color, or gold for featured
            embed_color = 13132095 if notif.get('featured') else source_info['color']

            embed = {
                "title": f"{source_info['icon']} {notif['title']}",
                "url": notif['link'],
                "color": embed_color,
                "fields": fields,
                "footer": {
                    "text": f"Portal Notification System • {source_info['name']}"
                },
                "timestamp": notif['crawled_at']
            }

            payload = {
                "embeds": [embed]
            }

            try:
                response = requests.post(webhook_url, json=payload)
                response.raise_for_status()
            except Exception as e:
                print(f"Failed to send to Discord: {e}")

def main():
    # Get Discord webhook from environment variable
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')

    if not discord_webhook:
        print("Missing required environment variable!")
        print("Required: DISCORD_WEBHOOK_URL")
        return

    crawler = PortalCrawler()

    # Get current notifications from all sources
    print("Fetching notifications from all sources...")
    current_notifications = crawler.get_notifications(page=1)
    print(f"\nTotal found: {len(current_notifications)} notifications")

    if not current_notifications:
        print("No notifications found. Please check the website structure.")
        return

    # Load previous notifications from Supabase
    previous_notifications = crawler.load_previous_notifications()
    previous_titles = {n['title'] for n in previous_notifications}

    # Find new notifications (not in previous list)
    new_notifications = [
        n for n in current_notifications
        if n['title'] not in previous_titles
    ]

    # Send start notification with count
    print(f"Found {len(new_notifications)} new notifications")
    crawler.send_start_notification(discord_webhook, len(new_notifications))

    if new_notifications:
        # Send to Discord
        crawler.send_to_discord(discord_webhook, new_notifications)
        print("Sent to Discord!")

        # Save only new notifications to Supabase
        crawler.save_notifications(new_notifications)
    else:
        print("No new notifications")

    # Send end notification with summary
    crawler.send_end_notification(discord_webhook, len(new_notifications), len(current_notifications))

if __name__ == "__main__":
    main()
