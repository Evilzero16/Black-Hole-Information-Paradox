from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram, circuit_drawer, \
    plot_bloch_vector
import matplotlib.pyplot as plt
from qiskit import transpile, assemble
from qiskit.quantum_info import Statevector
import numpy as np
import pandas as pd
from fractions import Fraction

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
            counts = str(result.get_counts())
            theta_frac = Fraction(theta / np.pi).limit_denominator(100)
            theta_str = f"π/{theta_frac.denominator}" if theta_frac.numerator != 0.0 else '0'

            data.append({"State" : state, "Theta": theta_str, "Counts": counts})
    else:
        qc = prepare_state(state)
        result = simulator.run((transpile(qc, simulator)), shots=1000).result()
        counts = str(result.get_counts())

        data.append({"State": state, "Theta": "N/A", "Counts": counts})

df = pd.DataFrame(data)
df.to_csv("/Users/hrishitkotadia/PycharmProjects/Black-Hole-Information-Paradox/data/quantum_state_results.csv", index=False)
print("Results saved to 'quantum_state_results.csv'")




# selected_state = "+"
# theta_val = np.pi / 3
#
# qc = prepare_state(selected_state, theta_val if selected_state == 'ry' else None)

# print(f"Quantum Circuit for State {selected_state}")
# print(qc)
# qc.draw(output='mpl')
# plt.show()
#
# simulator = Aer.get_backend("qasm_simulator")
#
# compiled_circuit = transpile(qc, simulator)
#
# result = simulator.run(compiled_circuit, shots=1000).result()
#
# counts = result.get_counts()
# print(f"Measurement Results {counts}")
#
# plot_histogram(counts, title=f"Measurement Results for {selected_state}")
# plt.show()


# circuit_bloch = QuantumCircuit(1)  # Create a new circuit without measurement
# if selected_state == "1":
#     circuit_bloch.x(0)
# elif selected_state == "+":
#     circuit_bloch.h(0)
# elif selected_state == "-":
#     circuit_bloch.h(0)
#     circuit_bloch.z(0)
# elif selected_state == "ry":
#     circuit_bloch.ry(theta_val, 0)
#
# # Get the statevector after transformations
# state = Statevector.from_instruction(circuit_bloch)
# bloch_vector = [np.real(state.expectation_value(Operator([[0, 1], [1, 0]]))),  # X-expectation
#                 np.real(state.expectation_value(Operator([[0, -1j], [1j, 0]]))),  # Y-expectation
#                 np.real(state.expectation_value(Operator([[1, 0], [0, -1]])))]  # Z-expectation
#
#
# # Plot Bloch sphere representation
# plot_bloch_vector(bloch_vector, title=f"Bloch Sphere for |{selected_state}⟩")
# plt.show()


















