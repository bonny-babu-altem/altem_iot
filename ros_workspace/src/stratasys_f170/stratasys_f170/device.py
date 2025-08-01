from asyncio.subprocess import Process
import platform
import asyncio
from typing import Any, Optional
from httpx import AsyncClient, Response

import rclpy
from rclpy.impl.rcutils_logger import RcutilsLogger


class DeviceRequest:
    __slots__: tuple[str, ...] = (
        '_client',
        '_base_url',
        '_timeout',
        '_log'
    )

    def __init__(self, url: str, log: RcutilsLogger, timeout: float = 10.0) -> None:
        self._base_url: str = f'http://{url}:5000'
        self._timeout: float = timeout
        self._log: RcutilsLogger = log

        self._client: AsyncClient

    async def _is_client(self) -> bool:
        return hasattr(self, '_client')

    async def connect(self) -> None:
        if not await self._is_client():
            self._log.info(f'Trying to connect to {self._base_url}')
            self._client = AsyncClient(
                base_url=self._base_url, timeout=self._timeout)

    async def disconnect(self) -> None:
        if await self._is_client():
            await self._client.aclose()

    async def get(self, endpoint: str = '/current', params: Optional[dict[str, Any]] = None) -> Response:
        if not await self._is_client():
            raise RuntimeError("Client not initialized. Use 'connect'.")

        response: Response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        return response


async def ping_ip(ip: str, count: int = 1, timeout: int = 1) -> bool:
    system: str = platform.system().lower()
    args: list[str] = ["ping"]

    if system == "windows":
        args += ["-n", str(count), "-w", str(timeout * 1000), ip]
    else:
        args += ["-c", str(count), "-W", str(timeout), ip]

    process: Process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    return await process.wait() == 0


async def wait_for_device_ip(
        ip: str, delay: float = 2.0, max_attempts: int = 0,
        logger: Optional[RcutilsLogger] = None) -> bool:

    attempt = 0
    while rclpy.ok():
        if await ping_ip(ip):
            if logger:
                logger.info(f"Device at {ip} is reachable.")
            return True

        attempt += 1
        msg: str = f"Device at {ip} not reachable. Attempt {attempt}"
        if logger:
            logger.warn(msg)
        else:
            print(msg)

        if max_attempts and attempt >= max_attempts:
            if logger:
                logger.error(
                    f"Device at {ip} not reachable after {max_attempts} attempts.")
            return False

        await asyncio.sleep(delay)

    return False
