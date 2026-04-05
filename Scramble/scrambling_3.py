from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
import numpy as np
import pandas as pd
from fractions import Fraction
import ast


def prepare_entanglement(state, theta):
    circuit = QuantumCircuit(3, 3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)



    return circuit

