
import random, argparse, time
from src.core.network import SensorNetwork
from src.visualization.visualization import (
    visualize_network_matplotlib,
    visualize_network
)

def run_dynamic_scenario(network, n_nodes, time_steps=20, p_request=0.5, p_fail=0.5, p_new=0.8, delay_between_steps=0.5, verbose=False):
# Run simulation with aodv protocol
    if verbose:
        print(f"Running dynamic scenario with {n_nodes} nodes...")
    for t in range(time_steps):
    # for t in range(5):
        # visualize_network(network)

        for node in network.nodes:
            node.print_routing_table()
        step_events = {"step": t+1, "events": []}

        #___________________________________________________________________________________________________________________________________________________-

        #this is fine

        if random.random() < p_request:
            # Randomly select source and destination nodes
            source_id = random.randint(0, n_nodes-1)
            dest_id = random.randint(0, n_nodes-1)
            while dest_id == source_id:
                dest_id = random.randint(0, n_nodes-1)
            print(f"[Step {t}] Simulating data packet between Node {source_id} and Node {dest_id}")

            path, nHops = network.simulate_message_transmission(
                source_node=network.nodes[source_id],
                target_node=network.nodes[dest_id],
                message=f"Hi from Node {source_id} to Node {dest_id}",
                verbose=verbose
            )
            print(f"Path found: {' -> '.join(map(str, path))}")
            print(f"Total transmission delay: {nHops} units")
            
        #___________________________________________________________________________________________________________________________________________________-

        # Fine after routing table adjustments

        if random.random() < p_fail and len(network.get_all_links()) > 0:
            # Randomly select a link to remove
            links = network.get_all_links()
            if links:
                node_a_id, node_b_id, _ = random.choice(links)
                print(f"[Step {t}] Trying Link failure: Connection between Node {node_a_id} and Node {node_b_id} disappeared")
                # Remove the link
                network.remove_link(node_a_id, node_b_id)
                # stats["links_removed"] += 1
                step_events["events"].append(f"Link removed: {node_a_id}-{node_b_id}")

        #___________________________________________________________________________________________________________________________________________________-

        # Fine but some routes are suboptimal
        
        if random.random() < p_new:
            # Randomly select two unconnected nodes to create a new link
            

            unconnected_pairs = network.get_unconnected_pairs()
            if not unconnected_pairs:
                print(f"[Step {t}] No unconnected pairs available to create a new link.")
                continue

            delay = random.uniform(0.1, 1.0)
            node_a_id, node_b_id = random.choice(unconnected_pairs)
            # Add the link
            print(f"[Step {t}] Trying New link: Connection established between Node {node_a_id} and Node {node_b_id} with delay {delay:.4f}")
            network.add_link(node_a_id, node_b_id, delay=delay)
            
            network.get_node_by_id(node_a_id).discover_neighbors(network, verbose=False)
            # print(f"Node {node_a_id} neighbors after discovery: {network.get_node_by_id(node_a_id).routing_table}")
            # print(f"Node {node_b_id} neighbors after discovery: {network.get_node_by_id(node_b_id).routing_table}")
            # stats["links_added"] += 1
            # stats["reconvergence_iterations"] += iterations
            step_events["events"].append(f"Link added: {node_a_id}-{node_b_id}")
        
        #___________________________________________________________________________________________________________________________________________________-
            # Add delay between steps
        # if t < time_steps - 1 and delay_between_steps > 0:
        #     time.sleep(delay_between_steps)

def main(args):
    n_nodes = int(args.n)
    verbose=args.v
    # seed = args.seed
    seed = int(time.time())
    # seed = 1750940548 # error in update aggiunto >= in seq number so below code is unreachable
    # seed = 1750942460 #error the packet is looping in triangle
    
    print("Random seed:", seed)

    # Create a random sensor network
    network = SensorNetwork()

    network.create_random_network(n_nodes, seed=seed, area_size=10)

    visualize_network(network)

    network.neighbor_discovery(verbose=False)
    #print the routing table of each node


    run_dynamic_scenario(
        network=network,
        n_nodes=n_nodes,
        time_steps=10,
        p_request=0.5,
        p_fail=0.1,
        p_new=0.1,
        delay_between_steps=0.5,
        verbose=verbose
    )



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', required=False, default=10, type=int)
    parser.add_argument('-v', required=False, default=False, action='store_true', help="Enable verbose output")
    parser.add_argument('--seed', required=False, default=None, type=int, help="Random seed for reproducibility")
    args = parser.parse_args()

    main(args)
    exit(0)

    
