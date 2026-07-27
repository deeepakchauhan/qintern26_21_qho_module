"""
- main Path : QubitOperator → cirq.PauliSum → cirq.Simulator → VQE
- validation: QubitOperator → SparsePauliOp → Qiskit EstimatorV2 → cross-check

- this file takes the Hamiltonian and the circuit that were built in the other files
- and, runs the variational optimisation, and returns the physical results.
- basically, it finds the lowest energy state of the nuclear Hamiltonian 
- using the variational quantum eigensolver algorithm.
"""

import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
import cirq
import sympy
import numpy as np
from scipy.optimize import minimize
from openfermion import get_sparse_operator



# --------------------- CONVERT OpenFermion QubitOperator TO CIRQ PAULISUM --------------------
def qubit_operator_to_pauli_sum(qubit_operator, qubits):

    """
    - The Hamiltonian arrives from nuclear_hamiltonian.py as an OpenFermion QubitOperator. 
    - But Cirq's simulator cannot directly compute expectation values from a QubitOperator.
    - cirq.PauliSum function is the translator between the two formats.

    Args:
        qubit_operator : openfermion.QubitOperator
        qubits         : list of cirq.LineQubit

    Returns:
        cirq.PauliSum

    """


    pauli_map = {'X': cirq.X, 'Y': cirq.Y, 'Z': cirq.Z}
    pauli_sum = cirq.PauliSum()

    for term, coeff in qubit_operator.terms.items():
        if len(term) == 0:
            pauli_sum += coeff * cirq.PauliString()

        else:
            pauli_string = cirq.PauliString(
                {qubits[index]: pauli_map[pauli] for index, pauli in term},
                coeff = coeff
            )
            pauli_sum += pauli_string


    return pauli_sum    




# ------------------------------- EXACT DIAGONALISATION -------------------------------
def exact_diagonalise(qubit_operator, n_qubits):

    """
    - exact ground state energy via NumPy eigenvalue decomposition.
    - unchanged from original decomposition

    """

    H_matrix = get_sparse_operator(qubit_operator, n_qubits=n_qubits).toarray()
    evals, evecs = np.linalg.eigh(H_matrix)

    return float(evals[0].real), evecs[:, 0]





# ------------------------------- FIDELITY COMPUTATION -------------------------------
def compute_fidelity(psi_exact, psi_vqe):

    """
    - Computes how similar the VQE state is to the exact ground state using the below formula:
    - Fidelity F = |<psi_exact|psi_vqe>|^2
    - It measures the actual overlap between the VQE wavefunction,
    - and the true nuclear ground state wavefunction.

    Args:
        psi_exact : np.ndarray
        psi_vqe   : np.ndarray

    Returns:
        float in [0,1]

    """

    return float(np.abs(np.dot(np.conj(psi_exact), psi_vqe)) ** 2)




# ----------------------- MAIN PATH: VQE USING CIRQ SIMULATOR -----------------------
def run_vqe_using_cirq(qubit_operator, cirq_circuit, symbols, qubits,
                       optimizer="COBYLA", max_iter=5000, seed=42):

    """
    - After OpenFermion builds H and Cirq builds the circuit
    - then cirq.Simulator is used for expectation value computation
    - It is the primary execution Path

    Args:
        qubit_operator : The Hamiltonian
        cirq_circuit   : symbolic ansatz
        symbols        : variational parameters
        qubits         : list of cirq.LineQubit
        optimizer      : 'COBYLA' or 'SLSQP'
        max_iter       : maximum optimiser iterations
        seed           : random seed


    Returns:
        dictionary with keys:
            energy, exact_energy, error, fidelity,
            optimal_params, history, num_iterations, converged

    """

    np.random.seed(seed)
    num_params = len(symbols)
    history    = []
    n_qubits   = len(qubits)
    simulator  = cirq.Simulator()



    # Convert Hamiltonian to cirq.PauliSum for expectation value 
    pauli_sum = qubit_operator_to_pauli_sum(qubit_operator, qubits)

    def cost(theta):
        """
        Bind parameters, simulate circuit, and compute <psi|H|psi>
        """

        # Bind symbolic parameters to numerical values
        param_resolver = cirq.ParamResolver(
            {str(sym): float(theta[i]) for i, sym in enumerate(symbols)}
        )

        # Simulate the circuit
        result = simulator.simulate(
            cirq_circuit,
            param_resolver=param_resolver
        )

        # Get the statevector
        state_vector = result.final_state_vector

        # Compute expectation value
        energy = pauli_sum.expectation_from_state_vector(
            state_vector,
            qubit_maps = {q: i for i, q in enumerate(qubits)}
        ).real

        history.append(float(energy))

        return float(energy)


    # random initial parameters in [0, pi]
    theta_initial = np.random.uniform(0, np.pi, size=num_params)


    # Classical optimisation
    opt = minimize(
        cost,
        theta_initial,
        method=optimizer,
        options={'maxiter': max_iter, 'rhobeg': 0.5}
    )


    # Validation against exact diagonalisation
    e0_exact, psi_exact = exact_diagonalise(qubit_operator, n_qubits)


    # Get VQE statevector for fidelity
    param_resolver = cirq.ParamResolver(
    {
        str(sym): float(opt.x[i])
        for i, sym in enumerate(symbols)
    }
) 

    result_opt = simulator.simulate(cirq_circuit, param_resolver=param_resolver)
    psi_vqe    = result_opt.final_state_vector
    fidelity   = compute_fidelity(psi_exact, psi_vqe)


    return {

        'energy'        : float(opt.fun),
        'exact_energy'  : float(e0_exact),
        'error'         : abs(e0_exact - opt.fun) / abs(e0_exact)  * 100,
        'fidelity'      : fidelity,
        'optimal_params': opt.x,
        'history'       : history,
        'n_iterations'  : len(history),
        'converged'     : opt.success,
    }


        


# -------------------------- VALIDATION PATH: Qiksit ESTIMATORV2 --------------------------
def run_vqe_qiskit(qubit_operator, qasm2_string, n_qubits,
                   optimizer='COBYLA', max_iter=500, seed=42):
        
    """
    - used to cross check cirq pipeline path

    """

    np.random.seed(seed)
    history = []

    qiskit_circuit = QuantumCircuit.from_qasm_str(qasm2_string)
    num_params = len(qiskit_circuit.parameters)


    H_matrix = get_sparse_operator(qubit_operator, n_qubits= n_qubits).toarray()
    H_qiskit = SparsePauliOp.from_operator(H_matrix)

    def cost(theta):
        param_dict = {
            qiskit_circuit.parameters[i]: float(theta[i])
            for i in range(num_params)
        }
        
        
        bound  = qiskit_circuit.assign_parameters(param_dict)
        energy = Statevector(bound).expectation_value(H_qiskit).real
        history.append(float(energy))
        return float(energy)

    theta_initial = np.random.uniform(0, np.pi, size=num_params)

    options = {
    "maxiter": max_iter,
    }

    # rhobeg is only supported by COBYLA
    if optimizer.upper() == "COBYLA":
        options["rhobeg"] = 0.5

    opt = minimize(
        cost,
        theta_initial,
        method=optimizer,
        options=options
    )

    e0_exact, psi_exact = exact_diagonalise(qubit_operator, n_qubits)

    param_dict  = {
        qiskit_circuit.parameters[i]: float(opt.x[i])
        for i in range(num_params)
    }
    bound_opt   = qiskit_circuit.assign_parameters(param_dict)
    psi_vqe     = Statevector(bound_opt).data
    fidelity    = compute_fidelity(psi_exact, psi_vqe)



    return {
        'energy'         : float(opt.fun),
        'exact_energy'   : float(e0_exact),
        'error_pct'      : abs(e0_exact - opt.fun) / abs(e0_exact) * 100,
        'fidelity'       : fidelity,
        'optimal_params' : opt.x,
        'history'        : history,
        'n_iterations'   : len(history),
        'converged'      : opt.success,
    }

    


# ------------------------------ COMPARISON LOGIC BETWEEN CIRQ and QISKIT ------------------------------

def cross_check_vqe(config: dict, maxiter: int = 200) -> dict:

    """
    - Runs VQE via both Cirq and Qiskit 
    - on the same Hamiltonian, and returns comparison results

    """

    cirq_result = run_vqe_using_cirq(config, maxiter=maxiter)
    qiskit_result = run_vqe_qiskit(config, maxiter=maxiter)

    return {

        'cirq_energy'       : cirq_result["ground_state_energy"],
        'qiskit_energy'     : qiskit_result["ground_state_energy"],
        'discrepancy'       : abs(
            cirq_result["ground_state_energy"] - qiskit_result["ground_state_energy"]
        ),

        'cirq_result'       : cirq_result,
        'qiskit_result'     : qiskit_result,

    }

