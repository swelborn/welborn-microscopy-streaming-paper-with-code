import json
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np
import psutil
from pydantic import ValidationError

from .schemas import AnalysisConfig, Config


# Load and validate JSON configuration
def load_and_validate_config_json(file_path: Path) -> Config:
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return Config(**data)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}.")
        exit(1)
    except ValidationError as e:
        print(f"Error: Configuration validation failed. {e}")
        exit(1)


# Load and validate JSON configuration
def load_and_validate_analysis_json(file_path: Path) -> AnalysisConfig:
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return AnalysisConfig(**data)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}.")
        exit(1)
    except ValidationError as e:
        print(f"Error: Configuration validation failed. {e}")
        exit(1)


def check_memory_usage(threshold=0.9):
    """Check if the memory usage exceeds the given threshold."""
    mem = psutil.virtual_memory()
    return mem.percent >= threshold * 100


def check_for_invalid_values(
    name: str, array: np.ndarray
) -> List[Tuple[int, int, int, int]]:
    invalid_values: List[Tuple[int, int, int, int]] = []
    invalid_indices = np.argwhere(np.isnan(array) | np.isinf(array))

    if invalid_indices.size > 0:
        print(f"{name} contains NaN or Inf values.")
        invalid_values = [tuple(idx) for idx in invalid_indices]

    return invalid_values


def check_for_zero_slices(name: str, array: np.ndarray) -> List[Tuple]:
    """
    Check if any 2D slice in the reciprocal space of a 4D data cube contains all zeroes.

    Parameters:
        arr (numpy.ndarray): A 4D array where the first two dimensions are real space
                                  and the last two dimensions are reciprocal space.

    Returns:
        zero_slices (list): List of tuples indicating the indices of all-zero slices.
    """
    # Initialize an empty list to store the indices of all-zero slices
    zero_slices: List[tuple] = []

    # Get the shape of the 4D data cube
    ny, nx, _, _ = array.shape

    # Loop through the real-space dimensions
    for i in range(ny):
        for j in range(nx):
            # Extract the 2D slice in reciprocal space
            slice_2D = array[i, j, :, :]

            # Check if all elements in the 2D slice are zero
            if np.all(slice_2D == 0):
                zero_slices.append((i, j))

    # Print a message if all-zero slices are found
    if zero_slices:
        print(f"{name} has all-zero slices at real-space indices: {zero_slices}")

    return zero_slices


def replace_invalid_values(
    array: np.ndarray, invalid_indices: List[Tuple[int, int, int, int]]
) -> np.ndarray:
    for idx in invalid_indices:
        array[idx] = 0
    return array


def replace_zero_slices(
    array: np.ndarray, zero_slices: List[Tuple[int, int]]
) -> np.ndarray:
    ny, nx, _, _ = array.shape

    for i, j in zero_slices:
        neighbors = []

        if i > 0:
            neighbors.append(array[i - 1, j, :, :])
        if i < ny - 1:
            neighbors.append(array[i + 1, j, :, :])
        if j > 0:
            neighbors.append(array[i, j - 1, :, :])
        if j < nx - 1:
            neighbors.append(array[i, j + 1, :, :])

        array[i, j, :, :] = np.mean(neighbors, axis=0)

    return array
