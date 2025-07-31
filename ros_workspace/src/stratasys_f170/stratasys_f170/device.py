from datetime import datetime

from httpx import AsyncClient, Response, RequestError, HTTPStatusError
from rclpy.impl.rcutils_logger import RcutilsLogger


class DeviceClient:

    def __init__(self, ip: str, log: RcutilsLogger) -> None:
        self._ip: str = ip
        self._base_url: str = f'http://{ip}:5000'
        self._log: RcutilsLogger = log
        self._client = AsyncClient(timeout=5.0)

    async def disconnect(self) -> None:
        await self._client.aclose()

    async def get_status(self) -> str:
        url: str = f"{self._base_url}/current"
        try:
            response: Response = await self._client.get(url)  # type: ignore
            response.raise_for_status()
            return response.text

        except RequestError as e:
            self._log.error(f"{datetime.now()} | Request error: {e}")
            raise

        except HTTPStatusError as e:
            self._log.error(
                f"{datetime.now()} | HTTP error: {e.response.status_code} - {e.response.text}")
            raise

        except Exception as e:
            self._log.error(
                f"{datetime.now()} | An exception occurred: {e}")
            raise
