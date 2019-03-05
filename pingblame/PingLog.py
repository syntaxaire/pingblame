class PingLog:
    """
    Keeps a record of how many ping packets have been sent and received for each address.
    sent_ping: record sent packet
    got_ping: record rec'd packet
    lost_ping: record lost packet
    __repr__: human readable log
    """

    def __init__(self, targets):
        self.data = {}
        for address in targets:
            self.data[address] = {'sent': 0,
                                  'received': 0,
                                  'lost': 0,
                                  'min': 0,
                                  'max': 0,
                                  'mean': 0,
                                  'in_flight': False, }

    def sent_ping(self, address):
        """Record that a ping has been sent to address."""
        self.data[address]['sent'] += 1
        self.data[address]['in_flight'] = True

    def got_ping(self, address, rtt):
        """Record that a ping has been received from address."""
        log = self.data[address]
        if log['received'] == 1:  # first answer for this address, initialize stats
            log['min'] = rtt
            log['max'] = rtt
            log['mean'] = rtt
        else:
            log['min'] = min(log['min'], rtt)
            log['max'] = max(log['max'], rtt)
            total = log['received']
            # TODO: verify correctness:
            log['mean'] = (total * log['mean'] + rtt) / (total + 1)
        log['in_flight'] = False
        log['received'] += 1

    def lost_ping(self, address):
        """Record that a ping was lost to address."""
        # Don't use (sent-received) because the log can be checked while a ping is in transit.
        self.data[address]['in_flight'] = False
        self.data[address]['lost'] += 1

    def __repr__(self):
        """Output the log in a readable format."""
        ret = ""
        for address in self.data:
            log = self.data[address]
            ret += f"{address}: sent {log['sent']}, "
            ret += f"received {log['received']}, lost {log['lost']}, "
            if log['in_flight']:
                ret += "1 in flight, "
            ret += f"min {log['min']}, max {log['max']}, mean {log['mean']}\n"
        return ret
