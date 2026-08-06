"""
- Not the part of the main execution pipeline, but local validation utilities
- To verify whether the Hamiltonian and the quantum state produced by the module is correct
- 

"""

import cirq
import numpy as np
from openfermion import get_sparse_operator


# ---------------------------------------- HAMILTONIAN DIAGONALISATION ----------------------------------------

def exact_digonalise(qubit_operator, n_qubits):
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





# ---------------------------------------- QUANTUM STATE FIDELITY ----------------------------------------
def compute_fidelity(psi_exact, psi_test):
    """
    - Fidelity F = |<psi_exact|psi_test>|^2
    - Measures how closely the test state reproduces the exact ground-state wavefunction.
     
    """

    return float(np.abs(np.dot(np.conj(psi_exact), psi_test)) ** 2)


