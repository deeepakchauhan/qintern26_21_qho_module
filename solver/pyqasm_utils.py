"""
---------------------------------------- QHO SIMULATION ENGINE ----------------------------------------

    - This module checks that the exported QASM is correct and 
    - converts it into a form that different hardware SDKs can understand.
    - It is basically preparing a quantum program for execution.

    In the Pipeline:
    Cirq circuit -> export_to_qasm2() -> pyqasm_utils.py -> IBM / Google / AWS

"""

from pyqasm import loads, dumps




#  ---------------------------------------- RAW QASM2 TO CLEAN VERIFIED QASM2 STRING ---------------------------------------- 
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
    print("PyQASM Validation completed successfully!")
    return validated





# --------------------------------------- CONVERT TO FORMAT REQUIRED BY CHOSEN BACKEND ----------------------------------------
def cirq_from_qasm(qasm2_string):
    """
    - Imports QASM2 string back to cirq
    - Used when google backend is selected

    """

    from cirq.contrib.qasm_import import circuit_from_qasm
    return circuit_from_qasm(qasm2_string)




def qasm2_to_backend(validated_qasm, backend='ibm'):

    """
    - Prepare a validated OpenQASM2 circuit for the selected backend.
    - Supported backends: IBM, Google, and AWS. 


    Returns:
    - backend_circuit : backend specific circuit object

    """



    if backend == 'ibm':
        from qiskit import QuantumCircuit
        circuit = QuantumCircuit.from_qasm_str(validated_qasm)

        print(f"Circuit ready for IBM Backend: "
              f"{circuit.num_qubits} qubits, depth {circuit.depth()}")

        return circuit


    elif backend == 'google':
        circuit = cirq_from_qasm(validated_qasm)

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
            f"Supported Backends: 'ibm', 'google', 'aws' "
        )





# ---------------------------------------- BASIC INFORMATION ABOUT THE CIRCUIT ---------------------------------------- 
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



    