import math
import random
import copy

class SensorNode:
    """A node in a wireless sensor network with position and connection capabilities."""
    
    _all_nodes = []  # Keep track of all nodes in the network
    
    def __init__(self, node_id, x=0, y=0, transmission_range=1.0, network=None):
        """Initialize a sensor node.
        
        Args:
            node_id: Unique identifier for the node
            x, y: Position coordinates
            transmission_range: Maximum distance the node can transmit
        """
        self.node_id = node_id
        self.x = x
        self.y = y
        self.transmission_range = transmission_range
        self.connections = {}  # {neighbor_node_id: delay}
        self.route_discovery_msg_count = 0  # Count of control packets for route discovery
        self.network = network  # Reference to the network this node belongs to
        SensorNode._all_nodes.append(self)


    def distance_to(self, other_node):
        """Calculate Euclidean distance to another node."""
        return math.sqrt((self.x - other_node.x)**2 + (self.y - other_node.y)**2)
    
    def can_reach(self, other_node):
        """Check if this node can reach another node based on distance and range."""
        if self is other_node:
            return False
        return self.distance_to(other_node) <= self.transmission_range
    
    def add_connection(self, other_node_id, delay):
        """Add a connection to another node with specified delay."""
        self.connections[other_node_id] = delay
        self.update_needed = True
        
    def get_neighbors(self):
        """Return a list of neighbor node IDs."""
        return list(self.connections.keys())
    
    def reset(self):
        """Reset the node's state."""
        self.seq = 0
        self.routing_table.clear()
        self.broadcast_id = 0
        self.seen_rreqs.clear()
        self.received_msgs.clear()
        
    def __str__(self):
        return f"Node {self.node_id} at ({self.x:.2f}, {self.y:.2f}) with {len(self.connections)} connections"
    
    @classmethod
    def get_all_nodes():
        """Return all nodes in the network."""
        return SensorNode._all_nodes


