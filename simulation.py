
import random, argparse, time
from src.core.network import SensorNetwork
from src.visualization.visualization import (
    visualize_network_matplotlib,
    visualize_network
)

def run_dynamic_scenario(network, n_nodes, time_steps=20, p_request=0.3, p_fail=0.1, p_new=0.1, delay_between_steps=0.5, verbose=False):
# Run simulation with aodv protocol
    if verbose:
        print(f"Running dynamic scenario with {n_nodes} nodes...")
    for t in range(time_steps):
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

            path, nHops, cost = network.simulate_message_transmission(
                source_node=network.nodes[source_id],
                target_node=network.nodes[dest_id],
                message=f"Hi from Node {source_id} to Node {dest_id}",
                verbose=verbose
            )
            if cost:
                print(f"Path found: {' -> '.join(map(str, path))}")
                print(f"Total transmission delay: {nHops}, {cost:3f} units\n")
            else:
                print(f"No path found from Node {source_id} to Node {dest_id}\n")
        #___________________________________________________________________________________________________________________________________________________-

        if random.random() < p_fail and len(network.get_all_links()) > 0:
            # Randomly select a link to remove
            links = network.get_all_links()
            if links:
                node_a_id, node_b_id, _ = random.choice(links)
                print(f"[Step {t}] Trying Link failure: Connection between Node {node_a_id} and Node {node_b_id} disappeared\n")
                # Remove the link
                network.remove_link(node_a_id, node_b_id)
                # stats["links_removed"] += 1
                # visualize_network_matplotlib(network, title="step {t+1} - Link Down")

                step_events["events"].append(f"Link removed: {node_a_id}-{node_b_id}")

        #___________________________________________________________________________________________________________________________________________________-

        if random.random() < p_new:
            

            # Randomly select two unconnected nodes to create a new link
            unconnected_pairs = network.get_unconnected_pairs()
            if not unconnected_pairs:
                print(f"[Step {t}] No unconnected pairs available to create a new link.")
                continue

            delay = random.uniform(0.1, 1.0)
            node_a_id, node_b_id = random.choice(unconnected_pairs)
            # Add the link
            print(f"[Step {t}] Trying New link: Connection established between Node {node_a_id} and Node {node_b_id} with delay {delay:.4f}\n")
            network.add_link(node_a_id, node_b_id, delay=delay)
            # visualize_network_matplotlib(network, title="step {t+1} - New Link Added")
            
            network.get_node_by_id(node_a_id).discover_neighbors(network, verbose=False)
            
            step_events["events"].append(f"Link added: {node_a_id}-{node_b_id}")
        
        #___________________________________________________________________________________________________________________________________________________-
        
        
        # visualize_network(network, title=f"Dynamic Scenario - Step {t+1}")
        # input("Press Enter to continue to the next step...")
        # if t < time_steps - 1 and delay_between_steps > 0:
        #     time.sleep(delay_between_steps)

    total_exchanged_messages = sum( sum( tot for tot in node.msg_stats.values()) for node in network.nodes)
    print("Total exchanged messages:", total_exchanged_messages)

    network.print_stats_compact()



def main(args):
    n_nodes = int(args.n)
    verbose=args.v
    seed = args.seed
    time_steps = int(args.t)
    # seed = 1751548377
    print("Random seed:", seed)
    

    # Create a random sensor network
    network = SensorNetwork()
    network.create_random_network(n_nodes, seed=seed, area_size=10)
    visualize_network(network)

    # network.neighbor_discovery(verbose=False)

    run_dynamic_scenario(
        network=network,
        n_nodes=n_nodes,
        time_steps=time_steps,
        p_request=0.3,
        p_fail=0.2,
        p_new=0.1,
        delay_between_steps=0.5,
        verbose=verbose
    )



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', required=False, default=10, type=int)
    parser.add_argument('-t', required=False, default=25, type=int)
    parser.add_argument('-v', required=False, default=False, action='store_true', help="Enable verbose output")
    parser.add_argument('--seed', required=False, default=int(time.time()), type=int, help="Random seed for reproducibility")
    args = parser.parse_args()

    main(args)
    exit(0)

    
