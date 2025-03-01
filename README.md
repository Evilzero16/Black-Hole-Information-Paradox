# Black Hole Information Scrambling & Retrieval via Quantum Teleportation

This repository contains code and simulations exploring the black hole information paradox using quantum information techniques. We simulate how quantum information that falls into a black hole is scrambled and later retrieved via quantum teleportation methods. The project also leverages hybrid quantum-classical optimization (Variational Quantum Machine Learning) to optimize the retrieval process.

---

## Overview

Black holes are believed to be fast quantum scramblers, mixing the information that falls into them in complex ways. This project is inspired by recent theoretical work—such as the Yoshida–Yao protocol—and aims to:

- **Simulate Quantum Scrambling:**  
  Model how information entering a black hole is mixed (scrambled) using random unitary operations (gates like CNOT, Hadamard, and controlled-phase shifts).

- **Information Retrieval via Teleportation:**  
  Implement quantum teleportation techniques to attempt retrieval of the scrambled quantum information, simulating how information might be recovered from a black hole.

- **Hybrid Quantum-Classical Optimization:**  
  Use variational quantum circuits (VQCs) with tools like PennyLane and Qiskit to optimize the retrieval process, enhancing fidelity between the original and reconstructed states.

- **Scaling and Noise Studies:**  
  Extend simulations from small (4–5 qubits) to larger systems (10+ qubits) and study the impact of realistic hardware noise with error mitigation techniques.

---

## Project Structure

1. **Core Concepts & Theory**  
   Documentation on:
   - Black hole information scrambling
   - Quantum teleportation-based information retrieval
   - Variational quantum machine learning for optimization

2. **Quantum Scrambling Simulation**  
   Code for setting up randomized quantum circuits:
   - **Input Qubit:** Represents the information entering the black hole.
   - **Scrambling Qubits:** A set of qubits that act as the black hole's internal state.
   - **Random Unitary Gates:** Layers of gates (CNOT, Hadamard, controlled-phase) to simulate scrambling.

3. **Information Retrieval via Teleportation**  
   Implementation of the Yoshida–Yao protocol:
   - Create entanglement between the information qubit and the scrambling system.
   - Apply random scrambling (unitary transformations).
   - Use teleportation circuits to attempt information recovery.
   - Measure fidelity between the original and retrieved states.

4. **Hybrid Optimization with VQML**  
   Use PennyLane and classical optimizers (e.g., Adam, RMSprop) to:
   - Define a variational quantum circuit (retrieval circuit) with trainable parameters.
   - Optimize the circuit to maximize the fidelity of information retrieval.
   - Benchmark the performance against fixed-circuit approaches.

5. **Scaling and Noise Resistance**  
   - Scale experiments from 4–5 qubits to 10+ qubits.
   - Simulate realistic hardware noise using Qiskit Aer’s noise models.
   - Explore error mitigation techniques (Qiskit Ignis, PennyLane error-mitigation).

6. **Testing & Analysis**  
   - Experiment with varying scrambling depths and noise levels.
   - Analyze retrieval fidelity vs. scrambling depth.
   - Compare fixed-circuit and hybrid-optimized retrieval methods.

7. **Reporting Results**  
   - Compile quantum circuits, Jupyter Notebooks, and analysis graphs.
   - Discuss theoretical implications for black hole physics and quantum information.
   - Outline future work (scaling up, improving noise resistance, exploring AdS/CFT models).

---

## Requirements

- **Python 3.8+**
- **Qiskit:** For constructing and simulating quantum circuits  
  [Qiskit Documentation](https://qiskit.org/documentation/)
- **PennyLane:** For hybrid quantum-classical optimization  
  [PennyLane Documentation](https://pennylane.ai/)
- **PyTorch** or **TensorFlow:** For optimizing variational circuits
- **Jupyter Notebook:** For interactive development and demonstration

Install the main dependencies with:

```bash
pip install qiskit pennylane torch  
