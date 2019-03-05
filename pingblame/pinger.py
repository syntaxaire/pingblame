# used queue example from
# http://asyncio.readthedocs.io/en/latest/producer_consumer.html

import asyncio
import aioping


async def pinger(queue, address, delay, log):
    """Ping an address, then submit result to the queue."""

    await asyncio.sleep(delay)  # flood limiter

    try:
        log.sent_ping(address)
        rtt = await aioping.ping(str(address))
        # print(f"Ping reply from {address}: {rtt*1000:.0f}ms")
        log.got_ping(address, rtt)
    except TimeoutError:
        # print(f"Ping timed out to {address}")
        log.lost_ping(address)
    await queue.put(address)  # alert the reissuer to resubmit to this address


async def reporter(log):
    """Occasionally dump stats."""
    while True:
        await asyncio.sleep(5)
        print(log)


async def reissuer(queue, loop, delay, log):
    """Reissue answered pings."""
    while True:
        result = await queue.get()
        if result is None:
            print("Queue empty (bug!)")
            break
        address = result

        # reissue the ping that just completed
        next_pinger = pinger(queue, address, delay, log)
        loop.create_task(next_pinger)
