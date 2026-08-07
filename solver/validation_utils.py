"""
--------------------------------------------- QHO SIMULATION ENGINE ---------------------------------------------

- This module provides local validation and VQE execution utilities.
- Role in the pipeline: Hamiltonian -> Backend translation -> VQE execution -> ground state energy.

- The analytical diagonalisation utilities are intended only for
- local verification, benchmarking, and testing. 
- They are not part of the hardware-agnostic execution pipeline. 

"""

import cirq
import numpy as np
from scipy.optimize import minimize
from openfermion import get_sparse_operator
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error



# ---------------------------------- HAMILTONIAN DIAGONALISATION ---------------------------------
def exact_diagonalise(qubit_operator, n_qubits):
    """
    - To find the exact ground state energy using NumPy, 
    - by diagonalising the Hamiltonian matrix
    - Provides the analytical reference solution used for
    -  testing, benchmarking and verifying Hamiltonian construction.

    Returns:
        e0  : exact ground state energy
        psi0: exact ground state vector

    """

    H_matrix = get_sparse_operator(
        qubit_operator, n_qubits=n_qubits).toarray()

    evals, evecs = np.linalg.eigh(H_matrix)

    return float(evals[0].real), evecs[:, 0]





# ---------------------------------------- HELPER FUNCTIONS ----------------------------------------
def hamiltonian_to_matrix(qubit_operator, n_qubits):
    """
    - convert qubit operator to dense matrix

    """

    return get_sparse_operator(
        qubit_operator, n_qubits=n_qubits
    ).toarray()



def counts_to_energy(counts, H_matrix, n_qubits):
    """
    - Converts measurement counts to energy expectation value.
    - It is only used when the IBM backend is running with noise.
    - However, This only works correctly when the Hamiltonian is diagonal in the computational basis.

    """
    total_shots = sum(counts.values())
    energy      = 0.0
    for bitstring, count in counts.items():
        idx        = int(bitstring.replace(' ', ''), 2)
        state      = np.zeros(2 ** n_qubits)
        state[idx] = 1.0
        prob        = count / total_shots
        energy     += prob * float(np.real(state @ H_matrix @ state))

    return energy



def _matrix_to_cirq_paulisum(qubit_operator, qubits):
    """
    - This function converts an OpenFermion QubitOperator into a Cirq PauliSum.
    - It is only used for the Cirq execution path.

    """
    
    pauli_map = {'X': cirq.X, 'Y': cirq.Y, 'Z': cirq.Z}
    pauli_sum = cirq.PauliSum()
    for term, coeff in qubit_operator.terms.items():
        if len(term) == 0:
            pauli_sum += coeff * cirq.PauliString()
        else:
            ps = cirq.PauliString(
                {qubits[idx]: pauli_map[p] for idx, p in term},
                coefficient=coeff
            )
            pauli_sum += ps
    return pauli_sum





# -------------------------------------------------- VQE LOOP --------------------------------------------------
def run_vqe(qubit_operator, n_qubits, backend_circuit,
            backend='ibm', noise_level=0.0, symbols=None,
            optimizer='COBYLA', max_iter=500, seed=42):

    
    """
    - Executes VQE on the translated backend circuit.
    - Runs on simulator (noiseless or noisy) or real hardware.
    - Uses COBYLA to optimise variational parameters.

    Args:
        qubit_operator  : QubitOperator (The Hamiltonian)
        n_qubits        : number of qubits
        backend_circuit : backend-specific circuit (from translator)
        backend         : 'ibm', 'google', 'aws'
        noise_level     : noiseless, >0 = noisy simulator
        optimizer       : 'COBYLA' or 'SLSQP'
        max_iter        : maximum optimization iterations
        seed            : Ensures reproducible initialization

    Returns:
        dictionary      : energy, exact_energy, error_pct,
                          optimal_params, history, converged
    """

    rng = np.random.default_rng(seed)
    H_matrix = hamiltonian_to_matrix(qubit_operator, n_qubits)

    energy_history = []


    # ---------- IBM PATH ----------
    if backend == 'ibm':
        H_qiskit   = SparsePauliOp.from_operator(H_matrix)
        n_params   = len(backend_circuit.parameters)
        sorted_params = sorted(
            backend_circuit.parameters, key=lambda p: p.name
        )


        if noise_level > 0.0:
                
            # Noisy simulator
            noise_model = NoiseModel()
            error_1q    = depolarizing_error(noise_level, 1)
            error_2q    = depolarizing_error(min(1.0, noise_level * 10 ), 2)
            noise_model.add_all_qubit_quantum_error(error_1q, ['x', 'ry'])
            noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])
            simulator   = AerSimulator(noise_model=noise_model)

            def cost(theta):
                param_dict = {
                        sorted_params[i]: float(theta[i])
                        for i in range(n_params)
                }
                bound  = backend_circuit.assign_parameters(param_dict)
                job    = simulator.run(bound, shots=1024)
                counts = job.result().get_counts()
                energy = counts_to_energy(counts, H_matrix, n_qubits)
                energy_history.append(energy)
                return energy 

        else:
                # Noiseless statevector
                def cost(theta):
                    param_dict = {
                        sorted_params[i]: float(theta[i])
                        for i in range(n_params)
                    }
                    bound  = backend_circuit.assign_parameters(param_dict)
                    energy = float(
                        Statevector(bound).expectation_value(H_qiskit).real
                    )
                    energy_history.append(energy)
                    return energy

        theta_init = rng.uniform(0, np.pi, size=n_params)


    # ------------------ CIRQ PATH --------------------
    elif backend == 'google':

        qubits    = sorted(backend_circuit.all_qubits())
        simulator = cirq.DensityMatrixSimulator() \
                    if noise_level > 0.0 else cirq.Simulator()

        # Count symbols in circuit
        if symbols is None:
            raise ValueError(
                "Symbols must be provided for Google backend"
            )

        n_params = len(symbols)


        H_sum   = _matrix_to_cirq_paulisum(qubit_operator, qubits)

        def cost(theta):
            resolver = cirq.ParamResolver(
                {sym.name: float(theta[i])
                 for i, sym in enumerate(symbols)}
            )

            result  = simulator.simulate(
                backend_circuit, param_resolver=resolver 
            )
            
            sv      = result.final_state_vector    
            energy  = H_sum.expectation_from_state_vector(
                sv, {q: i for i, q in enumerate(qubits)}
            ).real
            energy_history.append(float(energy))
            return float(energy)

        theta_init = rng.uniform(0, np.pi, size=n_params)

    else:
        raise ValueError(
            f"VQE execution not yet implemented for backend: '{backend}'. "
            f"Use 'ibm' or 'google'."
        )



    # ------------------------------ CLASSICAL OPTIMISATION LOOP ------------------------------
    options={'maxiter': max_iter}

    if optimizer.upper() == "COBYLA":
        options['rhobeg'] = 0.5

    opt = minimize(
        cost,
        theta_init,
        method=optimizer,
        options=options 
    )


    # ---------------------------------------- VALIDATION ----------------------------------------
    e0_exact, _ = exact_diagonalise(qubit_operator, n_qubits)

    return {

        'energy'        : float(opt.fun),
        'exact_energy'  : float(e0_exact),
        'error_pct'     : abs(e0_exact - opt.fun) / abs(e0_exact) * 100,
        'optimal_params': opt.x.tolist(),
        'energy_history': energy_history,
        'n_iterations'  : len(energy_history),
        'converged'     : bool(opt.success),
        'optimizer'     : optimizer,
        "noise_level"   : noise_level
    }