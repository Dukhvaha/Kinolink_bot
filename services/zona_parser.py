import asyncio
from playwright.async_api import async_playwright
from typing import Optional


class ZonaParser:
    """Парсер для zona.plus с улучшенной обработкой ошибок"""

    def __init__(self, base_url: str = "https://w140.zona.plus", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.video_urls = []

    async def search_movie(self, movie_title: str) -> Optional[str]:
        """
        Ищет фильм и возвращает прямую ссылку на видео

        Args:
            movie_title: Название фильма

        Returns:
            URL видео или None если не найдено
        """
        search_query = movie_title.replace(" ", "%20")
        search_url = f"{self.base_url}/search/{search_query}"

        print(f"🔍 Ищу: {movie_title}")
        print(f"📍 URL: {search_url}")

        self.video_urls = []

        try:
            async with async_playwright() as p:
                # Запускаем браузер
                browser = await p.chromium.launch(headless=self.headless)

                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080}
                )

                page = await context.new_page()

                # Перехватчик видео
                def handle_response(response):
                    url = response.url.lower()

                    # Ищем только .mp4 (самые надежные)
                    if '.mp4' in url:
                        if response.url not in self.video_urls:
                            self.video_urls.append(response.url)
                            print(f"✅ Найдено видео: {response.url[:80]}...")

                page.on("response", handle_response)

                # Шаг 1: Открываем поиск
                print("⏳ Загружаю страницу поиска...")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                # Шаг 2: Проверяем результаты
                try:
                    await page.wait_for_selector('.results-wrap', timeout=15000)
                except:
                    print("❌ Результаты не загрузились")
                    await browser.close()
                    return None

                results = page.locator('a.results-item')
                count = await results.count()

                if count == 0:
                    print("❌ Фильм не найден")
                    await browser.close()
                    return None

                print(f"📋 Найдено результатов: {count}")

                # Шаг 3: Кликаем на первый результат
                print("🎬 Открываю страницу фильма...")
                first_result = results.first
                await first_result.click(force=True)
                await page.wait_for_load_state('domcontentloaded', timeout=60000)
                await page.wait_for_timeout(3000)

                # Шаг 4: Нажимаем Play
                try:
                    play_button = page.locator("button.vjs-big-play-button")

                    if await play_button.is_visible(timeout=10000):
                        print("▶️ Нажимаю Play...")
                        await play_button.click(force=True)
                        await page.wait_for_timeout(8000)  # Ждем загрузку видео
                    else:
                        print("⚠️ Кнопка Play не найдена, жду автозапуск...")
                        await page.wait_for_timeout(5000)

                except Exception as e:
                    print(f"⚠️ Ошибка с Play: {e}")

                # Закрываем браузер
                await browser.close()

                # Проверяем что нашли
                if not self.video_urls:
                    print("❌ Видео не найдено")
                    return None

                # Берем первую ссылку (обычно лучшего качества)
                video_url = self.video_urls[0]
                print(f"✅ Видео найдено: {video_url}")

                return video_url

        except Exception as e:
            print(f"❌ Ошибка парсера: {e}")
            return None


# Пример использования
# if __name__ == "__main__":
#     async def test():
#         parser = ZonaParser(headless=True)  # False чтобы видеть браузер
#         url = await parser.search_movie("халк")
#         if url:
#             print(f"\n🎉 Результат: {url}")
#         else:
#             print("\n😔 Не найдено")
#
#
#     asyncio.run(test())