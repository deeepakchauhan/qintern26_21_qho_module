"""
------------------------------- NUCLEAR HAMILTONIAN ENGINE ------------------------------ :

Covers different Hamiltonian Options:
- Quantum Oscillator : predefined QHO based nuclear hamiltonians
- Fermion Mapping: predefined fermionic hamiltonian
- Custom Hamiltonian: user-defined hamiltonians via pauli string input 

"""


from openfermion import QubitOperator
import numpy as np 




# --------------------------------------------- PREDEFINED HAMILTONIANS --------------------------------------------------

# -------------------------------------------- Quantum Oscillator Hamiltonians -------------------------------------------
predefined_hamiltonians = {

    'free_oscillators': {

        'option'        : 'oscillator',
        'parameters'    : {'omega': 1.0},
        'n_modes'       : 2,
        'phenomenon'    : 'Nuclear Vibrartions at rest',
        'interactions'  : [], 
    },

    'qho_pairing': {

        'option'       : 'oscillator',
        'parameters'    : {'omega': 1.0, 'coupling': 0.5},
        'n_modes'       : 2,
        'phenomenon'    : 'Nuclear Pairing',
        'interactions'  : [{'type': 'pairing', 'strength': 0.5, 'time_dep': False}],
    },

    'qho_spinorbit': {

        'option'        : 'oscillator',
        'parameters'    : {'omega': 1.0, 'kappa': 0.1},
        'n_modes'       : 2,
        'phenomenon'    : 'Nuclear Shell splitting',
        'intercations'  : [{'type': 'spinorbit', 'strength': 0.1, 'time_dep': False}],
    },

    'qho_full': {

        'option'        : 'oscillator',
        'parameters'    : {'omega': 1.0, 'coupling': 0.5, 'kappa': 0.1},
        "n_modes"       : 2,
        'phenomenon'    : 'Full nuclear single particle model',
        'interactions'  : [
            {'type': 'pairing', 'strength': 0.5, 'time_dep': False},
            {'type': 'spinorbit', 'strength': 0.1, 'time_dep': False},
        ], 
    },

    'qho_time_dependent': {

        'option'        : 'oscillator',
        'phenomenon'    : 'Driven nuclear excitation',
        'interaction'   : [{'type': 'pairing', 'strength': 0.5, 'time_dep': True}],
    },




    # ----------------------------------- Fermion Mapping Hamiltonian -----------------------------------
    'fermion_free': {

        'option'        : 'fermion',
        'parameters'    : {'epsilon': [0.5, 1.5]},
        'n_modes'       : 2,
        'phenomenon'    : 'Free fermionic nuclear levels',
    },

    'fermion_pairing': {

        'option'        : 'fermion',
        'parameters'    : {'epsilon': [0.5, 1.5], 'g': 0.5},
        'n_modes'       : 2,
        'phenomenon'    : 'fermionic nuclear paring',
    },

    'fermion_two_level': {

        'option'        : 'fermion',
        'parameters'    : {'epsilon1': 0.0, 'epsilon2': 1.0, 'v': 0.5},
        'n_modes'       : 2,
        'phenomenon'    : 'Two Level Nuclear shell  model',
    }
}





# ---------------------------------------- INTERNAL HELPER FUNCTIONS ----------------------------------------
def _z_term(i):

    """
    - Pauli Z operator on Qubit i
    - it represents single level energy occupation

    """
    return QubitOperator(f'Z{i}')

def _xx_term(i,j):

    """
    - Tensor product of Pauli X on i and Pauli X on j
    - it represents a part of pair - hopping operator

    """
    return QubitOperator(f'Z{i} Z{j}')

def _yy_term(i, j):

    """
    - tensor product of Pauli Y on i and Pauli Y on j
    - represnts the other half of the pair - hopping operator

    """
    return QubitOperator(f"Y{i} Y{j}")

def _zz_term(i, j):

    """
    - Tensor product of Z on i and Z on j
    - it represents the two body interaction energy between nucleons in different energy levels

    """
    return QubitOperator(f'Z{i} Z{j}')





# ----------------------------------- OSCILLATOR HAMILTONIANS -----------------------------------
def build_free_qho(n_modes, omega=1.0):

    """
    Args:
        n_modes : number of qubits
        omega   : 

    Returns:
        QubitOperator

    """

    H = QubitOperator()
    for i in range (n_modes):
        H += QubitOperator('', omega/2)
        H += -omega / 2.0 * _z_term(i)

    return H



def build_pairing_interaction(n_modes, coupling):

    H = QubitOperator()
    for i in range(n_modes):
        for j in range(i + 1, n_modes):
            H += -coupling / 2.0 * _xx_term(i,j)
            H += -coupling / 2.0 * _yy_term(i,j)

    return H



def build_spinorbit_interaction(n_modes, kappa):

    H = QubitOperator()
    for i in range(n_modes):
        H += -kappa * _z_term(i)

    return H 




def build_oscillator_hamiltonian(n_modes, omega=1.0, interactions=None, time=None):

    """
    - This represents the combined hamiltonian oscillator
    - combines free QHO + any interaction layers

    """


    if interactions is None:
        interactions = []

    H = build_free_qho(n_modes, omega)

    for term in interactions:
        strength = term['strength']

        if term.get('time_dep', False) and time is not None:
            strength = strength * np.sin(time)

        if np.isclose(strength, 0.0):
            continue

        if term['type'] == 'pairing':
            H += build_pairing_interaction(n_modes, strength)
        elif term['type'] == 'spinorbit':
            H += build_spinorbit_interaction
        else:
            raise ValueError(f"Unknown Interaction: '{term['type']}' ")


    return H 






# ---------------------------------------- FERMION MAPPING HAMILTONIAN ----------------------------------------

def build_fermion_free(n_modes, epsilon):

    H = QubitOperator()
    for i in range(n_modes):
        H += QubitOperator('', epsilon[i]/2)
        H += -epsilon[i] / 2.0 * _z_term(i)

    return H


def build_fermion_pairing(n_modes, epsilon, g):

    """
    Args:
        epsilon : single particle energies
        g       : pairing strength

    """

    H = QubitOperator()
    for i in range(n_modes):
        for j in range(i+1, n_modes):

            H += -g / 2.0 * _xx_term(i,j)
            H += -g / 2.0 * _yy_term(i,j)

    return H




def build_fermion_two_level(epsilon1, epsilon2, v):

    """
    H = epsilon1 * n_0 + epsilon2 * n_1 + v * (XX + YY)

    Args:
        epsilon1    : energy of level 0
        epsilon2    : energy of level 1
        v           : coupling between levels

    """

    H = QubitOperator()

    H += QubitOperator('', epsilon1 / 2.0)
    H += -epsilon1 / 2.0 * _z_term(0)

    H += QubitOperator('', epsilon2 / 2.0)
    H += -epsilon2 / 2.0 * _z_term(1)

    H += v * _xx_term(0, 1)
    H += v * _yy_term(0, 1)

    return H



def build_fermion_hamiltonian(name, params):

    """
    Args:
        name    : 'fermion_free', 'fermion_pairing', 'fermion_two_level'
        params  : parameters for chosen hamiltonian


    Returns:
        QubitOperator, n_modes

    """

    if name == 'free_fermion':
        n_modes = len(params['epsilon'])
        return build_fermion_free(n_modes, params['epsilon']), n_modes

    elif name == 'fermion_pairing':
        n_modes = len(params['epsilon'])
        return build_fermion_pairing(n_modes, params['epsilon'], params['g']), n_modes

    elif name == 'fermion_two_level':
        return build_fermion_two_level(params['epsilon1'], params['epsilon2'], params['v']), 2

    else:
        raise ValueError(f"Unknown fermion Hamiltonian: , '{name}' ")





# --------------------------------------------- CUSTOM HAMILTONIAN ---------------------------------------------

def build_custom_hamiltonian(pauli_terms):

    """
    - User - defined Hamiltonian from a list of Pauli Terms

    Args:
        pauli_terms : list of tuples (pauli_string, coefficients)

    """

    if not pauli_terms:
        raise ValueError(
            "pauli_terms cannot be empty. "
            "Provide atleast one (pauli_string, coefficient) tuple." 
        )


    H = QubitOperator()
    for pauli_string, coefficient in pauli_terms:
        H += QubitOperator(pauli_string, coefficient)

    return H





# ---------------------------------------- Combining Oscillator + Fermionic + Custom Hamiltonian ----------------------------------------

def build_nuclear_hamiltonian(config):

    """
    Args:
        config : dict with keys
            'options'       : 'oscillator', 'fermion', 'custom'
            'name'          : predefined Hamiltonian name
            'n_modes'       : physical parameters
            'time'          : for time - dependent hamiltonians
            'custom_terms'  : for custom options 

    Returns:
        QubitOperator
        n_modes 
        metadeta

    """

    option = config.get('option', 'oscillator')

    if option == 'oscillator':
        name = config['name']
        preset = predefined_hamiltonians[name]
        params = config.get('params', preset['parameters'])
        n_modes = config.get('n_modes', preset['n_modes'])
        time = config.get('time', None)


        H = build_oscillator_hamiltonian(
            n_modes=n_modes,
            omega=params.get('omega', 1.0),
            interactions=preset['interactions'],
            time=time
        )


        metadata = {
            'option'        : 'oscillator',
            'name'          : name,
            'phenomenon'    : preset['phenomenon'],
            'n_modes'       : n_modes,
            'parameters'    : params,
        }

        return H, n_modes, metadata


    elif option == 'fermion':
        name = config['name']
        params = config.get('params', predefined_hamiltonians[name]['parameters'])
        H, n_modes = build_fermion_hamiltonian(name, params)
        preset = predefined_hamiltonians[name]


        metadata = {
            'option'        : 'fermion',
            'name'          : name,
            'phenomenon'    : preset['phenomenon'],
            'n_modes'       : n_modes,
            'parameters'    : params,
        }

        return H, n_modes, metadata

    elif option == 'custom':
        custom_terms = config.get('custom_terms', [])
        n_modes = config.get('n_modes', 2)
        H = build_custom_hamiltonian(custom_terms)


        metadata = {

            'option'        : 'custom',
            'name'          : 'user-defined',
            'phenomenon'    : 'Custom nuclear problem',
            'n_modes'       : n_modes,
            'parameters'    : {'custom_terms': custom_terms},
        }

        return H, n_modes, metadata

    else:
        raise ValueError(
            f"Unknown Option: '{option}'. " 
            f"Supported Only: 'Oscillator','Fermion', 'Custom' "
        )