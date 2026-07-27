"""
------------------------------ QHO SIMULATION ENGINE ------------------------------

    PyQASM Utility layer:
    - It loads, validates, and transpiles QASM2 circuits via PyQASM
    - It prepares circuits for hardware submission on IBM, Google, or AWS.

    In the Pipeline:
    Cirq circuit -> export_to_qasm2() -> pyqasm_utils.py -> IBM / Google / AWS

"""

from pyqasm import loads, dumps


#  ------------------------------ RAW QASM2 TO CLEAN VERIFIED QASM2 STRING ------------------------------ 
def validate_qasm2(qasm2_string):

    """
    - Parse and validate a QASM2 string using PyQASM

    Args:
        qas2_string :  raw QASM2 from cirq_circuit.to_qasm()

    Returns:
        validated_qasm : clean validated QASM2

    """

    module = loads(qasm2_string)
    module.unroll()
    validated = dumps(module)
    print("PyQASM Validation is DONE!")
    return validated




# ------------------------------ CONVERT TO FORMAT REQUIRED BY CHOSEN BACKEND ------------------------------
def qasm2_to_backend(validated_qasm, backend='ibm'):

    """
    - Prepares a validated QASM2 circuit for a IBM backend.

    Returns:
    - backend_circuit : backend specific circuit object

    """


    if backend == 'ibm':
        from qiskit import QuantumCircuit
        circuit = QuantumCircuit.from_qasm_str(validated_qasm)

        print(f"Circuit ready for IBM Backend: "
              f"{circuit.num_qubits} qubits, depth {circuit.depth}")

        return circuit


    elif backend == 'google':
        import cirq
        circuit = cirq.read_json(json_text=validated_qasm)

        print("Quantum Circuit is ready for Google Backend.")

        return circuit


    elif backend == 'aws':
        from braket.circuits import Circuit
        circuit = Circuit.from_ir(validated_qasm)

        print("Quantum Circuit is ready for AWS backend")

        return circuit

    else:
        raise ValueError(
            f"Unknown backend: '{backend}'. "
            f"Supported Backends: 'IBM', 'Google', 'AWS' "
        )




# ------------------------------ BASIC INFORMATION ABOUT THE CIRCUIT ------------------------------ 
def get_circuit_info(validated_qasm):

    """
    - Extracts basic circuit information from validated QASM2

    Returns:
        dictionary with n_qubits, n_gates, gate_list

    """


    from qiskit import QuantumCircuit
    qc = QuantumCircuit.from_qasm_str(validated_qasm)

    return {
        'n_qubits'  : qc.num_qubits,
        'depth'     : qc.depth(),
        'n_gates'   : len(qc.data),
        'gate_list' : [str(gate.operation.name) for gate in qc.data],
    }



    