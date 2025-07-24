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

        self.msg_stats = {
            'rreq_sent': 0, 'rreq_recv': 0,
            'rrep_sent': 0, 'rrep_recv': 0,
            'rerr_sent': 0, 'rerr_recv': 0,
            'data_sent': 0, 'data_recv': 0,
        }

        self.seen_rerrs = set()
        self.seen_rreqs = set()  # Set to track seen RREQs to avoid duplicates
        self.received_msgs = []  # List to store received messages for processing

    #___________________________________________________# Ad Hoc On Demand Distance Vector Routing Methods #____________________________________________#
    #___________________________________________________________________________________________________________________________________________________#


    def isDuplicate(self, rreq, verbose=False):
        """Check if the RREQ is a duplicate based on source ID and sequence number."""
        if verbose:
            print(f"Node {self.node_id}: Checking if RREQ is duplicate: [{rreq}], seen_rreqs: {self.seen_rreqs}")

        return (rreq.source_id, rreq.broadcast_id) in self.seen_rreqs

    
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
                # self.seq += 1
                # self.broadcast_id += 1
                # rreq = RREQ(self.node_id, neighbor_id, self.seq)
                # rreq.broadcast_id = self.broadcast_id
                # self.seen_rreqs.add((rreq.source_id, rreq.broadcast_id))


                if verbose:
                    print(f"Node {self.node_id}: Sending initial RREQ to neighbor {neighbor_id}: [{rreq}]")
                
                self.msg_stats['rreq_sent'] += 1
                self.send_RREQ(network, neighbor_id, verbose)
                # neighbor.receive_RREQ(network, rreq, self.node_id, verbose)


    def broadcast_RREQ(self, network, dest_id, verbose=False):
        """Send a Route Request (RREQ) using BFS to discover a route to the destination."""
        if dest_id == self.node_id:
            return
        self.seq += 1  # increment before creating RREQ
        self.broadcast_id += 1
        # I should use the last known dst_seq not self.seq or 0
        rreq = RREQ(self.node_id, dest_id, self.seq)
        rreq.broadcast_id = self.broadcast_id

        self.msg_stats['rreq_sent'] += 1

        self.seen_rreqs.add((rreq.source_id, rreq.broadcast_id))

        if verbose:
            print(f"Node {self.node_id}: Starting BFS RREQ for destination {dest_id}")

        # Initialize BFS queue
        for neighbor_id in self.get_neighbors():
            neighbor = network.get_node_by_id(neighbor_id)
            if neighbor:
                network.queue.append((neighbor, rreq, self.node_id))  # (node_obj, rreq_packet, forwarder_id)


    def send_RREQ(self, network, dest_id, verbose=False):
        """Send a Route Request (RREQ) using BFS to discover a route to the destination."""
        if dest_id == self.node_id:
            return

        self.seq += 1  # increment before creating RREQ
        self.broadcast_id += 1
        # I should use the last known dst_seq not self.seq or 0
        rreq = RREQ(self.node_id, dest_id, self.seq)
        rreq.broadcast_id = self.broadcast_id

        self.msg_stats['rreq_sent'] += 1

        self.seen_rreqs.add((rreq.source_id, rreq.broadcast_id))

        if verbose:
            print(f"Node {self.node_id}: Starting BFS RREQ for destination {dest_id}")

        # Initialize BFS queue
        dst_node = network.get_node_by_id(dest_id)
        network.queue.append((dst_node, rreq, self.node_id))  # (node_obj, rreq_packet, forwarder_id)


    def forward_RREQ(self, rreq, network, forwarder_id, verbose=False):
        """Broadcast a Route Request (RREQ) to all neighbors."""

        self.msg_stats['rreq_recv'] += 1

        if verbose:
            print(f"Node {self.node_id}: Broadcasting RREQ: [{rreq}] from {forwarder_id}")

        # Forward the RREQ to all neighbors
        for neighbor_id in self.get_neighbors():
            if neighbor_id == forwarder_id:
                continue
            neighbor = network.get_node_by_id(neighbor_id)
            if neighbor:
                # Create a shallow copy of the RREQ with incremented hops and cost
                forwarded_rreq = copy.copy(rreq)
                forwarded_rreq.hops += 1
                forwarded_rreq.cost += network.get_link_cost(self.node_id, forwarder_id)
                
                if verbose:
                    print(f"Node {self.node_id}: Forwarding RREQ to neighbor {neighbor_id}")

                # Use the network's queue to send the RREQ
                network.queue.append((neighbor, forwarded_rreq, self.node_id))


    def receive_MSsG(self, msg_packet, network, sender_id, verbose=False):
        """Receive a message and either consume it or forward it."""
        # print(f"Node {self.node_id}",msg_packet)
        
        msg_packet['path'].append(self.node_id)
        msg_packet['hops'] += 1
        msg_packet['cost'] += network.get_link_cost(self.node_id, sender_id)

        if self.node_id == msg_packet['dst']:
            self.msg_stats['data_recv'] += 1
            self.received_msgs.append(copy.deepcopy(msg_packet))
            if verbose:
                print(f"Node {self.node_id}: Received message from {msg_packet['src']} via path {msg_packet['path']}")
            return msg_packet['hops'], msg_packet['path'], msg_packet['cost']
        
        dst_id = msg_packet['dst']


        try:    
            next_hop = self.routing_table[dst_id].next_hop
        except KeyError:
            print(f"Node {self.node_id}: No route to destination {dst_id}, initiating route discovery.")
            network.route_discovery(self.node_id, dst_id, verbose)
        
        next_hop = self.routing_table[dst_id].next_hop

        # DEBUG 
        if msg_packet['hops'] > 40:
            print("Loop detected in message forwarding!")

            print(f"node {self.node_id}: mgs_path {msg_packet['path']}")
            for node in network.nodes:
                node.print_routing_table()
            exit(69)

        return network.get_node_by_id(next_hop).receive_MSG(
            msg_packet, network, self.node_id, verbose
        )
    
    def receive_MSG(self, msg_packet, network, sender_id, verbose=False):
        """Receive a message and either consume it or forward it."""
        # Aggiungo il mio ID al path
        msg_packet['path'].append(self.node_id)

        # ————————————————————————————— Loop detection —————————————————————————————
        dst_id = msg_packet['dst']
        next_hop = None
        if dst_id in self.routing_table:
            next_hop = self.routing_table[dst_id].next_hop

        if next_hop in msg_packet['path']:
            if verbose:
                print(f"Node {self.node_id}: loop detected via next_hop {next_hop}, invalidating route to {dst_id}")
            # 1) Invalido la rotta corrotta
            del self.routing_table[dst_id]
            # 2) Invio RERR verso i vicini
            self.send_RERR([dst_id], network, verbose=verbose)
            # 3) Se sono il mittente, rilancio route discovery
            if msg_packet['src'] == self.node_id:
                if verbose:
                    print(f"Node {self.node_id}: restarting the discovery of the path for {dst_id}")
                network.route_discovery(self.node_id, dst_id, verbose)
            # Stoppo qui il forwarding
            return None, msg_packet['path'], msg_packet.get('cost')
        # ——————————————————————————————————————————————————————————————————————

        # Aggiorno hops e cost
        msg_packet['hops'] += 1
        msg_packet['cost'] += network.get_link_cost(self.node_id, sender_id)

        # Se sono la destinazione, consegno localmente
        if self.node_id == dst_id:
            self.msg_stats['data_recv'] += 1
            self.received_msgs.append(copy.deepcopy(msg_packet))
            if verbose:
                print(f"Node {self.node_id}: Received message from {msg_packet['src']} via path {msg_packet['path']}")
            return msg_packet['hops'], msg_packet['path'], msg_packet['cost']

        # Altrimenti inoltro o innesco discovery
        if dst_id not in self.routing_table:
            if verbose:
                print(f"Node {self.node_id}: No route to destination {dst_id}, initiating route discovery.")
            network.route_discovery(self.node_id, dst_id, verbose)

        next_hop = self.routing_table[dst_id].next_hop
        return network.get_node_by_id(next_hop).receive_MSG(
            msg_packet, network, self.node_id, verbose
        )


    def can_send(self, dst_node):
        dst_id = dst_node.node_id
        """Check if the node can send messages based on its routing table."""
        if not self.routing_table:
            return False
        
        if dst_id not in self.routing_table:
            return False
        
        # Check if the next hop is still valid
        next_hop = self.routing_table[dst_id].next_hop

        # Get every node that is reachable by next hop
        potential_unreachable_nodes = []
        for entry in self.routing_table.values():
            if entry.next_hop == next_hop:
                potential_unreachable_nodes.append(entry.dest_id)  


        if not self.network.link_exists(self.node_id, next_hop):
            # TODO self.send_RERR
            print(f"Node {self.node_id}: Cant send to {dst_id} generating RERR")

            self.send_RERR(potential_unreachable_nodes, self.network, verbose=False)
            return False    
        
        # If we have a valid route to the destination, we can send messages
        print(f"Node {self.node_id}: Can send to {dst_id} via next hop {next_hop}")
        next_node = self.network.get_node_by_id(next_hop)
        # return next_node.can_send(dst_node)
        return True

    def send_RERR(self, unreachable_nodes, network, verbose=False):
        """Send a Route Error (RERR) to notify about unreachable nodes."""
        if not unreachable_nodes:
            return
        
        rerr = RERR(unreachable_nodes)
        self.msg_stats['rerr_sent'] += 1
        rerr_key = tuple(sorted(map(int, rerr.unreachable_nodes)))
        self.seen_rerrs.add(rerr_key)  # Store the unreachable nodes as a tuple for uniqueness

        if verbose:
            print(f"Node {self.node_id}: Sending RERR: [{rerr}] for unreachable nodes {unreachable_nodes}")

        # Forward the RERR to all neighbors
        for neighbor_id in self.get_neighbors():
            neighbor = network.get_node_by_id(neighbor_id)
            if neighbor:
                neighbor.receive_RERR(rerr, network, self.node_id, verbose)
                # Use the network's queue to send the RERR
                # network.queue.append((neighbor, rerr, self.node_id))

    def receive_RERR(self, rerr, network, forwarder_id, verbose=False):
        """Receive a Route Error (RERR) and update routing table."""
        rerr_key = tuple(sorted(map(int, rerr.unreachable_nodes)))
        if (rerr_key in self.seen_rerrs):
            return  # Ignore duplicate RERRs
        
        self.seen_rerrs.add(rerr_key)  # Store the unreachable nodes as a tuple for uniqueness
        
        if verbose:
            print(f"Node {self.node_id}: received RERR: [{rerr}] from {forwarder_id} for unreachable nodes {rerr.unreachable_nodes}")

        self.msg_stats['rerr_recv'] += 1

        # Remove the unreachable nodes from the routing table
        for node_id in rerr.unreachable_nodes:
            if node_id in self.routing_table:
                del self.routing_table[node_id]
                print(f"Node {self.node_id}: Removed route to unreachable node {node_id}")
                if verbose:
                    print(f"Node {self.node_id}: Removed route to unreachable node {node_id}")

        # Forward the RERR to all neighbors
        for neighbor_id in self.get_neighbors():
            # Skip the forwarder to avoid sending it back
            if neighbor_id == forwarder_id:
                continue
            
            neighbor = network.get_node_by_id(neighbor_id)
            if neighbor:
                neighbor.receive_RERR(rerr, network, self.node_id, verbose)


    def send_MSG(self, dst_id, msg, network, verbose=False):
        """Send a message using the routing protocol (AODV-like)."""
        if dst_id == self.node_id:
            if verbose:
                print(f"Node {self.node_id}: Cannot send message to itself.")
            return None, [], None
        

        # next_hop, hops, seq = self.routing_table[dst_id]
        next_hop = self.routing_table[dst_id].next_hop

    
        # Create and send the message packet
        msg_packet = {
            'src': self.node_id,
            'dst': dst_id,
            'payload': msg,
            'hops': 0,
            'cost': 0,
            'path': [self.node_id]
        }
        self.msg_stats['data_sent'] += 1

        # print(f"Node {self.node_id}: Sending message to {dst_id} via next hop {next_hop}")
        network.get_node_by_id(next_hop).receive_MSG(msg_packet, network, self.node_id, verbose)

        return msg_packet['hops'], msg_packet['path'], msg_packet['cost']


    def update_RT(self, dest_id, new_route, verbose=False):
        current = self.routing_table.get(dest_id)
        
        # No existing route - accept new one
        if current is None:
            self.routing_table[dest_id] = new_route
            return True
            
        # Existing route is broken - replace it
        if not self.network.link_exists(self.node_id, current.next_hop):
            self.routing_table[dest_id] = new_route
            return True
            
        # New route has significantly fresher sequence number
        if new_route.seq > current.seq:
            self.routing_table[dest_id] = new_route
            return True
            
        # Same sequence number but better metric
        if new_route.seq == current.seq and new_route.cost < current.cost:
            self.routing_table[dest_id] = new_route
            return True
            
        return False  # No update made


    def receive_RREQ(self, network, rreq, forwarder_id, verbose=False):
        """Receive a Route Request (RREQ) and process it."""
        if self.isDuplicate(rreq, verbose):
            # If this RREQ is a duplicate, ignore it
            return
        self.seen_rreqs.add((rreq.source_id, rreq.broadcast_id))
        self.msg_stats['rreq_recv'] += 1

        if verbose:
            print(f"Node {self.node_id}: received RREQ: [{rreq}] from {forwarder_id} for destination {rreq.dest_id}")

        
        # Update Reverse Path
        link_cost = network.get_link_cost(self.node_id, forwarder_id)
        new_route = RoutingTableEntry(rreq.source_id, forwarder_id, rreq.src_seq, rreq.hops + 1, rreq.cost + link_cost)
        self.update_RT(rreq.source_id, new_route, verbose)

        # Check if this node is the destination
        if rreq.dest_id == self.node_id:

            self.seq = max(self.seq, rreq.dest_seq)  # Increment seq number for RREP
            # If this node is the destination, increment its seq number before replying
            self.send_RREP(self.node_id, rreq.source_id, self.seq, 0, 0, network, verbose)
            return

        # Check if we have a "valid" route to the destination
        if rreq.dest_id in self.routing_table:
            route = self.routing_table[rreq.dest_id]
            if self.network.link_exists(self.node_id, route.next_hop) and (
                route.seq > rreq.dest_seq or
                (route.seq == rreq.dest_seq and route.cost < rreq.cost)
            ):
                # if route.next_hop != forwarder_id:
                    self.send_RREP(
                        rreq.dest_id, rreq.source_id,
                        route.seq, route.hops, route.cost,
                        network, verbose
                    )
                    return
            
        # If no valid route, forward the RREQ to neighbors
        if verbose:
            print(f"Node {self.node_id}: Forwarding RREQ: [{rreq}] to neighbors")
        
        self.forward_RREQ(rreq, network, forwarder_id, verbose)

            
    def send_RREP(self, source_id, dest_id, seq, hops, cost, network, verbose=False):
        """
        Send a unicast Route Reply (RREP) back to the originator of the RREQ.
        source_id: the original destination of the RREQ (i.e., this node or known destination)
        dest_id: the originator of the RREQ (i.e., who we’re sending the RREP to)
        """
        rrep = RREP(source_id, dest_id, seq, hops, cost)
        self.msg_stats['rrep_sent'] += 1
        if verbose:
            print(f"Node {self.node_id}: Sending RREP: [{rrep}] to {dest_id} from {source_id} with hops {hops}")
        # Lookup next hop to the RREQ originator
        if dest_id in self.routing_table:
            next_hop = self.routing_table[dest_id].next_hop
            # next_hop, _, _ = self.routing_table[dest_id]

            next_node = network.get_node_by_id(next_hop)
            next_node.receive_RREP(rrep, network, self.node_id, verbose)
        else:
            # No route back to the originator, drop the packet (or log error)
            if verbose:
                print(f"Node {self.node_id}: No route to RREQ originator {dest_id}, cannot send RREP")


    def receive_RREP(self, rrep, network, forwarder_id, verbose=False):
        """Receive a Route Reply (RREP) and update routing table."""
        if verbose:
            print(f"Node {self.node_id}: received RREP: [{rrep}] from {forwarder_id} for destination {rrep.dest_id}")
        
        self.msg_stats['rrep_recv'] += 1
        # Update route to the RREP originator (the final destination of the RREQ)
        rrep.hops += 1
        rrep.cost += network.get_link_cost(self.node_id, forwarder_id)
        # new_route = (forwarder_id, rrep.hops, rrep.seq)
        new_route = RoutingTableEntry(rrep.source_id, forwarder_id, rrep.dest_seq, rrep.hops, rrep.cost)

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
        entries = [f"{dest_id}: ({entry.next_hop}, [{entry.hops}, {entry.cost}],{entry.seq})" for dest_id, entry in self.routing_table.items()]
        routing_table_str = f"Node {self.node_id} Routing Table: {' | '.join(entries)}"
        print(routing_table_str)
        return routing_table_str
