"""
- CONTAINS TESTS FOR vqe_solver.py
- It Tests VQE Correctness: energy accuracy, variational bound, convergence
- Also, cross - check agreement between Cirq(main path) & qiakit (validation path)

"""



import numpy as np
import pytest
from hamiltonian.nuclear_hamiltonian import build_nuclear_hamiltonian
from solver.vqe_solver import (
    run_vqe_using_cirq,
    run_vqe_qiskit,
    cross_check_vqe

)



# ----------------------------------- SMALL TEST CASE -----------------------------------

@pytest.fixture
def simple_config():

    """ Small digonalise test case: free_qho only, no interactions """

    return {'n_modes': 2, 'omega': 1.0, 'interactions': []}


@pytest.fixture
def exact_ground_energy(simple_config):

    """ Independent Classical benchmark for ground state energy """

    H, metadata = build_nuclear_hamiltonian(**simple_config)

    return min(metadata["exact_eigenvalues"])



# ------------------------------ TEST 1: ENERGY ACCURACY ------------------------------
def test_vqe_energy(simple_config, exact_ground_energy):

    """VQE (main Cirq path) should converge close to the exact ground state energy"""

    result = run_vqe_using_cirq(simple_config, max_iter=200)
    error = abs(result["ground_state_energy"] - exact_ground_energy)

    assert error < 1e-2, f"VQE energy off by {error}, exceeds tolerance"





# ------------------------------ TEST 2: VARIATIONAL BOUND ------------------------------
def test_variational_bound(simple_config, exact_ground_energy):

    """ 
        - VQE energy must never fall below the true ground state energy 
        - Variational Principle

    """

    result = run_vqe_using_cirq(simple_config, max_iter=200)

    assert result["ground_state_energy"] >= exact_ground_energy - 1e-6, (

        " Variational bound violated, "
        "indicating a bug in Hamiltonian, Ansatz, or estimator setup"
    )





# -------------------------------- TEST 3: CONVERGENCE ------------------------------------
def test_vqe_convergence(simple_config):

    """
    - VQE should reach a converged result without hitting the max. iteration ceilling

    """

    result = run_vqe_using_cirq(simple_config, max_iter=200)

    assert result["success"] is True
    assert result["n_iterations"] < 200, "VQE used up to full iteration budget without converging"





# ------------------------------ TEST 4: CROSS - CHECK BETWEEN CIRQ AND QISKIT ------------------------------
def test_cirq_and_qiskit_paths(simple_config):

    """
    - Cirq path and Qiskit path should agree closely
    
    """

    cross_check_result= cross_check_vqe(simple_config, max_iter=200)
    discrepancy = abs(
        cross_check_result["cir_energy"] - cross_check_result["qiskit_energy"]
    )

    assert discrepancy < 1e-2, (
        f" Cirq and Qiskit disagree by {discrepancy} - check operator "
        f" conversion (QubitOperator -> PauliSum vs QubitOperator  -> SparsePauli)"
        f"or ansatz/estimator setup on one of the two paths."
    )





# ------------------------------ TEST 5: BEHAVIOUR ON A SLIGHTLY HARDER CASE (with Interaction) ------------------------------
def test_vqe_with_pairing_interaction():

    """ 
    Sanity check:
        whether VQE still converges reasonably with non-trivial interaction term

    """

    config = {
        'n_modes': 2,
        'omega'  : 1.0,
        'interactions': [{"type": "pairing", "strength": 0.5}],
    }

    H, metadata = build_nuclear_hamiltonian(**config)
    exact_energy = min(metadata["exact_eigenvalues"])

    result = run_vqe_using_cirq(config, max_iter=300)
    error = abs(result["ground_state_energy"] - exact_energy)

    assert error < 1e-2
    assert result["ground_state_energy"] >= exact_energy - 1e-6
