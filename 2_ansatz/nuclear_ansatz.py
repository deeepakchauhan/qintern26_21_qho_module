"""
-------------------- VARIATIONAL ANSATZ BUILDER --------------------

- This file covers the building of ansatz circuits in Cirq  with sympy symbolic parameters.
- It exports to QASM2 
- Validates QASM2 via PyQASM

"""


import cirq
import sympy
import numpy as np 


# ------------------------------ CIRQ ANSATZ ------------------------------

def build_nuclear_ansatz(n_modes, reps=2):

    """
    Structure per rep:
        - Ry rotations (occupancy control per level)
        - CNOT between paired qubits (pair correlation entanglement)

    Args:
        n_modes: int - numbe rof qubits
        reps   : int - number of variational layers

    Returns:
        circuit : cirq.Circuit 
        symbols : list of sympy.Symbol (variational parameters)
        qubits  : list of cirq.LineQubit

    """

    qubits = cirq.LineQubit.range(n_modes)
    symbols = []
    moments = []            # group of gates that can all execute at the same time

    for rep in range(reps):

        # Ry rotations on each qubits
        for i, q in enumerate(qubits):
            sym = sympy.Symbol(f"theta_{rep}_{i}")
            symbols.append(sym)
            moments.append(cirq.ry(sym)(q))

        # CNOT between paired qubits
        # pairs: (0,1), (2,3), ...
        for i in range(0, n_modes-1, 2):
            moments.append(cirq.CNOT(qubits[i], qubits[i+1]))

    circuit = cirq.Circuit(moments)
    return circuit, symbols, qubits




# ------------------------------ QASM EXPORT ------------------------------

def export_to_qasm2(cirq_circuit, filepath=None):

    """
    Args
        cirq_circuit : unbound symbolic circuit
        filepath     : str or None - save the file if provided

    Returns
        qasm2_str : str (raw qasm string)

    """

    qasm2_str = cirq_circuit.to_qasm()

    if filepath:
        with open(filepath, 'w') as f:
            f.write(qasm2_str)
            print(f"QASM2 is saved to: {filepath}")

    return qasm2_str



# ------------------------------ PyQASM VALIDATION ------------------------------

def validate_with_pyqasm(qasm2_str, filepath=None):

    """
    - Validate and unroll QASM2 string using PyQASM
    - PyQASM parses the QASm2 circuit, validates gate syntax,
    - prepares the circuit for quantum hardware submission

    Returns:
        validated_qasm : clean validated qasm string

    """

    from pyqasm import loads, dumps

    module = loads(qasm2_str)
    module.unroll()
    validated_qasm = dumps(module)     # export clean QASM

    if filepath:
        with open(filepath, 'w') as f:
            f.write(validated_qasm)
        print(f"Validated QASM2 saved: {filepath}")

    print("PyQASm validation has been done")

    return validated_qasm 
