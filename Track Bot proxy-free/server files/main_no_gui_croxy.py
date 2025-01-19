import asyncio
import sys
import json
from playwright.async_api import async_playwright
import time
import re
import random  # Import the random module

sys.stdout.reconfigure(encoding='utf-8')
MAX_RETRIES = 5  # Adjusted maximum retries

async def get_current_url_and_extract_ip(page):
    """Gets the current URL from the page and extracts the IP address."""
    current_url = page.url
    print(f"Current URL: {current_url}")

    # Regular expression to match an IP address
    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', current_url)
    if ip_match:
        ip_address = ip_match.group(1)
        print(f"Extracted IP Address: {ip_address}")
    else:
        print("No IP address found in the URL.")

async def extract_and_play_tracks(url, min_duration, max_duration, repeat_count, headless, change_ip_after, use_croxyproxy):
    """Extract and play tracks using Playwright, with retries and browser restarts as needed."""
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/91.0",
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )
        page = await context.new_page()

        for repeat_index in range(repeat_count):
            retry_count = 0  # Counter for retries
            success = 0
            # Navigate via CroxyProxy if required (only on first repeat or at change_ip_after intervals)
            if use_croxyproxy and (repeat_index == 0 or repeat_index % change_ip_after == 0):
                while True:
                    while retry_count < MAX_RETRIES:
                        try:
                            print("Navigating to CroxyProxy for proxy usage...")
                            await page.goto("https://www.croxyproxy.com/")
                            await page.wait_for_selector('#url')
                            await page.fill('#url', url)
                            await page.click('#requestSubmit')
                            await page.wait_for_load_state('load')
                            await page.wait_for_load_state('networkidle')
                            await asyncio.sleep(10)
                            await handle_cookie_popup(page)
                            await scroll_down_to_load_all_tracks(page)

                            print("Navigated to URL via CroxyProxy.")
                            success = 1
                            break
                        except:
                            retry_count += 1
                            continue
                    if success:
                        break
                    else:
                        print('Retrying in 1 minute..')
                        time.sleep(60)
                        await browser.close()
                        time.sleep(5)
                        browser = await p.firefox.launch(headless=headless)
                        context = await browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/91.0",
                            viewport={"width": 1280, "height": 720},
                            locale="en-US"
                        )
                        page = await context.new_page()
                        continue

            try:
                print(f"Repeat: {repeat_index + 1}", flush=True)
                await page.wait_for_selector('.list-cards .list-item', timeout=30000)
                tracks = await page.query_selector_all('.list-cards .list-item')
                track_data = []
                unique_track_names = set()

                for track in tracks:
                    name_element = await track.query_selector('.item-title .name')
                    track_name = await name_element.inner_text() if name_element else "Unknown Track"
                    track_name = track_name.strip()
                    if track_name not in unique_track_names:
                        unique_track_names.add(track_name)
                        track_data.append((track, track_name))

                for index, (track, track_name) in enumerate(track_data):
                    safe_track_name = track_name.encode('utf-8', errors='replace').decode('utf-8')
                    print(f"Playing track {index + 1}: {safe_track_name}", flush=True)
                    play_button = await track.query_selector('button.btn-play.no-scale.vb-list-view-play-button-cards')
                    if play_button:
                        await play_button.click()
                        for _ in range(3):
                            player_title_element = await page.query_selector('.player-content .playable-information .title .caption')
                            current_playing_title = await player_title_element.inner_text() if player_title_element else None
                            if current_playing_title == track_name:
                                print(f"Successfully playing: {current_playing_title}", flush=True)
                                # Generate a random wait time between min_duration and max_duration
                                random_wait_time = random.randint(min_duration, max_duration)
                                print(f'Playing track for {random_wait_time} seconds..')
                                await asyncio.sleep(random_wait_time)
                                break
                            else:
                                print(f"Incorrect track playing: {current_playing_title}. Retrying...", flush=True)
                                await play_button.click()
                                await asyncio.sleep(random.randint(min_duration, max_duration))  # Random wait time for retry
            except Exception as e:
                retry_count += 1
                print(f"Error during repeat {repeat_index + 1}, attempt {retry_count}/{MAX_RETRIES}: {e}", flush=True)
                if retry_count == MAX_RETRIES:
                    print("Max retries reached for this repeat.", flush=True)

            # Close and reopen the browser if change_ip_after interval is reached
            if use_croxyproxy and repeat_index > 0 and (repeat_index + 1) % change_ip_after == 0:
                print("Reaching change_ip_after interval. Restarting browser...", flush=True)
                await browser.close()
                browser = await p.firefox.launch(headless=headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/91.0",
                    viewport={"width": 1280, "height": 720},
                    locale="en-US"
                )
                page = await context.new_page()

async def scroll_down_to_load_all_tracks(page):
    """Scroll down the page to load all tracks."""
    try:
        for _ in range(5):  # Adjust the range to control the number of scrolls
            await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
            await asyncio.sleep(5)
        print("Scrolling completed to load all tracks.", flush=True)
        await get_current_url_and_extract_ip(page)
    except Exception as e:
        print(f"Error during scrolling: {e}", flush=True)

async def handle_cookie_popup(page):
    """Handle any cookie popups on the page."""
    try:
        await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=30000)
        await page.click('#onetrust-accept-btn-handler')
        print("Cookie popup handled.", flush=True)
    except Exception as e:
        print(f"No cookie popup found or could not be handled: {e}", flush=True)

def main():
    config_file_path = "/home/music_plays_bot/config_crox.json"
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
            url = config.get("url")
            min_duration = config.get("min_duration", 1)
            max_duration = config.get("max_duration", 10)
            repeat_count = config.get("repeat_count", 1)
            headless = config.get("headless", True)
            change_ip_after = config.get("ip_change_interval", 1)
            use_croxyproxy = config.get("use_proxy", True)

    except FileNotFoundError:
        print(f"Config file not found at {config_file_path}. Please ensure it exists.", flush=True)
        return
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {config_file_path}. Please check the file format.", flush=True)
        return

    asyncio.run(extract_and_play_tracks(url, min_duration, max_duration, repeat_count, headless, change_ip_after, use_croxyproxy))

if __name__ == "__main__":
    main()
