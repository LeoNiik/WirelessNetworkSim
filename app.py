import streamlit as st
import random, os, time
import imageio

from src.core.network import SensorNetwork
# Usa esplicitamente l'implementazione Matplotlib per evitare ombre/import sbagliati
from src.visualization.visualization import visualize_network_matplotlib as visualize_network

# --- CONFIG PAGINA ---
st.set_page_config(
    page_title="Sensor Network Simulation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR ---
st.sidebar.header("Simulation Parameters")
n_nodes = st.sidebar.number_input("Number of nodes", 2, 100, 10)
steps   = st.sidebar.number_input("Time steps",     1, 100, 10)
p_req   = st.sidebar.slider("P Request", 0.0, 1.0, 0.5)
p_fail  = st.sidebar.slider("P Fail",    0.0, 1.0, 0.1)
p_new   = st.sidebar.slider("P New Link",0.0, 1.0, 0.1)
seed    = st.sidebar.number_input("Random seed", value=int(time.time()))

OUTPUT_DIR = os.path.join(os.getcwd(), "output", "visualizations")
VIDEO_PATH = os.path.join(os.getcwd(), "output", "simulation.mp4")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- GENERA TUTTI GLI STEP ---
def generate_all_steps(net, n_nodes, time_steps, p_req, p_fail, p_new):
    lst = []
    for t in range(time_steps):
        events = []

        # PACKET
        if random.random() < p_req:
            src = random.randrange(n_nodes)
            dst = src
            while dst == src:
                dst = random.randrange(n_nodes)

            result = net.simulate_message_transmission(
                source_node=net.nodes[src],
                target_node=net.nodes[dst],
                message=f"Hi from Node {src} to Node {dst}"
            )

            # Controlla se result è una tupla (path, hops) oppure solo hops
            if result is None:
                events.append(f"Packet {src}->{dst} failed (no route)")
            elif isinstance(result, tuple) and len(result) == 2:
                path, hops = result
                events.append(f"Packet {src}->{dst}, hops: {hops}, path: {path}")
            elif isinstance(result, int):
                hops = result
                events.append(f"Packet {src}->{dst}, hops: {hops}")
            else:
                events.append(f"Packet {src}->{dst} sent (unknown format)")

        # LINK FALLITO
        if random.random() < p_fail and net.get_all_links():
            a, b, _ = random.choice(net.get_all_links())
            net.remove_link(a, b)
            events.append(f"Link removed: {a}-{b}")

        # NUOVO LINK
        if random.random() < p_new:
            pairs = net.get_unconnected_pairs()
            if pairs:
                a, b = random.choice(pairs)
                d = random.uniform(0.1, 1.0)
                net.add_link(a, b, delay=d)
                events.append(f"Link added: {a}-{b} (delay={d:.2f})")

        if not events:
            events = ["No events"]

        # SALVA IMMAGINE (usa posizionali per essere compatibile con firme diverse)
        img = os.path.join(OUTPUT_DIR, f"step_{t+1}.png")
        visualize_network(net, img, f"Step {t+1}")
        lst.append((t+1, events, img))
    return lst


# --- INIZIALIZZA session_state ---
for key in ("all_steps", "current_index", "network", "generated", "run_requested"):
    if key not in st.session_state:
        st.session_state[key] = (
            False if key in ("generated", "run_requested")
            else []   if key == "all_steps"
            else -1   if key == "current_index"
            else None
        )

# --- HEADER + BOTTONI ---
st.title("Step-by-Step Sensor Network Simulation")
c1, c2, c3, c4, _ = st.columns([5, 5, 5, 5, 20])

# Run imposta run_requested
run = c1.button("Run Simulation")
if run:
    if os.path.exists(VIDEO_PATH):
        os.remove(VIDEO_PATH)
    st.session_state.all_steps = []
    st.session_state.current_index = -1
    st.session_state.generated = False
    st.session_state.run_requested = True
    st.session_state.network = None

# Se mi era stato richiesto, genero alla successiva render
if st.session_state.run_requested and not st.session_state.generated:
    random.seed(seed)
    net = SensorNetwork()
    net.create_random_network(n_nodes, seed=seed, area_size=10)
    net.neighbor_discovery(verbose=False)
    st.session_state.all_steps = generate_all_steps(
        net, n_nodes, steps, p_req, p_fail, p_new
    )
    st.session_state.network = net
    st.session_state.current_index = -1
    st.session_state.generated = True
    st.session_state.run_requested = False

# Disabilita nav finché non ho generated
disabled_nav = not st.session_state.generated
prev     = c2.button("Previous Step", disabled=disabled_nav)
nxt      = c3.button("Next Step",     disabled=disabled_nav)
complete = c4.button("Complete Simulation", disabled=disabled_nav)

# --- NAV-LOGICA ---
if prev and st.session_state.current_index > 0:
    st.session_state.current_index -= 1

if nxt and st.session_state.current_index + 1 < len(st.session_state.all_steps):
    st.session_state.current_index += 1

if complete:
    st.session_state.current_index = len(st.session_state.all_steps) - 1

# --- COSTRUISCO LA HISTORY ---
history = []
for idx in range(st.session_state.current_index + 1):
    step, events, img = st.session_state.all_steps[idx]
    history.append({"step": step, "events": events, "image": img})
finished = (st.session_state.current_index + 1) == len(st.session_state.all_steps)

# --- DISPLAY LOG + IMMAGINE passo corrente ---
if history:
    left, right = st.columns([4.5, 4.5])
    with left:
        st.subheader("Logs")
        st.table([{"Step": h["step"], "Log": "\n".join(h["events"])} for h in history])
    with right:
        cur = history[-1]
        st.subheader(f"Network at Step {cur['step']}")
        st.image(cur["image"], use_container_width=True)

# --- FINE SIMULAZIONE: ADJ-LIST, VIDEO, BEFORE/AFTER ---
if finished and st.session_state.network:
    st.info("Simulation finished.")
    st.markdown("---")
    st.subheader("Adjacency List Representation")
    adj = {n.node_id: {} for n in st.session_state.network.nodes}
    for a, b, d in st.session_state.network.get_all_links():
        adj[a][b] = d
        adj[b][a] = d
    lines = []
    for nid in sorted(adj):
        parts = [f"{nbr} (delay: {adj[nid][nbr]:.2f})" for nbr in sorted(adj[nid])]
        lines.append(f"[{nid}]: {', '.join(parts)}")
    st.code("\n".join(lines), language=None)

    # --- STATISTICHE DELL'ESECUZIONE ---
    st.subheader("📊 Execution Statistics")

    total_stats = {
        "rreq_sent": 0, "rreq_recv": 0,
        "rrep_sent": 0, "rrep_recv": 0,
        "rerr_sent": 0, "rerr_recv": 0,
        "data_sent": 0, "data_recv": 0,
    }

    for node in st.session_state.network.nodes:
        for key in total_stats:
            total_stats[key] += node.msg_stats.get(key, 0)

    total_exchanged = sum(total_stats.values())
    total_useful = total_stats["data_recv"]
    efficiency = total_useful / total_exchanged if total_exchanged > 0 else 0

    # Mostra tabella
    st.table([
        {"Metric": "Total packets exchanged", "Value": total_exchanged},
        {"Metric": "Useful packets (data received)", "Value": total_useful},
        {"Metric": "Efficiency (useful / total)", "Value": f"{efficiency:.3f}"},
    ])

    with st.expander("📦 Detailed Message Counts per Type"):
        st.json(total_stats)

    # Bottone per generare e mostrare il video
    if st.button("Generate Video"):
        target_duration = 10.0  # secondi totali del video
        fps = max(1, int(len(history) / target_duration))  # calcolo FPS dinamico

        try:
            with imageio.get_writer(VIDEO_PATH, fps=fps, format='FFMPEG') as w:
                for h in history:
                    frame = imageio.imread(h["image"])
                    w.append_data(frame)
            st.success(f"Video generated at {fps} FPS (~{target_duration:.0f}s)")
        except Exception:
            st.error("Installare il backend FFMPEG: `pip install imageio[ffmpeg]`")

        # Mostra video e BEFORE / AFTER
        col_vid, col_before, col_after = st.columns([5, 3, 3])
        with col_vid:
            st.video(VIDEO_PATH, width=600)
        with col_before:
            st.markdown("**BEFORE**")
            first_img = st.session_state.all_steps[0][2]
            st.image(first_img, use_container_width=True)
        with col_after:
            st.markdown("**AFTER**")
            last_img = st.session_state.all_steps[-1][2]
            st.image(last_img, use_container_width=True)
