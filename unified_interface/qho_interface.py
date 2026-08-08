"""
- This file represents the backend logic

- Sequence of the Pipeline:
    1. Takes user config (problem, parameters, backend)
    2. Calls nuclear_hamiltonian.py → builds Hamiltonian
    3. Calls nuclear_ansatz.py → builds Cirq circuit
    4. Calls nuclear_ansatz.py → exports QASM2
    5. Calls pyqasm_utils.py → validates + translates to backend
    6. Calls vqe_solver.py → executes VQE
    7. Returns full results dictionary 

"""

from pathlib import Path
from hamiltonian.nuclear_hamiltonian import build_nuclear_hamiltonian

from ansatz.cirq_ansatz import (
    build_ansatz_cirq,
    export_to_qasm2,
)

from solver.pyqasm_utils import (
    validate_qasm2,
    translate_to_backend,
    get_circuit_info
)
from solver.validation_utils import (
    run_vqe,
)



def run_pipeline(
        config, backend='ibm', noise_level=0.0,
        optimizer='COBYLA', reps=2,
        qasm_export_path=None):

    """
    Args:
        config           : Hamiltonian configuration
        backend          : 'ibm', 'google', 'aws'
        noise_level      : 0.0 noiseless, >0 noisy
        optimizer        : 'COBYLA' or 'SLSQP'
        reps             : ansatz repetitions
        qasm_export_path : QASM2 file path

    Returns:
        result : dictionary containing all pipeline outputs including VQE results

    """

    # --------------- INPUT VALIDATION ---------------
    backend = backend.lower()

    supported_backends = {
        "ibm",
        "google",
        "aws",
    }

    if backend not in supported_backends:
        raise ValueError(
            f"Unsupported backend: '{backend}'. "
            f"Choose from {sorted(supported_backends)}."
        )

    if "option" not in config:
        raise ValueError(
            "Hamiltonian configuration must contain "
            "an 'option' field."
        )

    if reps < 1:
        raise ValueError(
            "reps must be at least 1."
        )

    if not 0.0 <= noise_level <= 1.0:
        raise ValueError(
            "noise_level must be between 0.0 and 1.0."
        )




    # --------------- QHO SIMULATION ENGINE ---------------
    print("FULL PIPELINE OF QHO SIMULATION ENGINE ! ")

    # Step 1: Build Hamiltonian
    print(f"\nBuilding Hamiltonian — {config['option']}")
    H, n_modes, metadata = build_nuclear_hamiltonian(config)
    print(f"      {metadata['phenomenon']}")


    # Step 2: Build ansatz circuit
    print(f"\nBuilding Cirq ansatz (reps={reps})")
    circuit, symbols, _ = build_ansatz_cirq(n_modes, reps=reps)
    print(f"      Parameters: {len(symbols)}")


    # Step 3: QASM2 export + PyQASM validation
    print(f"\nExporting QASM2 + PyQASM validation")
    raw_qasm2      = export_to_qasm2(circuit, filepath=None)

    if qasm_export_path is None:
        qasm_export_path = (
            f"exports/"
            f"{config['option']}_ansatz.qasm"
        )

    Path(qasm_export_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    validated_qasm = validate_qasm2(raw_qasm2)

    with open(qasm_export_path, "w") as file:
        file.write(validated_qasm)

    circuit_info = get_circuit_info(validated_qasm)
    print(f"      Qubits: {circuit_info['n_qubits']}, "
          f"Depth: {circuit_info['depth']}, "
          f"Gates: {circuit_info['n_gates']}")


    # Step 4: Translate to backend
    print(f"\nTranslating to backend: {backend.upper()}")
    backend_circuit = translate_to_backend(validated_qasm, backend=backend)


    # Step 5: Execute VQE
    print(f"\nExecuting VQE "
          f"(backend={backend}, noise={noise_level}, optimizer={optimizer})")
    vqe_result = run_vqe(
        qubit_operator  = H,
        n_qubits        = n_modes,
        backend_circuit = backend_circuit,
        backend         = backend,
        noise_level     = noise_level,
        symbols         = symbols,
        optimizer       = optimizer,
    ) 


    print(f"  ---------- RESULTS ----------")
    print(f"  VQE Energy              : {vqe_result['energy']:.6f} MeV")
    print(f"  Exact Energy            : {vqe_result['exact_energy']:.6f} MeV")
    print(f"  Error                   : {vqe_result['error_pct']:.4f} %")
    print(f"  Number of Iterations    : {vqe_result['n_iterations']}")
    print(f"  Converged               : {vqe_result['converged']}")


    return {
        'hamiltonian'    : H,
        'n_modes'        : n_modes,
        'metadata'       : metadata,
        'circuit_info'   : circuit_info,
        'qasm2_validated': validated_qasm,
        "qasm2_path"     : qasm_export_path,
        'backend'        : backend,
        **vqe_result,
    }
