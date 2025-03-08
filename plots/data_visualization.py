from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram, plot_bloch_vector
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit.quantum_info import Statevector
import numpy as np


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

selected_state = "ry"
theta_val = np.pi / 3

qc = prepare_state(selected_state, theta_val if selected_state == 'ry' else None)

print(f"Quantum Circuit for State {selected_state}")
print(qc)
if selected_state != 'ry':
   qc.draw(output='mpl', filename=f"|{selected_state}⟩/circuit.png")
else:
    qc.draw(output='mpl', filename=f"|ψ⟩/circuit.png")
plt.show()

simulator = Aer.get_backend("qasm_simulator")

compiled_circuit = transpile(qc, simulator)

result = simulator.run(compiled_circuit, shots=1000).result()

counts = result.get_counts()
print(f"Measurement Results {counts}")

hist = plot_histogram(counts, title=f"Measurement Results for {selected_state}")
plt.show()
if selected_state != 'ry':
   hist.savefig(f"|{selected_state}⟩/histogram.png", dpi=300)
else:
    hist.savefig(f"|ψ⟩/histogram.png", dpi=300)


circuit_bloch = QuantumCircuit(1)  # Create a new circuit without measurement
if selected_state == "1":
    circuit_bloch.x(0)
elif selected_state == "+":
    circuit_bloch.h(0)
elif selected_state == "-":
    circuit_bloch.h(0)
    circuit_bloch.z(0)
elif selected_state == "ry":
    circuit_bloch.ry(theta_val, 0)

# Get the statevector after transformations
state = Statevector.from_instruction(circuit_bloch)
bloch_vector = [np.real(state.expectation_value(Operator([[0, 1], [1, 0]]))),  # X-expectation
                np.real(state.expectation_value(Operator([[0, -1j], [1j, 0]]))),  # Y-expectation
                np.real(state.expectation_value(Operator([[1, 0], [0, -1]])))]  # Z-expectation


# Plot Bloch sphere representation
bloch = plot_bloch_vector(bloch_vector, title=f"Bloch Sphere for |{selected_state}⟩")
if not selected_state == 'ry':
   bloch.savefig(f'|{selected_state}⟩/Bloch_spehere')
else:
    bloch.savefig(f'|ψ⟩/Bloch_spehere')
plt.show()
