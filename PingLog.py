class PingLog:
    def __init__(self, targets):
        self.data = {}
        for address in targets:
            self.data[address] = {'sent': 0, 'received': 0, 'lost': 0, 'min': 0, 'max': 0, 'mean': 0, 'in_flight': False}

    def sent_ping(self, address):
        self.data[address]['sent'] += 1
        self.data[address]['in_flight'] = True

    def got_ping(self, address, rtt):
        log = self.data[address]
        if log['received'] == 1:  # first answer for this address, initialize stats
            log['min'] = rtt
            log['max'] = rtt
            log['mean'] = rtt
        else:
            log['min'] = min(log['min'], rtt)
            log['max'] = max(log['max'], rtt)
            total = log['received']
            log['mean'] = (total * log['mean'] + rtt) / (total + 1)  # TODO: verify correctness
        log['in_flight'] = False
        log['received'] += 1

    def lost_ping(self, address):
        # Don't use (sent - received) because the log can be checked while a ping is in transit.
        self.data[address]['in_flight'] = False
        self.data[address]['lost'] += 1

    def __repr__(self):
        ret = ""
        for address in self.data:
            log = self.data[address]
            ret += f"{address}: sent {log['sent']}, received {log['received']}, lost {log['lost']}, "
            if log['in_flight']:
                ret += "1 in flight, "
            ret += f"min {log['min']}, max {log['max']}, mean {log['mean']}\n"

        return ret