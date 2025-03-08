from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
import numpy as np
import pandas as pd
from fractions import Fraction
import ast


def prepare_state(state, theta):
    circuit = QuantumCircuit(3, 3)

    return circuit