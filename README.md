<h1  align="center"> 
  QUANTUM HARMONIC OSCILLATOR SIMULATION ENGINE  (QIntern'26) 
</h1>

- Quantum Harmonic Oscillator (QHO) nuclear vibration simulation module.
- For QIntern 2026 (Project qi26_21).
- This project implements a modular Quantum Harmonic Oscillator (QHO) simulation engine that models simplified nuclear vibrational systems,
- And performs ground-state estimation using VQE, and prepares quantum circuits for execution on multiple quantum computing platforms through an OpenQASM2-based hardware interface.

---

## Features:

- Modular Hamiltonian construction using OpenFermion
- Config-driven interaction model
- Free Quantum Harmonic Oscillator Hamiltonian
- Pairing, and Spin-Orbit interaction support
- Multiple variational ansätze
- Cirq-based VQE implementation
- Exact diagonalization benchmark
- State fidelity computation
- Variational bound verification
- QASM2 circuit export
- PyQASM validation pipeline
- Hardware-ready architecture (IBM / Google / AWS)

---
## Project Architecture:

The QHO Simulation Engine follows a modular pipeline that separates Hamiltonian construction, variational optimization, validation, and hardware execution.

```text
                        User Configuration
                    (Config Dictionary / JSON)
                                   │
                                   ▼
                    Hamiltonian Construction
                         (OpenFermion)
                                   │
                                   ▼
                    QubitOperator Representation
                                   │
               ┌───────────────────┴───────────────────┐
               │                                       │
               ▼                                       ▼
     Main Execution Path                     Validation Path
               │                                       │
               ▼                                       ▼
      Cirq PauliSum Conversion              Qiskit SparsePauliOp
               │                                       │
               ▼                                       ▼
         Variational Ansatz                     Exact Validation
          (Cirq Circuit)                    (Statevector / Estimator)
               │
               ▼
        Cirq Simulator (VQE)
               │
               ▼
     Classical Optimizer (COBYLA)
               │
               ▼
      Ground-State Energy & Parameters
               │
               ▼
     OpenQASM 2.0 Circuit Export
               │
               ▼
         PyQASM Validation
               │
               ▼
     Quantum Hardware Interface
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
 IBM Quantum  Google   Amazon Braket
```

### Main Components:

| Component | Description |
|-----------|-------------|
| **Hamiltonian Builder** | Constructs the nuclear Hamiltonian as an OpenFermion `QubitOperator` from the user-defined configuration. |
| **Ansatz Generator** | Builds parameterized Cirq quantum circuits for the Variational Quantum Eigensolver (VQE). |
| **VQE Solver** | Optimizes the variational parameters using a classical optimizer (COBYLA) with the Cirq simulator. |
| **Validation Layer** | Performs exact diagonalization and additional validation checks to verify simulation correctness. |
| **QASM Export** | Converts the optimized quantum circuit into OpenQASM 2.0 format. |
| **PyQASM Validation** | Validates the generated OpenQASM program before hardware execution. |
| **Hardware Interface** | Provides a backend-ready pathway for execution on IBM Quantum, Google Quantum AI, and Amazon Braket. |

---

## Folder Structure:

```text
QINTERN26_21/
│
├── hamiltonian/
│   ├── __init__.py
│   └── nuclear_hamiltonian.py
│
├── ansatz/
│   ├── __init__.py
│   └── nuclear_ansatz.py
│
├── solver/
│   ├── __init__.py
│   ├── vqe_solver.py
│   └── pyqasm_utils.py
│
├── exports/
│   └── oscillator_ansatz.qasm
│
├── notebooks/
│   └── qho_engine_demo.ipynb
│
├── results/
│   └── (auto-generated at runtime)
│
├── tests/
│   ├── __init__.py
│   ├── test_hamiltonian.py
│   └── test_vqe.py
│
├── .gitignore
├── README.md
└── requirements.txt
```
## How to Run This Locally:
### Setup Steps 

```bash
# 1. Clone the repository
git clone https://github.com/deeepakchauhan/qintern26_21_qho_module.git
cd qintern26_21_qho_module

# 2. Create a virtual environment (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Run the unit tests to confirm everything works
pytest tests/ -v

# 5. Launch Jupyter and open the demo notebook
jupyter notebook notebooks/qho_engine_demo.ipynb

Running all cells in `qho_engine_demo.ipynb` top to bottom will reproduce:
- Hamiltonian construction and exact-diagonalization benchmark
- VQE runs on both the Cirq and Qiskit paths, with cross-check comparison
- Convergence plots and optimal-parameter reporting
- QASM2 export and PyQASM validation
```
## References:

- Qiskit: https://www.ibm.com/quantum/qiskit
- Peruzzo et al. 2014 (Original VQE paper):
  arXiv: https://arxiv.org/abs/1304.3061
  DOI:   https://doi.org/10.1038/ncomms5213
- Tilly et al. 2022 (VQE review):
  arXiv: https://arxiv.org/abs/2111.05176
  DOI:   https://doi.org/10.1016/j.physrep.2022.08.003
- Ring & Schuck (The Nuclear Many-Body Problem) 
  Publisher: https://link.springer.com/book/9783540212065
- OpenFermion documentation: https://quantumai.google/openfermion
- Cirq documentation: https://quantumai.google/cirq
- PyQASM: https://pypi.org/project/pyqasm/
