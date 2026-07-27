"""
------------------------------- NUCLEAR HAMILTONIAN ENGINE ------------------------------ :

- Free QHO with n-modes and arbitrary 'w' : represents single particle basis
- Pairing Interaction : represents the most universal hamiltonian
- Quadruple Interaction (deformed nuclei, collective modes) : needed for heavier nuclei
- Physical Units: MeV throughout 

"""

import openfermion as of
from openfermion import QubitOperator
from qiskit.quantum_info import SparsePauliOp
import numpy as np 





# ------------------------------ PREDEFINED HAMILTONIANS -----------------------------------
predefined_hamiltonians = {

    'free_oscillators': {
        'parameters' : {'omega': 1.0},
        'n_modes'    : 2,
        'phenomenon' : 'Nuclear Vibrartions at rest',
        'time_dep'   : False,
    },

    'qho_pairing': {
        'parameters' : {'omega': 1.0, 'coupling': 0.5},
        'n_modes'    : 2,
        'phenomenon' : 'Nuclear Pairing',
        'time_dep'   : False,
    },

    'qho_spinorbit': {
        'parameter' : {'omega': 1.0, 'kappa': 0.1},
        'n_modes'   : 2,
        'phenomenon': 'Nuclear Shell splitting',
        'time_dep'  : False
    },

    'qho_full': {
        'parameter' : {'omega': 1.0, 'coupling': 0.5, 'kappa': 0.1},
        "n_modes"   : 2,
        'phenomenon': 'Driven nuclear excitation',
        'time_dep'  : True
    },
}





# ------------------------------ LAYER 1: FREE QHO ----------------------------------------
def build_free_qho(n_modes: int, omega: float = 1.0):

    """
    Free QHO for n single particle levels.

    Args: 
        n_modes: number of qubits
        omega  : oscillator frequency

    Returns:
        OpenFermion QubitOperator
    
    """

    H = QubitOperator()

    for i in range(n_modes):
        H += (omega / 2.0) * QubitOperator("")

        H += (-omega / 2.0) * QubitOperator(f"Z{i}")

    return H
    




# ------------------------------ CONVERSION FUNCTION TO QISKIT ------------------------------
def to_qiskit_validation_operator(openfermion_qubit_op, n_modes):

    
    """
    For Validation / Exact Diagonalization checks only
    - convert an openfermion operator to a Qiskit SparsePauliOp

    """

    pauli_list = []
    for term, coeff in openfermion_qubit_op.terms.items():

        pauli_str = ["I"] * n_modes

    for qubit_idx, pauli_char in term:
        pauli_str[n_modes - 1 - qubit_idx] = pauli_char

    pauli_list.append((''.join(pauli_str), coeff))


    return SparsePauliOp.from_list(pauli_list).simplify()





# ------------------------------ LAYER 2: PAIRING INTERACTION ------------------------------
def build_pairing_interaction(n_modes, coupling):

    """
    Nuclear pairing interaction: H_pair = -G/2 * Σᵢ<ⱼ (XXᵢⱼ + YYᵢⱼ)

    - Encodes pair-hopping: aᵢ†aⱼ + aⱼ†aᵢ in qubit language.
    - Pairing lowers the ground state energy.

    """

    H = QubitOperator()

    for i in range(n_modes):
        for j in range(i + 1, n_modes):
            H += (-coupling / 2.0) * QubitOperator(f"X{i} X{j}")
            H += (-coupling / 2.0) * QubitOperator(f"Y{i} Y{j}")

    return H





# ------------------------------ LAYER 3: SPIN ORBIT INTERACTIONS ------------------------------
def build_spinorbit_interaction(n_modes, kappa):

    """
    Simplified Spin Orbit correction: H_so = -κ * Σᵢ Zᵢ

    - encodes the spin-orbit coupling correction to the nuclear shell mode
    - Splits degenerate shells. And,
    - Produces correct magic numbers > 20.

    Args:
        kappa: float - spin-orbit strength

    """


    H = QubitOperator()
    for i in range(n_modes):
        H += (-kappa) * QubitOperator(f"Z{i}")

    return H 





# ------------------------------ FULL HAMILTONIAN: COMBINING ALL THE ABOVE LAYERS ------------------------------------
def build_nuclear_hamiltonian(
        n_modes: int, 
        omega: float = 1.0, 
        interactions=None, 
        time=None
):

    """
    Args:
        interactions : list of dicts, each with:
            'type': 'pairing' or 'spinorbit'
            'strength': float
            'time_dependednt': bool

        time        : for time dependednt terms

    """

    if interactions is None:
        interactions = []

    # Start from the free hamiltonian
    H = build_free_qho(n_modes, omega)

    for term in interactions:
        strength = term['strength']

        if term.get('time_dep', False) and time is not None:
            strength *= np.sin(time)

        if np.isclose(strength, 0.0):
            continue


        interaction_type = term['type'].lower()    
        if interaction_type == 'pairing':
            H += build_pairing_interaction(n_modes, strength)
        elif interaction_type == 'spinorbit':
            H += build_spinorbit_interaction(n_modes, strength)
        else:
            raise ValueError(f"UNKNOWN INTERACTION TYPE: {interaction_type}")



    # validation only checks Qiskit Conversion and exact diagonalization benchmarks

    qiskit_op = to_qiskit_validation_operator(H, n_modes)
    exact_eigenvalues = np.linalg.eigvalsh(qiskit_op.to_matrix()).tolist()


    metadata = {

            "n_qubits": n_modes,
            "n_terms" : len(H.terms),
            "exact_eigenvalues": exact_eigenvalues,
            "qiskit_validation_operator": qiskit_op,   
        }

    return H, metadata 





# ------------------------------ UTILITY: LIST PREDEFINED HAMILTONIANS ------------------------------

def list_hamiltonians():

    """
    PRINT ALL AVAILABLE PREDEFINED HAMILTONIANS

    """

    print("AVAILABLE PREDEFINED HAMILTONIANS")
    print("=" * 50)

    for name, config in predefined_hamiltonians.items():

        print(f"\n [{name}]")
        print(f" Phenomenon : {config['phenomenon']}")
        print(f" Parameters : {config['paramters']}")
        print(f" Modes      : {config['n_modes']}")
       
