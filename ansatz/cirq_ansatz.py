"""
--------------------------------------------- VARIATIONAL ANSATZ BUILDER ---------------------------------------------

- This file covers the building of ansatz circuits in Cirq  with sympy symbolic parameters.
- It exports to QASM2  via cirq_circuit.to_qasm()
- Validates QASM2 via PyQASM

"""


import cirq
import sympy
from pyqasm import loads, dumps



# -------------------------------------------------- CIRQ ANSATZ --------------------------------------------------

def build_ansatz_cirq(n_modes, reps=2):

    """
    Each repetition contains:
        - Ry rotations (occupancy control per level)
        - CNOT between paired qubits (pair correlation entanglement)
    
    Works for all three Hamiltonian options:
        oscillator  : encodes nuclear pair correlations
        fermion     : encodes fermionic level occupancy
        custom      : general entangled trial state 

    Args:
        n_modes: int - number of qubits
        reps   : int - number of variational layers

    Returns:
        circuit     : cirq.Circuit with SymPy symbolic parameters
        symbols     : list of sympy.Symbol
        qubits      : list of cirq.LineQubit 

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





# ------------------------------------------------- QASM EXPORT --------------------------------------------------
def export_to_qasm2(cirq_circuit, filepath=None):

    """
    Args:
        cirq_circuit : unbound symbolic circuit
        filepath     : str or None - save the file if provided

    Returns:
        qasm2_str : str (raw qasm string)

    """

    qasm2_str = cirq_circuit.to_qasm()

    if filepath:
        with open(filepath, 'w') as f:
            f.write(qasm2_str)
            print(f"QASM2 is saved to: {filepath}")

    return qasm2_str




# -------------------------------------------------- VALIDATION --------------------------------------------------------
def validate_with_pyqasm(qasm2_string, filepath=None):

    """
    - Parses the QASM string, validates gate syntax
    - unrolls composite gates to basis gates, and 
    - prepares the circuit to run on the Hardware

    Returns:
        a clean validated QASM2 string

    """

    module = loads(qasm2_string)
    module.unroll()
    validated = dumps(module)

    if filepath:
        with open(filepath, 'w') as f:
            f.write(validated)
        print("Validated QASM2 is saved:", filepath)

    print("PyQASM validation completed successfully !")

    return validated