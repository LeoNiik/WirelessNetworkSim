
#___________________________________________________________________________________________________________________________________________________#

class RREQ:
    """Route Request (RREQ) packet for route discovery in AODV."""
    
    def __init__(self, source_id, dest_id, src_seq, dest_seq=0, hops=0, ttl=300, cost=0):
        self.broadcast_id = 0  # Unique identifier for the RREQ, can be incremented for each new RREQ
        self.dest_id = dest_id
        self.dest_seq = dest_seq  # Sequence number of the destination node, initialized to 0
        self.source_id = source_id
        self.src_seq = src_seq
        self.hops = hops
        self.cost = cost # Cost of the route, can be used for metrics like bandwidth or delay

    def __str__(self):
        return f"RREQ from {self.source_id} to {self.dest_id}, dest_seq: {self.dest_seq}, hops: {self.hops}"
    
#___________________________________________________________________________________________________________________________________________________#

class RREP:
    """Route Reply (RREP) packet for route discovery in AODV."""
    
    # def __init__(self, source_id, dest_id, seq, hops):
    #     self.source_id = source_id
    #     self.dest_id = dest_id
    #     self.hops = hops
    #     self.seq = seq
        
    def __init__(self, source_id, dest_id, seq, hops, cost):
        self.dest_id = dest_id          # original source of RREQ
        self.dest_seq = seq        # latest known seq number for dest
        self.source_id = source_id      # destination of RREQ (initiator of RREP)
        self.hops = hops
        self.cost = cost
        self.ttl = 300  # Time to live for the RREP packet, can be adjusted based on network conditions

    def __str__(self):
        return f"RREP from {self.source_id} to {self.dest_id}, dest_seq: {self.dest_seq}, hops: {self.hops}"

#___________________________________________________________________________________________________________________________________________________#

class RERR:
    """Route Error (RERR) packet for notifying broken routes in AODV."""
    

    def __init__(self, unreachable_nodes):
        self.broadcast_id = 0  # Unique identifier for the RERR, can be incremented for each new RERR
        self.unreachable_nodes = unreachable_nodes  # List of node IDs that are unreachable
        self.dest_count = len(unreachable_nodes)  # Number of unreachable nodes
        
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