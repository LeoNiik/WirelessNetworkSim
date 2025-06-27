
#___________________________________________________________________________________________________________________________________________________#

class RREQ:
    """Route Request (RREQ) packet for route discovery in AODV."""
    
    def __init__(self, source_id, dest_id, seq, hops=0, ttl=300000):
        self.source_id = source_id
        self.dest_id = dest_id
        self.seq = seq
        self.hops = hops
        self.ttl = ttl

    def __str__(self):
        return f"RREQ from {self.source_id} to {self.dest_id}, seq: {self.seq}, hops: {self.hops}, ttl: {self.ttl}"
    
#___________________________________________________________________________________________________________________________________________________#

class RREP:
    """Route Reply (RREP) packet for route discovery in AODV."""
    
    def __init__(self, source_id, dest_id, seq, hops):
        self.source_id = source_id
        self.dest_id = dest_id
        self.hops = hops
        self.seq = seq
        
    def __str__(self):
        return f"RREP from {self.source_id} to {self.dest_id}, seq: {self.seq}, hops: {self.hops}"

#___________________________________________________________________________________________________________________________________________________#

class RERR:
    """Route Error (RERR) packet for notifying broken routes in AODV."""
    
    def __init__(self, unreachable_nodes):
        self.unreachable_nodes = unreachable_nodes  # List of node IDs that are unreachable
        
    def __str__(self):
        return f"RERR for unreachable nodes: {', '.join(map(str, self.unreachable_nodes))}"

#___________________________________________________________________________________________________________________________________________________#

class RoutingTableEntry:
    """Entry in the routing table for AODV."""
    
    def __init__(self, dest_id, next_hop, seq, hops, cost=0):
        self.dest_id = dest_id
        self.next_hop = next_hop
        self.seq = seq
        self.hops = hops  # Number of hops to reach the destination
        self.cost = cost
        
    def __str__(self):
        return f"{self.dest_id}: ({self.next_hop}, {self.hops}, {self.seq})"