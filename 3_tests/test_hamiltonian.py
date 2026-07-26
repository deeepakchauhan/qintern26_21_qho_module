"""
- Tests for nuclear_hamiltonian.py
- Tests QubitOperator output correctness against analytical eigenvalues

"""

import numpy as np
import pytest
from openfermion import get_sparse_operator
from hamiltonian.nuclear_hamiltonian import (

    build_free_qho,
    build_pairing_interaction,
    build_nuclear_hamiltonian,
)

# ----------------------------------------- HELPER FUNCTION ---------------------------------------------
def get_eigenvalues(qubit_operator, n_qubits):

    H_matrix = get_sparse_operator(qubit_operator, n_qubits=n_qubits).toarray()

    return np.sort(np.linalg.eigh(H_matrix)[0].real)



# -------------------- TEST 1 : Free QHO eigenvalues matches with analytical values --------------------
def test_free_qho_1mode_eigenvalues():

    """
    n = 1, omega = 1.0
    Analtical: E_n = omega*(n + 1/2) = [0.5, 1.5]

    """


    H = build_free_qho(n_modes=1, omega=1.0)
    evals = get_eigenvalues(H, n_qubits=1)
    expected_result = np.array([0.5, 0.5])

    assert np.allclose(evals, expected_result, atol=1e-6), \
        f"Expected: {expected_result}, got: {evals}"

    print("test_free_qho_1mode_eigenvalues: PASSED!")



def test_free_qho_2mode_eigenvalues():

    """
    n = 2, omega = 1.0
    Analytical: E_N = omega*(N + 1) for N=0,1,2
    Eigenvalues: [1.0, 2.0, 2.0, 3.0]

    """


    H = build_free_qho(n_modes=2, omega=1.0)
    evals = get_eigenvalues(H, n_qubits=2)
    expected_result = np.array([1.0, 2.0, 2.0, 3.0])

    assert np.allclose(evals, expected_result, atol=1e-6), \
        f"Expected: {expected_result}, got: {evals}"

    print("test_free_qho_2mode_eigenvalues: PASSED!")



def test_free_qho_omega_scaling():

    """
    - Since eigenvalues scale linearly with omega,
    - E(omega=2) = 2 * E(omega=1)

    """

    H1 = build_free_qho(n_modes=1, omega=1.0)
    H2 = build_free_qho(n_modes=2, omega=2.0)

    e1 = get_eigenvalues(H1, n_qubits=1)
    e2 = get_eigenvalues(H2, n_qubits=2)

    assert np.allclose(2 * e1, e2, atol=1e-6), \
        "Eigenvalues should scale linearly with omega"

    print("test_free_qho_omega_scaling: PASSED!")



# --------------------------- TEST 2 : PAIRING LOWERS GROUND STATE ENERGY ---------------------------

def test_pairing_lowers_ground_energy_state():

    """
    - Addition of pairing interaction terms must lower the ground state energy
    - And, pairing makes nucleus more bound

    """

    H_free = build_free_qho(n_modes=2, omega=1.0)
    H_pair = build_pairing_interaction(n_modes=2, coupling=0.5)
    H_total = H_free + H_total

    e_free = get_eigenvalues(H_free, n_qubits=2)[0]
    e_total = get_eigenvalues(H_total, n_qubits=2)[0]

    assert e_total < e_free, \
        f"Pairing should be lower E0: {e_total:.4f} < {e_free:.4f}"

    print("test_pairing_lowers_ground_energy_state: PASSED!")




# --------------------------------- TEST 3 : TIME DEPENDENT COUPLING ----------------------------------

def test_time_dependent_at_zero():

    """
    - H(t=0) with time-dependednt pairing must equal to free QHO
    - Sin(0) = 0, so coupling vanishes.

    """

    H_t0 = build_nuclear_hamiltonian(
        n_modes=2, omega=1.0,
        interactions=[{'type': 'pairing', 'strength': 0.5, 'time_dep': True}],
        time=0.0
    )

    H_free = build_free_qho(n_modes=2, omega=1.0)

    e_t0 = get_eigenvalues(H_t0, n_qubits=2)
    e_free = get_eigenvalues(H_free, n_qubits=2)

    assert np.allclose(e_t0, e_t0, atol=1e-6), \
        "H(t=0) should be equal to free QHO"

    print("test_time_dep_at_zero: PASSED!")


def test_time_dep_at_pi_over_2():

    """
    - H(t=pi/2) with time-dependent pairing must equal static full coupling
    - sin(pi/2) = 1; full coupling applies

    """

    H_td = build_nuclear_hamiltonian(
        n_modes=2, omega=1.0,
        interactions=[{'type': 'pairing', 'strength': 0.5, 'time_dep': True}],
        time = np.pi/2
    )

    H_static = build_nuclear_hamiltonian(
        n_modes=2, omega=1.0,
        interactions=[{'type': 'pairing', 'strength': 0.5, 'time_dep': False}]
    )

    e_td = get_eigenvalues(H_td, n_qubits=2)
    e_static = get_eigenvalues(H_static, n_qubits=2)

    assert np.allclose(e_td, e_static, atol=1e-6), \
        "H(t=pi/2) should be equal to static full coupling"

    print("test_time_dep_at_pi_over_2: PASSED!")



# ------------------------------ TEST 4: g=0 gives n*omega spectrum ------------------------------

def test_zero_coupling():

    """
    - with coupling = 0, the combined hamiltonian must return free QHO
    - confirmation: g=0 gives pure n*omega energy levels

    """

    H_combined = build_nuclear_hamiltonian(
        n_modes = 2, omega=1.0,
        interactions=[{'type': 'pairing', 'strength': 0.0, 'time_dep': False}]
    )

    H_free = build_nuclear_hamiltonian(n_modes=2, omega=1.0)

    e_combined = get_eigenvalues(H_combined, n_qubits=2)
    e_free = get_eigenvalues(H_free, n_qubits=2)

    assert np.allclose(e_combined, e_free, atol=1e-6), \
        "Zero coupling should give pure QHO spectrum"

    print("test_zero_coupling: PASSED!")



# ------------------------------ TEST 5: QUBIT OPERATOR OUTPUT TYPE ------------------------------

def test_output_type():

    """
    - It confirms whether build_nuclear_hamiltonian return Qubit Operator or not
    - It is required for OpenFermion pipeline compliance

    """

    from openfermion import QubitOperator

    H = build_nuclear_hamiltonian(n_modes=2, omega=1.0)

    assert isinstance(H, QubitOperator), \
        f"Expected QubitOperator, got {type(H)}"

    print("test_output_type: PASSED")