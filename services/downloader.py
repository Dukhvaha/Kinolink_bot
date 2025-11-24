import aiohttp
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def download_video(url: str, path: str) -> str:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Не удалось скачать видео: {url}")

                data = await resp.read()

        with open(path, "wb") as f:
            f.write(data)

    return path


