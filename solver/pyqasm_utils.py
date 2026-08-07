"""
---------------------------------------- QHO SIMULATION ENGINE ----------------------------------------

    - This module checks that the exported QASM is correct and 
    - converts it into a form that different hardware SDKs can understand.
    - It is basically preparing a quantum program for execution.

    In the Pipeline:
    Cirq circuit -> export_to_qasm2() -> pyqasm_utils.py -> IBM / Google / AWS

"""

from pyqasm import loads, dumps


# ---------------------------------------- GATE MAPPING DICTIONARY ----------------------------------------
QISKIT_GATE_MAP = {
    'x'      : 'x',
    'ry'     : 'ry',
    'cx'     : 'cx',
    'measure': 'measure',
    'h'      : 'h',
    'rz'     : 'rz',
    'rx'     : 'rx',
}

CIRQ_GATE_MAP = {
    'x'      : 'cirq.X',
    'ry'     : 'cirq.ry',
    'cx'     : 'cirq.CNOT',
    'measure': 'cirq.measure',
    'h'      : 'cirq.H',
    'rz'     : 'cirq.rz',
    'rx'     : 'cirq.rx',
}

BRAKET_GATE_MAP = {
    'x'      : 'X',
    'ry'     : 'Ry',
    'cx'     : 'CNot',
    'measure': None,        # Braket measures all at end automatically
    'h'      : 'H',
    'rz'     : 'Rz',
    'rx'     : 'Rx',
}

SUPPORTED_GATES = set(QISKIT_GATE_MAP.keys())



# ---------------------------------------- RAW QASM2 TO CLEAN VERIFIED QASM2 STRING ---------------------------------------- 
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




# ---------------------------------------- QUANTUM GATES USED IN CIRCUIT ---------------------------------------- 
def check_gate_support(qasm2_string):
    """
    - verify all gates in QASM2 
    - raises value error if unsupported gates found
    
    Returns:
        gates_used  : set of gate names found in the circuit

    """

    gates_used = set()
    for line in qasm2_string.split('\n'):
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('OPENQASM'):
            continue
        if line.startswith('include') or line.startswith('qreg') \
                or line.startswith('creg'):
            continue
        gate_name = line.split('(')[0].split(' ')[0].lower()
        if gate_name:
            gates_used.add(gate_name)


    unsupported = gates_used - SUPPORTED_GATES
    if unsupported:
        raise ValueError(
            f"Unsupported gates found: {unsupported}. "
            f"Supported gates: {SUPPORTED_GATES}"
        )

    print(f"Gate check completed successfully — Gates Used: {gates_used}")
    return gates_used




"""
---------------------------------------- TRANSLATOR LAYERS ----------------------------------------

    - Their purpose is to take the same validated OpenQASM 2.0 program and 
    - Convert it into the native circuit format required by different quantum SDKs, 
    - allowing one Cirq-generated circuit to run on IBM, Google, or AWS without changing the original code.

"""

# ---------------------------------------- TRANSLATOR LAYER-1 : QASM2 -> QISKIT (IBM) ----------------------------------------
def translate_to_qiskit(validated_qasm):
    """
    - Translate QASM2 to Qiskit QuantumCircuit for IBM hardware.

    """

    from qiskit import QuantumCircuit

    check_gate_support(validated_qasm)
    circuit = QuantumCircuit.from_qasm_str(validated_qasm)

    print("Qiskit Translation completed successfully! ")
    print(f"{circuit.num_qubits} qubits, and depth {circuit.depth()}")

    return circuit


# ---------------------------------------- TRANSLATOR LAYER-2 : QASM2 -> CIRQ (GOOGLE) ----------------------------------------
def translate_to_cirq(validated_qasm):
    """
    - Translate QASM2 back to Cirq circuit for Google hardware.

    """
    from cirq.contrib.qasm_import import circuit_from_qasm

    check_gate_support(validated_qasm)
    circuit = circuit_from_qasm(validated_qasm)

    print(f"Cirq Translation completed successfully! ")

    return circuit


# ---------------------------------------- TRANSLATOR LEVEL-3 : QASM2 -> BRAKET (AWS) ----------------------------------------
def translate_to_braket(validated_qasm):
    """
    - Translate QASM2 to AWS Braket circuit.
    - Braket has no direct OpenQASM importer.

    """
    from braket.circuits import Circuit
    from braket.circuits import gates as bg

    check_gate_support(validated_qasm)

    n_qubits = 0
    ops      = [] 

    for line in validated_qasm.split('\n'):
        line = line.strip()
        if not line or line.startswith('//') \
                or line.startswith('OPENQASM') \
                or line.startswith('include'):
            continue
        if line.startswith('qreg'):
            n_qubits = int(line.split('[')[1].split(']')[0])
            continue
        if line.startswith('creg') or line.startswith('measure'):
            continue


        if line.startswith('ry'):
            angle = float(line.split('(')[1].split(')')[0])
            qubit = int(line.split('q[')[1].split(']')[0])
            ops.append(('ry', angle, qubit))
        elif line.startswith('cx'):
            parts  = line.replace('cx', '').strip().rstrip(';')
            ctrl   = int(parts.split(',')[0].strip().split('[')[1].split(']')[0])
            target = int(parts.split(',')[1].strip().split('[')[1].split(']')[0])
            ops.append(('cx', ctrl, target))
        elif line.startswith('x'):
            qubit = int(line.split('q[')[1].split(']')[0])
            ops.append(('x', qubit))


        circuit = Circuit()
        for op in ops:
            if op[0] == 'ry':
                circuit.ry(op[2], op[1])
            elif op[0] == 'cx':
                circuit.cnot(op[1], op[2])
            elif op[0] == 'x':
                circuit.x(op[1])


    print(f"Braket Translation completed successfully! ")
    return circuit





# ---------------------------------------- TRANSLATOR DISPATCHER ----------------------------------------
def translate_to_backend(validated_qasm, backend):
    """
    - It's work is to decide which traslator should run
    - It is the dispatcher
    - it returns backend specific circuit object

    """

    translators = {
        'ibm'   : translate_to_qiskit,
        'google': translate_to_cirq,
        'aws'   : translate_to_braket,
    }

    if backend not in translators:
        raise ValueError(
            f"Unknown backend: '{backend}'. "
            f"Supported: {list(translators.keys())}"
        )

    return translators[backend](validated_qasm)
    



# --------------------------------------- CONVERT TO FORMAT REQUIRED BY CHOSEN BACKEND ----------------------------------------
def cirq_from_qasm(qasm2_string):
    """
    - Imports QASM2 string back to cirq
    - Used when google backend is selected

    """

    from cirq.contrib.qasm_import import circuit_from_qasm
    return circuit_from_qasm(qasm2_string)




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



    