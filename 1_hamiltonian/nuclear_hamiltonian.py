"""
NUCLEAR HAMILTONIAN ENGINE :

- Free QHO with n-modes and arbitrary 'w' : represents single particle basis
- Pairing Interaction : represents the most universal hamiltonian
- Quadruple Interaction (deformed nuclei, collective modes) : needed for heavier nuclei
- Physical Units: MeV throughout 

"""

import qiskit
from qiskit.quantum_info import SparsePauliOp
import numpy as np



# ------------------------------ PREDEFINED HAMILTONIANS ------------------------------
predefined_hamiltonians = {

    'free_oscillators': {
        'parameters' : {'omega': 1.0},
        'n_modes'    : 2,
    },

    'qho_pairing': {
        'parameters' : {'omega': 1.0, 'coupling': 0.5},
        'n_modes'    : 2,
    },

    'qho_spinorbit': {
        'parameter' : {'omega': 1.0, 'kappa': 0.1},
        'n_modes'   : 2,
    },

    'qho_full': {
        'parameter' : {'omega': 1.0, 'coupling': 0.5, 'kappa': 0.1},
        "n_modes"   : 2,
    },
}



# ------------------------------ HELPER FUCNTIONS ------------------------------
"""reusable string-builders that correctly handle Qiskit's qubit-ordering convention"""


def _single_qubit_pauli(pauli_char, qubit_index, n_modes):
    """Place one Pauli Character on qubit_index, and indentity on others"""

    string = ["I"] * n_modes
    string[n_modes - 1 - qubit_index] = pauli_char

    return ''.join(string)

def _two_qubit_pauli(pi, pj, i, j, n_modes):
    """Place Pauli pi on qubit i and pj on qubit j, Identity elsewhere"""

    string = ["I"] * n_modes
    string[n_modes - 1 - i] = pi
    string[n_modes - 1 - j] = pj

    return ''.join(string)




# ------------------------------ LAYER 1: FREE QHO ------------------------------
def build_free_qho(n_modes, omega=1.0):

    """
    Free QHO for n single particle levels.

    Args: 
        n_modes: int - number of qubits
        omega: float - oscillator frequency

    Returns:
        SparsePauliOp
    
    """

    pauli_list = []
    for i in range(n_modes):
        pauli_list.append(('I' * n_modes, omega/2.0))
        pauli_list.append((_single_qubit_pauli('Z', i, n_modes), -omega / 2.0))

    return SparsePauliOp.from_list(pauli_list).simplify()




# ------------------------------ LAYER 2: PAIRING INTERACTION ------------------------------
def build_pairing_interaction(n_modes, coupling):

    """
    Nuclear pairing interaction: H_pair = -G/2 * Σᵢ<ⱼ (XXᵢⱼ + YYᵢⱼ)

    - Encodes pair-hopping: aᵢ†aⱼ + aⱼ†aᵢ in qubit language.
    - Pairing lowers the ground state energy.

    """

    pauli_list = []
    for i in range(n_modes):
        for j in range(i+1, n_modes):

            pauli_list.append(
                (_two_qubit_pauli('X', 'X', i, j, n_modes), -coupling / 2.0)
            )
            pauli_list.append(
                (_two_qubit_pauli('Y', 'Y', i, j, n_modes), -coupling / 2.0)
            )

    return SparsePauliOp.from_list(pauli_list).simplify()




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

    pauli_list = []
    for i in range(n_modes):
        pauli_list.append(
                (_single_qubit_pauli('Z', i, n_modes), -kappa)
        )

    return SparsePauliOp.from_list(pauli_list).simplify()




# ------------------------------ FULL HAMILTONIAN: COMBINING ALL THE ABOVE LAYERS ------------------------------
def build_nuclear_hamiltonian(n_modes, omega=1.0, interactions=None, time=None):

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

    H = build_free_qho(n_modes, omega)

    for term in interactions:
        strength = term['strength']

        if term.get('time-dep') and time is not None:
            strength += np.sin(time)

        if np.isclose(strength, 0.0):
            continue

        if term['type'] == 'pairing':
            H = (H + build_pairing_interaction(n_modes, strength)).simplify()
        elif term['type'] == 'spinorbit':
            H= (H + build_spinorbit_interaction(n_modes, strength)).simplify()
        else:
            raise ValueError(f"UNKNOWN INTERACTION TYPE: {term['type']}")

    return H
