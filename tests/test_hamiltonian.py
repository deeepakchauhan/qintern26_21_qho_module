"""
- Tests for nuclear_hamiltonian.py
- Tests QubitOperator output correctness against analytical eigenvalues

"""

import numpy as np
import pytest
from openfermion import get_sparse_operator
from 1_hamiltonian.nuclear_hamiltonian import (
    build_free_qho,
    build_pairing_interaction,
    build_nuclear_hamiltonian,

)