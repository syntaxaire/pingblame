# used queue example from http://asyncio.readthedocs.io/en/latest/producer_consumer.html

import ipaddress
import asyncio
import aioping
import configparser
import quamash


class Log:
    def __init__(self, targets):
        self.records = {}
        for address in targets:
            self.records[address] = {'sent': 0, 'received': 0, 'mean': 0, 'min': 0, 'max': 0}

    def sent_ping(self, address):
        self.records[address]['sent'] += 1

    def got_ping(self, address, rtt):
        self.records[address]['received'] += 1
        tot = self.records[address]['sent'] + self.records[address]['received']
        if rtt < self.records[address]['min']:
            self.records[address]['min'] = rtt
        if rtt > self.records[address]['max']:
            self.records[address]['max'] = rtt
        self.records[address]['mean'] = (tot * self.records[address]['mean'] + rtt) / (tot + 1)

    def __repr__(self):
        ret = ""
        for address in self.records:
            ret += f"{address}: {self.records[address]}\n"
        return ret


def get_address_list(config) -> list:
    targets = []
    for address in config["Addresses"]:
        try:
            targets.append(ipaddress.ip_address(address))
        except ipaddress.AddressValueError:
            print(f"Error in config: {address} is not a valid IPv4 address.")
            exit()
    return targets


async def pinger(queue, address):
    """Ping an address, then submit the address and ping time to the queue in a dict."""

    await asyncio.sleep(1)  # flood limiter

    rtt = await aioping.ping(str(address))
    answer = {'address': address, 'rtt': rtt}
    print(f"Ping reply from {address}: {rtt*1000:.0f}ms")
    await queue.put(answer)


async def reporter(queue, loop, logger):
    """Report on answers in queue, and reissue answered pings to event loop."""
    while True:
        item = await queue.get()
        if item is None:
            print("Queue empty (bug!)")
            break
        logger.got_ping(item['address'], item['rtt'])
        next_pinger = pinger(queue, item['address'])
        logger.sent_ping(item['address'])
        loop.create_task(next_pinger)
        print(logger)


def netblame():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("netblame.cfg")
    if "Addresses" not in config:
        print("No address list found in netblame.cfg")
        print("Please copy netblame.cfg.example to netblame.cfg and edit it.")
        exit()
    targets = get_address_list(config)
    if len(targets) == 0:
        print("No valid addresses in address list in netblame.cfg")
        exit()

    logger = Log(targets)

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)

    pingers = [pinger(queue, address) for address in targets]
    loop.run_until_complete(asyncio.gather(*pingers, reporter(queue, loop, logger)))


if __name__ == "__main__":
    netblame()
