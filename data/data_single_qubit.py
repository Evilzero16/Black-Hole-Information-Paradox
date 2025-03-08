from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit import transpile
import numpy as np
import pandas as pd
from fractions import Fraction
import ast

def prepare_state(state, theta=None):
    circuit = QuantumCircuit(1, 1)
    if state == '0':
        pass
    elif state == "1":
        circuit.x(0)
    elif state == '+':
        circuit.h(0)
    elif state == '-':
        circuit.h(0)
        circuit.z(0)
    elif state == "ry":
        if theta is None:
            theta = np.pi / 2
        circuit.ry(theta, 0)
    circuit.measure(0, 0)
    return circuit

states = ["0", '1', '+', '-', 'ry']
ry_theta = [0, np.pi/6, np.pi / 4, np.pi / 3, np.pi / 2]

simulator = Aer.get_backend("qasm_simulator")

data = []

for state in states:
    if state == "ry":
        for theta in ry_theta:
            qc = prepare_state(state, theta)
            result = simulator.run((transpile(qc, simulator)), shots=1000).result()
            counts = result.get_counts()
            theta_frac = Fraction(theta / np.pi).limit_denominator(100)
            theta_str = f"π/{theta_frac.denominator}" if theta_frac.numerator != 0.0 else '0'

            data.append({"State" : state, "Theta": theta_str, "Counts": counts})
    else:
        qc = prepare_state(state)
        result = simulator.run((transpile(qc, simulator)), shots=1000).result()
        counts = result.get_counts()

        data.append({"State": state, "Theta": "N/A", "Counts": counts})

df = pd.DataFrame(data)
df["Counts"] = df["Counts"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df.to_csv("/Users/hrishitkotadia/PycharmProjects/Black-Hole-Information-Paradox/data/quantum_state_results.csv", index=False)
print("Results saved to 'quantum_state_results.csv'")


























