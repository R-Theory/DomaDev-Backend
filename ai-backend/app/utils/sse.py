from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional


HEARTBEAT_COMMENT = ": keepalive\n\n"


def format_sse_data(data: str, event: Optional[str] = None) -> bytes:
    lines = []
    if event:
        lines.append(f"event: {event}")
    for chunk_line in data.splitlines():
        lines.append(f"data: {chunk_line}")
    lines.append("")
    return ("\n".join(lines) + "\n").encode("utf-8")


async def heartbeat_sender(interval_seconds: float) -> AsyncIterator[bytes]:
    while True:
        await asyncio.sleep(interval_seconds)
        yield HEARTBEAT_COMMENT.encode("utf-8")
