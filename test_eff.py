
probs = [x / 100.0 for x in range(10, 40, 10)]

def gen_csv():

	file = open("file.csv", 'w')
	for nodes in range(10, 50, 20):
		for time_steps in [30, 60, 100, 1000]:
			for pfail in probs:
				for pnew in probs:
					for req in [15,35,65,85,100]:
						preq = req/100
						line = f"{nodes},{time_steps},{pfail},{pnew},{preq}\n"
						file.write(line)

import csv

def load_csv(filename="file.csv"):
    params = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            # row is a list of strings, convert to numbers as needed
            nodes = int(row[0])
            time_steps = int(row[1])
            pfail = float(row[2])
            pnew = float(row[3])
            preq = float(row[4])
            
            # store in a tuple (or list if you prefer)
            params.append((nodes, time_steps, pfail, pnew, preq))
    return params


gen_csv()

load_csv()
import subprocess

def run_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

all_params = load_csv()

output_file = open("results_efficiency.txt", "w")

for line in all_params:
    progress = all_params.index(line)/len(all_params)*100
    print(f"Progress: {progress:.2f}%", end="\r")
    cmd = f"python3 simulation.py -n {line[0]} -t {line[1]} --seed 1 -pf {line[2]} -pn {line[3]} -pr {line[4]} 2>/dev/null | tail -n 5"
    output = run_cmd(cmd)
    output_file.write(f"{line},{output.replace(',', ';')}")
    output_file.flush()
	
