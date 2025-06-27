from src.core.sensor_node import SensorNode
from src.core.aodv import RREP, RREQ, RERR, RoutingTableEntry
import copy
from collections import deque

class aodv_node(SensorNode):
    """
    A class representing a node in the AODV (Ad hoc On-Demand Distance Vector) routing protocol.
    This class is used to manage the state and behavior of a node in an AODV network.
    """

    def __init__(self,  node_id, x=0, y=0, transmission_range=1.0, network=None):
        """
        Initialize the AODV node with an ID and position.

        :param node_id: Unique identifier for the node.
        :param position: Position of the node in the network.
        """
        super().__init__(node_id, x,y, transmission_range, network)  # Call the parent class's __init__ method
        
        self.seq = 0  # Sequence number for node
        self.routing_table = {}  # {destination: (next_hop, cost)}
        self.broadcast_id = 0

        self.seen_rreqs = set()  # Set to track seen RREQs to avoid duplicates
        self.received_msgs = []  # List to store received messages for processing

    #___________________________________________________# Ad Hoc On Demand Distance Vector Routing Methods #____________________________________________#
    #___________________________________________________________________________________________________________________________________________________#


    def isDuplicate(self, rreq, verbose=False):
        """Check if the RREQ is a duplicate based on source ID and sequence number."""
        if verbose:
            print(f"Node {self.node_id}: Checking if RREQ is duplicate: [{rreq}], seen_rreqs: {self.seen_rreqs}")

        return (rreq.source_id, rreq.seq) in self.seen_rreqs
         
    def discover_neighbors(self, network, verbose=False):
        """Discover neighbors and initialize routing table."""
        if verbose:
            print(f"Node {self.node_id}: Discovering neighbors and initializing routing table.")
        
        # Send initial RREQs to neighbors
        for neighbor_id in self.get_neighbors():
            if neighbor_id in self.routing_table:
                continue
            neighbor = network.get_node_by_id(neighbor_id)
            if neighbor:
                rreq = RREQ(self.node_id, neighbor_id, self.seq)
                rreq.broadcast_id = self.broadcast_id
                self.broadcast_id += 1
                self.seq += 1
                self.seen_rreqs.add((rreq.source_id, rreq.seq))
                if verbose:
                    print(f"Node {self.node_id}: Sending initial RREQ to neighbor {neighbor_id}: [{rreq}]")
                neighbor.receive_RREQ(network, rreq, self.node_id, verbose)
        
    def send_RREQ(self, network, dest_id, verbose=False):
        """Send a Route Request (RREQ) using BFS to discover a route to the destination."""
        if dest_id == self.node_id:
            return

        rreq = RREQ(self.node_id, dest_id, self.seq)
        rreq.broadcast_id = self.broadcast_id
        self.broadcast_id += 1
        self.seq += 1  # increment after creating RREQ

        self.seen_rreqs.add((rreq.source_id, rreq.seq))

        if verbose:
            print(f"Node {self.node_id}: Starting BFS RREQ for destination {dest_id}")

        # Initialize BFS queue
        queue = deque()
        for neighbor_id in self.get_neighbors():
            neighbor = network.get_node_by_id(neighbor_id)
            if neighbor:
                queue.append((neighbor, rreq, self.node_id))  # (node_obj, rreq_packet, forwarder_id)

        while queue:

            current_node, current_rreq, forwarder_id = queue.popleft()
            
            # If node already saw this RREQ, skip
            if (current_rreq.source_id, current_rreq.seq) in current_node.seen_rreqs:
                continue

            # Mark as seen and update routing table
            current_node.seen_rreqs.add((current_rreq.source_id, current_rreq.seq))
            new_route = RoutingTableEntry(current_rreq.source_id, forwarder_id, current_rreq.seq, current_rreq.hops + 1)
            # new_route = (forwarder_id, current_rreq.hops + 1, current_rreq.seq)
            current_node.update_RT(current_rreq.source_id, new_route, verbose)

            if verbose:
                print(f"Node {current_node.node_id}: Processing RREQ [{current_rreq}] from {forwarder_id}")

            if current_rreq.dest_id == current_node.node_id:
                current_node.send_RREP(current_node.node_id, current_rreq.source_id, current_node.seq, 0, network, verbose)
                continue
            # If current node has a fresh route to the destination, reply instead of forwarding
            if current_rreq.dest_id in current_node.routing_table:
                # next_hop, known_hops, seq = current_node.routing_table[current_rreq.dest_id]
                route = current_node.routing_table[current_rreq.dest_id]
                if route.next_hop != forwarder_id and route.next_hop != current_node.node_id:
                    dst_node = network.get_node_by_id(current_rreq.dest_id)
                    current_node.send_RREP(current_rreq.dest_id, current_rreq.source_id, dst_node.seq, route.hops, network, verbose)
                    continue
            # Otherwise enqueue neighbors for BFS
            next_hops = current_node.get_neighbors()
            for next_id in next_hops:
                if next_id == forwarder_id:
                    continue  # avoid sending back
                neighbor_node = network.get_node_by_id(next_id)
                if neighbor_node:
                    # Create a shallow copy of the RREQ with incremented hops
                    forwarded_rreq = copy.copy(current_rreq)
                    forwarded_rreq.hops += 1
                    queue.append((neighbor_node, forwarded_rreq, current_node.node_id))



    def receive_MSG(self, msg_packet, network, sender_id, verbose=False):
        """Receive a message and either consume it or forward it."""
        # print(f"Node {self.node_id}",msg_packet)
        
        msg_packet['path'].append(self.node_id)
        msg_packet['hops'] += 1

        if self.node_id == msg_packet['dst']:
            self.received_msgs.append(copy.deepcopy(msg_packet))
            if verbose:
                print(f"Node {self.node_id}: Received message from {msg_packet['src']} via path {msg_packet['path']}")
            return msg_packet['hops'], msg_packet['path']
        
        # Check if we have a valid route to the destination
        dst_id = msg_packet['dst']
        if dst_id not in self.routing_table:
            self.send_RREQ(network, dst_id, verbose)
            if dst_id not in self.routing_table:
                if verbose:
                    print(f"Node {self.node_id}: No route to destination {dst_id}, dropping message.")
                return None, msg_packet['path']

        # next_hop, _, _= self.routing_table[dst_id]
        next_hop = self.routing_table[dst_id].next_hop
        # print(f"Node {self.node_id}: Forwarding message to next hop {next_hop} for destination {dst_id}")
        if msg_packet['hops'] > 40:
            print(f"node {self.node_id}: mgs_path {msg_packet['path']}")
            for node in network.nodes:
                node.print_routing_table()
            exit(69)
        # Check if the next hop is still connected
        if not network.link_exists(self.node_id, next_hop):
            if verbose:
                print(f"Node {self.node_id}: Broken link to next hop {next_hop}, rediscovering route.")
            self.send_RREQ(network, dst_id, verbose)
            if dst_id not in self.routing_table:
                if verbose:
                    print(f"Node {self.node_id}: Route discovery failed, dropping message.")
                return None, msg_packet['path']
            next_hop = self.routing_table[dst_id].next_hop
            # next_hop, _, _ = self.routing_table[dst_id]

        return network.get_node_by_id(next_hop).receive_MSG(
            msg_packet, network, self.node_id, verbose
        )


    def send_MSG(self, dst_id, msg, network, verbose=False):
        """Send a message using the routing protocol (AODV-like)."""

        # Step 1: Check if a route exists
        if dst_id not in self.routing_table:
            self.send_RREQ(network, dst_id, verbose)
            if dst_id not in self.routing_table:
                if verbose:
                    print(f"Node {self.node_id}: Failed to discover route to {dst_id}")
                return None, []

        # next_hop, hops, seq = self.routing_table[dst_id]
        next_hop = self.routing_table[dst_id].next_hop

        # Step 2: Check if the link to the next hop is still valid
        if not network.link_exists(self.node_id, next_hop):
            if verbose:
                print(f"Node {self.node_id}: Link to next hop {next_hop} is broken. Re-discovering route...")
            self.send_RREQ(network, dst_id, verbose)
            if dst_id not in self.routing_table:
                if verbose:
                    print(f"Node {self.node_id}: Failed to re-discover route to {dst_id}")
                return None, []
            # next_hop, hops, _ = self.routing_table[dst_id]  # Refresh route after discovery
            next_hop = self.routing_table[dst_id].next_hop

        # Step 3: Create and send the message packet
        msg_packet = {
            'src': self.node_id,
            'dst': dst_id,
            'payload': msg,
            'hops': 0,
            'path': [self.node_id]
        }
        # print(f"Node {self.node_id}: Sending message to {dst_id} via next hop {next_hop}")
        network.get_node_by_id(next_hop).receive_MSG(msg_packet, network, self.node_id, verbose)
        return msg_packet['hops'], msg_packet['path']



    def forward_RREQ(self, rreq, network, forwarder_id, verbose=False):
        """Forward a Route Request (RREQ) to the next hop."""

        # Check if TTL has expired
        if rreq.ttl <= 0:
            return

        # Prepare new RREQ copy
        new_rreq = RREQ(rreq.source_id, rreq.dest_id, rreq.seq, rreq.hops + 1, rreq.ttl - 1)
        if verbose:
            print(f"Node {self.node_id}: forwarding RREQ: [{new_rreq}] to neighbors")

        if verbose:
            print(self.get_neighbors())

        # Forward the RREQ to all neighbors
        for neighbor_id in self.get_neighbors():
            if neighbor_id == forwarder_id:
                if verbose:
                    print(f"Node {self.node_id}: Not forwarding RREQ back to {forwarder_id}")
                continue  # don’t send it back where it came from

            neighbor = network.get_node_by_id(neighbor_id)
            neighbor.receive_RREQ(network, new_rreq, self.node_id, verbose)

            self.route_discovery_msg_count += 1
        return
        
    def update_RT(self, dest_id, new_route, verbose=False):
        """Update routing table only if the new route is better or the current one is broken."""
        # newNextHop, nHops, newSeq = new_route
        
        current = self.routing_table.get(dest_id)

        if verbose:
            print(f"Node {self.node_id}: Updating routing table for {dest_id} with new route: {new_route}, current: {current}")

        if current is None:
            # No existing route — accept new route
            self.routing_table[dest_id] = new_route
            # self.routing_table[dest_id] = (newNextHop, nHops, newSeq)
            return

        # currNextHop, currHops, currSeq = current

        # Ignore old sequence numbers
        if new_route.seq < current.seq:
            if verbose:
                print(f"Node {self.node_id}: Ignoring route for {dest_id} with lower seq {new_route.seq} than current {current.seq}")
            return

        # If the new sequence number is fresher, accept it
        if new_route.seq >= current.seq:
            self.routing_table[dest_id] = new_route
            return

        # If sequence numbers are equal, prefer lower hop count
        if new_route.hops < current.hops:
            self.routing_table[dest_id] = new_route
            return

        # If the current route is through a broken link, replace it anyway
        if not self.network.link_exists(self.node_id, current.next_hop):
            if verbose:
                print(f"Node {self.node_id}: Replacing broken route to {dest_id} with new route via {new_route.next_hop}")
            self.routing_table[dest_id] = new_route


    def receive_RREQ(self, network, rreq, forwarder_id, verbose=False):
        """Receive a Route Request (RREQ) and process it."""
        if self.isDuplicate(rreq, verbose):
            # If this RREQ is a duplicate, ignore it
            return
        self.seen_rreqs.add((rreq.source_id, rreq.seq))
        
        if verbose:
            print(f"Node {self.node_id}: received RREQ: [{rreq}] from {forwarder_id} for destination {rreq.dest_id}")

        
        # new_route = (forwarder_id, rreq.hops + 1, rreq.seq)
        new_route = RoutingTableEntry(rreq.source_id, forwarder_id, rreq.seq, rreq.hops + 1)
        self.update_RT(rreq.source_id, new_route, verbose)

        self.broadcast_id += 1
        # Check if this node is the destination
        if rreq.dest_id == self.node_id:
            # If this node is the destination, send a RREP back
            self.send_RREP(self.node_id, rreq.source_id, self.seq, 0, network, verbose)
            return
        
        # If this node is not the destination, check if we have a route to the destination
        if rreq.dest_id in self.routing_table:
            route = self.routing_table[rreq.dest_id]
            # next_hop, known_hops, seq = self.routing_table[rreq.dest_id]
            # if next_hop == forwarder_id or next_hop == self.node_id:
            if route.next_hop == forwarder_id or route.next_hop == self.node_id:
                return
            dst_node = network.get_node_by_id(rreq.dest_id)
            self.send_RREP(rreq.dest_id, rreq.source_id, dst_node.seq, route.hops, network, verbose)
            # self.send_RREP(rreq.dest_id, rreq.source_id, dst_node.seq, known_hops, network, verbose)
            return
            
        # If we don't have a route, forward the RREQ to neighbors
        self.forward_RREQ(rreq, network, forwarder_id, verbose)

    def send_RREP(self, source_id, dest_id, seq, hops, network, verbose=False):
        """
        Send a unicast Route Reply (RREP) back to the originator of the RREQ.
        source_id: the original destination of the RREQ (i.e., this node or known destination)
        dest_id: the originator of the RREQ (i.e., who we’re sending the RREP to)
        """
        rrep = RREP(source_id, dest_id, seq, hops)
        if verbose:
            print(f"Node {self.node_id}: Sending RREP: [{rrep}] to {dest_id} from {source_id} with hops {hops}")
        # Lookup next hop to the RREQ originator
        if dest_id in self.routing_table:
            next_hop = self.routing_table[dest_id].next_hop
            # next_hop, _, _ = self.routing_table[dest_id]

            next_node = network.get_node_by_id(next_hop)
            next_node.receive_RREP(rrep, network, self.node_id, verbose)
            self.route_discovery_msg_count += 1
        else:
            # No route back to the originator, drop the packet (or log error)
            if verbose:
                print(f"Node {self.node_id}: No route to RREQ originator {dest_id}, cannot send RREP")



    def receive_RREP(self, rrep, network, forwarder_id, verbose=False):
        """Receive a Route Reply (RREP) and update routing table."""
        if verbose:
            print(f"Node {self.node_id}: received RREP: [{rrep}] from {forwarder_id} for destination {rrep.dest_id}")
        # Update route to the RREP originator (the final destination of the RREQ)
        rrep.hops += 1
        # new_route = (forwarder_id, rrep.hops, rrep.seq)
        new_route = RoutingTableEntry(rrep.source_id, forwarder_id, rrep.seq, rrep.hops)
        # print(f"Node {self.node_id}: {new_route}")
        self.update_RT(rrep.source_id, new_route, verbose)

        # If this node is the original RREQ source, we're done
        if rrep.dest_id == self.node_id:
            return

        # Otherwise, forward RREP toward original source of RREQ
        if rrep.dest_id in self.routing_table:
            next_hop = self.routing_table[rrep.dest_id].next_hop
            # next_hop, _, _ = self.routing_table[dest_id]
            # Increment hop count before forwarding
            next_node = network.get_node_by_id(next_hop)
            next_node.receive_RREP(rrep, network, self.node_id, verbose)
            self.route_discovery_msg_count += 1
        else:
            # No route back to the originator, drop the packet (or log error)
            if verbose:
                print(f"Node {self.node_id}: No route to RREQ originator {rrep.dest_id}, cannot send RREP")



    def print_routing_table(self):
        """Print the routing table for debugging."""
        entries = [f"{dest_id}: ({entry.next_hop}, {entry.hops}, {entry.seq})" for dest_id, entry in self.routing_table.items()]
        routing_table_str = f"Node {self.node_id} Routing Table: {' | '.join(entries)}"
        print(routing_table_str)
        return routing_table_str
