# used queue example from http://asyncio.readthedocs.io/en/latest/producer_consumer.html

import ipaddress
import asyncio
import aioping
import configparser

import PingLog


def get_address_list(config) -> list:
    targets = []
    for address in config["Addresses"]:
        try:
            targets.append(ipaddress.ip_address(address))
        except ipaddress.AddressValueError:
            print(f"Error in config: {address} is not a valid IPv4 address.")
            exit()
    return targets


async def pinger(queue, address, delay, log):
    """Ping an address, then submit the address and ping time to the queue in a dict."""

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


def netblame():
    config = configparser.ConfigParser(allow_no_value=True)
    try:
        config.read("netblame.cfg")
    except:  # TODO: this can apparently silently fail, see source
        print("Configuration missing. Please copy netblame.cfg.example to netblame.cfg and edit it.")
        exit()
    targets = get_address_list(config)
    if len(targets) == 0:
        print("No valid addresses in address list in netblame.cfg")
        exit()
    delay = float(config['Delay']['delay'])

    log = PingLog.PingLog(targets)

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)

    pingers = [pinger(queue, address, delay, log) for address in targets]
    loop.run_until_complete(asyncio.gather(*pingers, reissuer(queue, loop, delay, log), reporter(log)))


if __name__ == "__main__":
    netblame()
