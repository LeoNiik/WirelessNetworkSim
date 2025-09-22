probs = [x / 100.0 for x in range(10, 40, 10)]

def gen_csv():
    with open("file.csv", 'w') as file:
        for nodes in range(10, 50, 20):
            for time_steps in [30, 60, 100, 1000]:
                for pfail in probs:
                    for pnew in probs:
                        for req in [15, 35, 65, 85, 100]:
                            preq = req / 100
                            # aggiungo una colonna "efficiency" vuota (da calcolare dopo)
                            line = f"{nodes},{time_steps},{pfail},{pnew},{preq},efficiency\n"
                            file.write(line)

import csv

def load_csv(filename="file.csv"):
    params = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            nodes = int(row[0])
            time_steps = int(row[1])
            pfail = float(row[2])
            pnew = float(row[3])
            preq = float(row[4])
            # efficiency è una stringa placeholder per ora
            efficiency = row[5]
            params.append((nodes, time_steps, pfail, pnew, preq, efficiency))
    return params


gen_csv()

import subprocess

def run_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

all_params = load_csv()

with open("results_efficiency.txt", "w") as output_file:
    for idx, line in enumerate(all_params):
        progress = idx / len(all_params) * 100
        print(f"Progress: {progress:.2f}%", end="\r")
        cmd = f"python3 simulation.py -n {line[0]} -t {line[1]} --seed 1 -pf {line[2]} -pn {line[3]} -pr {line[4]} 2>/dev/null | tail -n 5"
        output = run_cmd(cmd)
        
        # Scrivo la riga con efficiency come ultima colonna + newline
        output_file.write(f"{line},{output.replace(',', ';')}\n")
        output_file.flush()
