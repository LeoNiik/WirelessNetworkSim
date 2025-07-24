from src.core.aodv_node import aodv_node as Node
from src.core.aodv import RoutingTableEntry
import random, copy
from tabulate import tabulate
from collections import deque

import time

class SensorNetwork:
    """A wireless sensor network consisting of nodes with weighted connections."""
    
    def __init__(self):
        """Initialize an empty sensor network."""
        self.nodes = []
        self.queue = deque()
        
    def add_node(self, node):
        """Add a node to the network."""
        self.nodes.append(node)
        return node

        
    def create_random_network(self, n, seed=None, area_size=10, min_range=1.0, max_range=3.0):
        """Create a network with n nodes randomly positioned with random transmission ranges.
        
        The network created will have the following properties:
        1. No isolated nodes: Every node will have at least one connection
        2. Fully connected: There will be a path between any two nodes
        
        Args:
            n: Number of nodes
            area_size: Size of the square area
            min_range, max_range: Min/max transmission range for nodes
            
        Returns:
            List of created nodes
        """
        #change the seed for reproducibility
        if seed is not None:
            random.seed(seed)

        self.nodes = []
        # Reset the class-level node tracking
        Node._all_nodes = []
        
        for i in range(n):
            x = random.uniform(0, area_size)
            y = random.uniform(0, area_size)
            transmission_range = random.uniform(min_range, max_range)
            node = Node(node_id=i, x=x, y=y, transmission_range=transmission_range, network=self)
            self.nodes.append(node)
            
        # Generate weighted connections
        self._generate_connections()
        return self.nodes


    def _generate_connections(self):
        """Generate bidirectional weighted connections between nodes that can reach each other."""
        n = len(self.nodes)
        for i in range(n):
            for j in range(i + 1, n):
                node_a = self.nodes[i]
                node_b = self.nodes[j]
                if node_a.can_reach(node_b) or node_b.can_reach(node_a):
                    delay = random.uniform(0, 1)
                    node_a.add_connection(node_b.node_id, delay)
                    node_b.add_connection(node_a.node_id, delay)
        
        # Ensure no isolated nodes (nodes without connections)
        self._ensure_no_isolated_nodes()
        
        # Ensure the network is fully connected (any node can reach any other)
        self._ensure_fully_connected_network()


    def _ensure_no_isolated_nodes(self):
        """Ensure that every node has at least one connection."""
        isolated_nodes = []
        
        # Find all isolated nodes
        for node in self.nodes:
            if len(node.connections) == 0:
                isolated_nodes.append(node)
        
        if not isolated_nodes:
            return  # No isolated nodes, nothing to do
            
        print(f"Found {len(isolated_nodes)} isolated nodes, connecting them to the network...")
        
        # For each isolated node, find the closest non-isolated node and connect them
        for isolated_node in isolated_nodes:
            closest_node = None
            min_distance = float('inf')
            
            # Find the closest non-isolated node
            for other_node in self.nodes:
                if other_node is isolated_node or other_node in isolated_nodes:
                    continue  # Skip self and other isolated nodes
                    
                distance = isolated_node.distance_to(other_node)
                if distance < min_distance:
                    min_distance = distance
                    closest_node = other_node
            
            # If there are no non-isolated nodes (all nodes are isolated),
            # connect to another isolated node instead
            if closest_node is None and len(isolated_nodes) > 1:
                for other_node in isolated_nodes:
                    if other_node is isolated_node:
                        continue
                        
                    distance = isolated_node.distance_to(other_node)
                    if distance < min_distance:
                        min_distance = distance
                        closest_node = other_node
            
            # If we found a node to connect to, create a bidirectional connection
            if closest_node is not None:
                # Increase the transmission range of both nodes to reach each other
                distance = isolated_node.distance_to(closest_node)
                isolated_node.transmission_range = max(isolated_node.transmission_range, distance * 1.1)
                closest_node.transmission_range = max(closest_node.transmission_range, distance * 1.1)
                
                # Create the connection with a random delay
                delay = random.uniform(0, 1)
                isolated_node.add_connection(closest_node.node_id, delay)
                closest_node.add_connection(isolated_node.node_id, delay)
                
                print(f"Connected isolated Node {isolated_node.node_id} to Node {closest_node.node_id} (distance: {distance:.2f})")
            else:
                print(f"Warning: Could not find a suitable connection for Node {isolated_node.node_id}")
        
        # Recursively check again in case there are still isolated nodes
        # (This could happen in edge cases where all nodes were initially isolated)
        still_isolated = [node for node in self.nodes if len(node.connections) == 0]
        if still_isolated:
            print(f"There are still {len(still_isolated)} isolated nodes, attempting to connect them...")
            self._ensure_no_isolated_nodes()


    def _is_network_fully_connected(self):
        """Check if the network is fully connected (any node can reach any other node).
        
        Returns:
            bool: True if the network is fully connected, False otherwise
        """
        if not self.nodes:
            return True  # Empty network is considered connected
            
        # Use breadth-first search to check connectivity
        n = len(self.nodes)
        visited = set()
        
        # Start BFS from the first node
        queue = [0]  # Start with node 0
        visited.add(0)
        
        while queue:
            current = queue.pop(0)
            current_node = self.nodes[current]
            
            for neighbor_id in current_node.connections.keys():
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(neighbor_id)
        
        # If all nodes are visited, the network is fully connected
        return len(visited) == n


    def _ensure_fully_connected_network(self):
        """Ensure the network is fully connected by identifying disconnected components
        and adding links between them.
        """
        if self._is_network_fully_connected():
            return  # Network is already fully connected
            
        print("Network is not fully connected. Identifying disconnected components...")
        
        # Identify all connected components using DFS
        n = len(self.nodes)
        components = []
        visited = set()
        
        for i in range(n):
            if i in visited:
                continue
                
            # Find a new component
            component = set()
            stack = [i]
            
            while stack:
                current = stack.pop()
                if current in component:
                    continue
                    
                component.add(current)
                visited.add(current)
                current_node = self.nodes[current]
                
                for neighbor_id in current_node.connections.keys():
                    if neighbor_id not in component:
                        stack.append(neighbor_id)
            
            components.append(component)
        
        print(f"Found {len(components)} disconnected components in the network")
        
        # Connect each component to the next one
        for i in range(len(components) - 1):
            # Find the closest pair of nodes between components i and i+1
            closest_pair = None
            min_distance = float('inf')
            
            for node_id_1 in components[i]:
                for node_id_2 in components[i + 1]:
                    node_1 = self.nodes[node_id_1]
                    node_2 = self.nodes[node_id_2]
                    distance = node_1.distance_to(node_2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_pair = (node_id_1, node_id_2)
            
            if closest_pair:
                node_1_id, node_2_id = closest_pair
                node_1 = self.nodes[node_1_id]
                node_2 = self.nodes[node_2_id]
                
                # Increase transmission range if needed
                distance = node_1.distance_to(node_2)
                node_1.transmission_range = max(node_1.transmission_range, distance * 1.1)
                node_2.transmission_range = max(node_2.transmission_range, distance * 1.1)
                
                # Create a bidirectional connection
                delay = random.uniform(0, 1)
                node_1.add_connection(node_2_id, delay)
                node_2.add_connection(node_1_id, delay)
                
                print(f"Connected component {i} to component {i+1} by linking Node {node_1_id} to Node {node_2_id} (distance: {distance:.2f})")
        
        # Verify that the network is now fully connected
        if not self._is_network_fully_connected():
            print("Warning: Network is still not fully connected after attempting to connect components")
            # Try again with a more aggressive approach
            self._connect_all_components()


    def _connect_all_components(self):
        """A more aggressive approach to connect all components by connecting each
        component to all other components.
        """
        print("Using more aggressive approach to connect all components...")
        
        # Identify all connected components using DFS
        n = len(self.nodes)
        components = []
        visited = set()
        
        for i in range(n):
            if i in visited:
                continue
                
            # Find a new component
            component = set()
            stack = [i]
            
            while stack:
                current = stack.pop()
                if current in component:
                    continue
                    
                component.add(current)
                visited.add(current)
                current_node = self.nodes[current]
                
                for neighbor_id in current_node.connections.keys():
                    if neighbor_id not in component:
                        stack.append(neighbor_id)
            
            components.append(component)
        
        # For each pair of components, connect the closest nodes
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                # Find the closest pair of nodes between components i and j
                closest_pair = None
                min_distance = float('inf')
                
                for node_id_1 in components[i]:
                    for node_id_2 in components[j]:
                        node_1 = self.nodes[node_id_1]
                        node_2 = self.nodes[node_id_2]
                        distance = node_1.distance_to(node_2)
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_pair = (node_id_1, node_id_2)
                
                if closest_pair:
                    node_1_id, node_2_id = closest_pair
                    node_1 = self.nodes[node_1_id]
                    node_2 = self.nodes[node_2_id]
                    
                    # Increase transmission range if needed
                    distance = node_1.distance_to(node_2)
                    node_1.transmission_range = max(node_1.transmission_range, distance * 1.1)
                    node_2.transmission_range = max(node_2.transmission_range, distance * 1.1)
                    
                    # Create a bidirectional connection
                    delay = random.uniform(0, 1)
                    node_1.add_connection(node_2_id, delay)
                    node_2.add_connection(node_1_id, delay)
                    
                    print(f"Connected component {i} to component {j} by linking Node {node_1_id} to Node {node_2_id} (distance: {distance:.2f})")
        
        # Final check
        if not self._is_network_fully_connected():
            print("Warning: Network is still not fully connected after aggressive connection attempt")
        else:
            print("Network is now fully connected")


    def get_adjacency_matrix(self):
        """Return the adjacency matrix with delays as weights."""
        n = len(self.nodes)
        matrix = [[float('inf') for _ in range(n)] for _ in range(n)]
        
        # Fill in weights where connections exist
        for i, node in enumerate(self.nodes):
            matrix[i][i] = 0  # Set diagonal to 0
            for other_node_id, delay in node.connections.items():
                matrix[i][other_node_id] = delay
                
        return matrix


    def get_node_by_id(self, node_id):
        """Return node with given ID."""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None
    

    def get_link_cost(self, node_a_id, node_b_id):
        """Get the cost (delay) of the link between two nodes."""
        node_a = self.get_node_by_id(node_a_id)
        node_b = self.get_node_by_id(node_b_id)
        
        if node_a is None or node_b is None:
            return float('inf')
        if node_b_id in node_a.connections:
            return node_a.connections[node_b_id]
        if node_a_id in node_b.connections:
            return node_b.connections[node_a_id]
        return float('inf')  # No link exists between these nodes
        

    def route_discovery(self, src_id, dst_id,verbose=False):


        src_node = self.get_node_by_id(src_id)
        src_node.broadcast_RREQ(self, dst_id)

        while self.queue:
            
            current_node, current_rreq, forwarder_id = self.queue.popleft()
            current_node.receive_RREQ(self, current_rreq, forwarder_id, verbose=verbose)


    def get_all_links(self):
        """Return a list of all links in the network as (node_a_id, node_b_id, delay) tuples."""
        links = []
        for i, node in enumerate(self.nodes):
            for neighbor_id, delay in node.connections.items():                # Only add each link once (when i < neighbor_id)
                if i < neighbor_id:
                    links.append((i, neighbor_id, delay))
        return links


    def get_message_counter_totals(self):
        """Calculate total message counts across all nodes in the network.
        
        Returns:
            Dictionary with totals for each message type and a grand total
        """
        totals = {
            "hello_msg_count": 0,
            "topology_msg_count": 0,
            "route_discovery_msg_count": 0,
            "data_packet_count": 0
        }
        
        for node in self.nodes:
            totals["hello_msg_count"] += node.hello_msg_count
            totals["topology_msg_count"] += node.topology_msg_count
            totals["route_discovery_msg_count"] += node.route_discovery_msg_count
            totals["data_packet_count"] += node.data_packet_count
            
        totals["total_messages"] = (totals["hello_msg_count"] + 
                                   totals["topology_msg_count"] + 
                                   totals["route_discovery_msg_count"] + 
                                   totals["data_packet_count"])
        
        return totals
    

    def get_unconnected_pairs(self):
        unconnected_pairs = []
        for i in range(len(self.nodes)):
            for j in range(i+1, len(self.nodes)):
                if j not in self.nodes[i].connections:
                    # Check if they're within range
                    node_a = self.nodes[i]
                    node_b = self.nodes[j]
                    if node_a.can_reach(node_b) or node_b.can_reach(node_a):
                        unconnected_pairs.append((i, j))
        return unconnected_pairs


    def neighbor_discovery(self, verbose=False):
        """
        Perform active route discovery to known neighbors using AODV RREQs,
        allowing RREPs to populate the routing table safely.
        """
        for node in self.nodes:
            node.discover_neighbors(self, verbose=verbose)


    def simulate_message_transmission(self, source_node, target_node, message="Test message", verbose=False):
        """Simulate sending a message from source to target using current routing tables.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            message: Message content to be sent
            verbose: Print detailed information during transmission
            
        Returns:
            Tuple containing the path found and the total delay, or None if no path exists
        """
        if source_node.can_send(target_node):
            nHops, path, delay = source_node.send_MSG(target_node.node_id, message, self, verbose=verbose)
            return path, nHops, delay
        if verbose:
            print(f"Node {source_node.node_id} cannot send message to Node {target_node.node_id}: No route found, initiating route discovery...")
        
        self.route_discovery(source_node.node_id, target_node.node_id, verbose=verbose)
        
        # After route discovery, try sending the message again
        if source_node.can_send(target_node):
            nHops, path, delay = source_node.send_MSG(target_node.node_id, message, self, verbose=verbose)
            return path, nHops, delay
        else:
            if verbose:
                print(f"Node {source_node.node_id} could not send message to Node {target_node.node_id}: No route found")
            return None, None, None


    def print_stats_table(self, page_size=10):
        """Print statistics for all nodes in the network in a paginated format."""
        if not self.nodes:
            print("No nodes in the network.")
            return

        
        print("\n=== Network Statistics ===")
        print(f"Total Nodes: {len(self.nodes)}")
        
        # Prepare table headers and rows
        headers = ['Node ID', 'RREQ Sent', 'RREQ Recv', 'RREP Sent', 'RREP Recv', 'Data Sent', 'Data Recv']
        all_rows = []

        for node in self.nodes:
            s = node.msg_stats
            all_rows.append([
                node.node_id,
                s['rreq_sent'], s['rreq_recv'],
                s['rrep_sent'], s['rrep_recv'],
                s['data_sent'], s['data_recv']
            ])

        for i in range(0, len(all_rows), page_size):
            print(f"\n=== Page {i // page_size + 1} ===")
            print(tabulate(all_rows[i:i+page_size], headers=headers, tablefmt='grid'))


    def print_stats_compact(self):
        headers = ['Node ID', 'Route Discovery Sent', 'Route Discovery Recv', 'Data Sent', 'Data Recv']
        rows = []

        for node in self.nodes:
            s = node.msg_stats
            discovery_sent = s['rreq_sent'] + s['rrep_sent']
            discovery_recv = s['rreq_recv'] + s['rrep_recv']
            rows.append([
                node.node_id,
                discovery_sent,
                discovery_recv,
                s['data_sent'],
                s['data_recv']
            ])

        print(tabulate(rows, headers=headers, tablefmt='grid'))


    def _find_shortest_path(self, source_id, target_id):
        """Find shortest path between nodes using Dijkstra's algorithm."""
        n = len(self.nodes)
        distances = {i: float('inf') for i in range(n)}
        distances[source_id] = 0
        predecessors = {i: None for i in range(n)}
        unvisited = set(range(n))
        
        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            
            if current == target_id:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = predecessors[current]
                path.reverse()
                return path, distances[target_id]
                
            if distances[current] == float('inf'):
                break
                
            unvisited.remove(current)
            current_node = self.get_node_by_id(current)
            
            for neighbor_id, delay in current_node.connections.items():
                if neighbor_id in unvisited:
                    new_distance = distances[current] + delay
                    if new_distance < distances[neighbor_id]:
                        distances[neighbor_id] = new_distance
                        predecessors[neighbor_id] = current
        
        return None, float('inf')
    
    
    def add_link(self, node_a_id, node_b_id, delay, verbose=False):
        """Add a new link between two nodes with a specified delay.
        
        Args:
            node_a_id: ID of the first node
            node_b_id: ID of the second node
            delay: Delay for the new link
            verbose: Print detailed information during link addition
        """
        if verbose:
            print(f"\nAdding link between Node {node_a_id} and Node {node_b_id} with delay {delay:.4f}")
        
        node_a = self.get_node_by_id(node_a_id)
        node_b = self.get_node_by_id(node_b_id)
        
        node_a.connections[node_b_id] = delay
        node_b.connections[node_a_id] = delay
        node_a.update_needed = True
        node_b.update_needed = True


    def remove_link(self, node_a_id, node_b_id, verbose=False):
        """Remove a link between two nodes.
        
        Args:
            node_a_id: ID of the first node
            node_b_id: ID of the second node
            verbose: Print detailed information during link removal
        """
        if verbose:
            print(f"\nRemoving link between Node {node_a_id} and Node {node_b_id}")
        
        node_a = self.get_node_by_id(node_a_id)
        node_b = self.get_node_by_id(node_b_id)
        
        # Remove the connection
        if node_b_id in node_a.connections:
            del node_a.connections[node_b_id]
            node_a.update_needed = True
        if node_a_id in node_b.connections:
            del node_b.connections[node_a_id]
            node_b.update_needed = True
            
        # After removal, check connectivity and create a bridge if needed
        if not self._is_network_fully_connected():
            if verbose:
                print("Network is disconnected after link removal. Creating bridge link to restore connectivity.")
            self._ensure_fully_connected_network()
        

    def invalidate_routes(self, broken_link):
        node1_id, node2_id = broken_link
        for node in self.nodes:
            to_remove = []
            for dest_id, (next_hop, hops, _) in node.routing_table.items():
                if next_hop == node1_id or next_hop == node2_id:
                    to_remove.append(dest_id)
            for dest_id in to_remove:
                del node.routing_table[dest_id]
                print(f"Node {node.node_id}: Removed route to {dest_id} due to broken link")


    def link_exists(self, node_a_id, node_b_id):
        """Check if a link exists between two nodes."""
        node_a = self.get_node_by_id(node_a_id)
        node_b = self.get_node_by_id(node_b_id)
        
        if node_a is None or node_b is None:
            return False
            
        return node_b_id in node_a.connections and node_a_id in node_b.connections

