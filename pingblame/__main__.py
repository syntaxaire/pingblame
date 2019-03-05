import asyncio
import configparser
import ipaddress
import sys
from pathlib import Path
from pingblame import PingLog
from pingblame.pinger import pinger, reissuer, reporter

CONFIG_FILE = Path('pingblame') / Path('pingblame.cfg')


def get_address_list(config) -> list:
    targets = []
    for address in config["Addresses"]:
        try:
            targets.append(ipaddress.ip_address(address))
        except ipaddress.AddressValueError:
            print(f"Error in config: {address} is not a valid IPv4 address.")
            sys.exit(1)
    return targets


app_config = configparser.ConfigParser(allow_no_value=True)
try:
    app_config.read(CONFIG_FILE)
except FileNotFoundError:
    print("No configuration. Copy pingblame.cfg.example to pingblame.cfg.")
    sys.exit(1)
targets = get_address_list(app_config)
if len(targets) == 0:
    print("No valid addresses in address list in pingblame.cfg")
    sys.exit(1)
delay = float(app_config['Delay']['delay'])

log = PingLog.PingLog(targets)
loop = asyncio.get_event_loop()
queue = asyncio.Queue(loop=loop)
pingers = [pinger(queue, address, delay, log) for address in targets]
loop.run_until_complete(
    asyncio.gather(*pingers, reissuer(queue, loop, delay, log), reporter(log)))
