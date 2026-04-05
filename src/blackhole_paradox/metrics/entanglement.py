from __future__ import annotations

import numpy as np


def reduced_density_matrix(
    statevector: np.ndarray,
    keep_qubits: list[int],
    num_qubits: int,
) -> np.ndarray:
    """
    Compute the reduced density matrix rho_keep by tracing out all qubits
    except those listed in keep_qubits.

    Qubit ordering convention:
    - statevector has size 2**num_qubits
    - qubits are indexed [0, 1, ..., num_qubits-1]

    This function is intended for small toy systems only.
    """
    state = np.asarray(statevector, dtype=complex)

    if state.ndim != 1:
        raise ValueError("statevector must be a 1D array")

    if len(state) != 2**num_qubits:
        raise ValueError("statevector length must be 2**num_qubits")

    norm = np.linalg.norm(state)
    if norm == 0:
        raise ValueError("statevector must be non-zero")

    state = state / norm

    keep_qubits = sorted(keep_qubits)
    if any(q < 0 or q >= num_qubits for q in keep_qubits):
        raise ValueError("keep_qubits contains an invalid qubit index")

    trace_qubits = [q for q in range(num_qubits) if q not in keep_qubits]

    dims = [2] * num_qubits
    psi_tensor = state.reshape(dims)

    perm = keep_qubits + trace_qubits
    psi_perm = np.transpose(psi_tensor, axes=perm)

    dim_keep = 2 ** len(keep_qubits)
    dim_trace = 2 ** len(trace_qubits)

    psi_matrix = psi_perm.reshape(dim_keep, dim_trace)
    # Use einsum for numerical robustness across BLAS backends.
    rho = np.einsum("ik,jk->ij", psi_matrix, psi_matrix.conj())
    return rho


def von_neumann_entropy(rho: np.ndarray, base: float = 2.0) -> float:
    """
    Compute the von Neumann entropy:
        S(rho) = -Tr(rho log rho)

    Default base=2 gives entropy in bits.
    """
    rho = np.asarray(rho, dtype=complex)

    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("rho must be a square matrix")

    eigvals = np.linalg.eigvalsh(rho)
    eigvals = np.real_if_close(eigvals)
    eigvals = np.clip(eigvals, 0.0, 1.0)

    nonzero = eigvals[eigvals > 1e-12]
    if len(nonzero) == 0:
        return 0.0

    if base == 2.0:
        logs = np.log2(nonzero)
    else:
        logs = np.log(nonzero) / np.log(base)

    entropy = -np.sum(nonzero * logs)
    return float(np.real_if_close(entropy))


def subsystem_entropy(
    statevector: np.ndarray,
    keep_qubits: list[int],
    num_qubits: int,
) -> float:
    """
    Compute the entanglement entropy of a subsystem for a pure global state.
    """
    rho = reduced_density_matrix(
        statevector=statevector,
        keep_qubits=keep_qubits,
        num_qubits=num_qubits,
    )
    return von_neumann_entropy(rho)


def linear_entropy(
    rho: np.ndarray,
) -> float:
    """
    Compute the linear entropy:
        S_L = 1 - Tr(rho^2)

    This is a simpler mixedness/entanglement proxy.
    """
    rho = np.asarray(rho, dtype=complex)

    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("rho must be a square matrix")

    purity = np.real_if_close(np.einsum("ij,ji->", rho, rho))
    return float(1.0 - purity)


def entanglement_summary(
    statevector: np.ndarray,
    subsystem_qubits: list[int],
    num_qubits: int,
) -> dict:
    """
    Frontend-friendly entanglement summary for a chosen subsystem.
    """
    rho = reduced_density_matrix(
        statevector=statevector,
        keep_qubits=subsystem_qubits,
        num_qubits=num_qubits,
    )

    return {
        "subsystem_qubits": subsystem_qubits,
        "von_neumann_entropy": subsystem_entropy(
            statevector=statevector,
            keep_qubits=subsystem_qubits,
            num_qubits=num_qubits,
        ),
        "linear_entropy": linear_entropy(rho),
        "note": (
            "Higher subsystem entropy indicates the information is more "
            "delocalized and entangled with the rest of the system."
        ),
    }