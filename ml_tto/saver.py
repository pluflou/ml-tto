from typing import Dict, Any
import h5py
import numpy as np
from pydantic import validate_call


class H5Saver:
    """
    Class to save and load dictionaries to and from HDF5 files.

    Methods:
    ------------------------
    save_to_h5: Saves a dictionary to an HDF5 file.
    load_from_h5: Loads a dictionary from an HDF5 file.
    """

    def __init__(self):
        """Initialize the H5Saver class.

        Arguments:
        ------------------------
        string_dtype: str, optional
            The encoding to use when saving string data. Default is 'utf-8'.
        """

        self.string_dtype = "utf-8"
        self.supported_types = (bool, int, float, np.integer, np.floating)

    @validate_call
    def save_to_h5(self, data: Dict[str, Any], filepath: str):
        """
        Save a dictionary to an HDF5 file.
        Arguments:
        ------------------------
        data: Dict[str, Any]
            The dictionary to save.
        filepath: str
            The path to save

        Returns:
        ------------------------
        None
        """

        dt = h5py.string_dtype(encoding=self.string_dtype)

        def recursive_save(d, f):
            for key, val in d.items():
                if key == "attrs":
                    f.attrs.update(val or h5py.Empty("f4"))
                elif isinstance(val, dict):
                    group = f.create_group(key, track_order=True)
                    recursive_save(val, group)
                elif isinstance(val, list):
                    if all(isinstance(ele, self.supported_types) for ele in val):
                        f.create_dataset(key, data=val, track_order=True)
                    elif isinstance(val, np.ndarray):
                        if val.dtype != np.dtype('O'):
                            f.create_dataset(key, data=val, track_order=True)
                    elif all(isinstance(ele, dict) for ele in val):
                        for i, ele in enumerate(val):
                            group = f.create_group(f"{key}/{i}", track_order=True)
                            recursive_save(ele, group)
                    else:
                        for i, ele in enumerate(val):
                            if isinstance(ele, str):
                                f.create_dataset(
                                    f"{key}/{i}", data=ele, dtype=dt, track_order=True
                                )
                            else:
                                f.create_dataset(
                                    f"{key}/{i}", data=str(ele), track_order=True
                                )
                elif isinstance(val, self.supported_types):
                    f.create_dataset(key, data=val, track_order=True)
                elif isinstance(val, np.ndarray):
                    if val.dtype != np.dtype('O'):
                        f.create_dataset(key, data=val, track_order=True)
                elif isinstance(val, str):
                    # specify string dtype to avoid issues with encodings
                    f.create_dataset(key, data=val, dtype=dt, track_order=True)
                else:
                    f.create_dataset(key, data=str(val), track_order=True)

        with h5py.File(filepath, "w") as file:
            recursive_save(data, file)

    def load_from_h5(self, filepath):
        """Convenience method to load a dictionary from an HDF5 file.

        Arguments:
        ------------------------
        filepath: str
            The path to the file to load.

        Returns:
        ------------------------
        dict
            The dictionary loaded from the file.
        """

        def recursive_load(f):
            d = {"attrs": dict(f.attrs)} if f.attrs else {}
            for key, val in f.items():
                if isinstance(val, h5py.Group):
                    d[key] = recursive_load(val)
                elif isinstance(val, h5py.Dataset):
                    if isinstance(val[()], bytes):
                        d[key] = val[()].decode(self.string_dtype)
                    else:
                        d[key] = val[()]
            return d

        with h5py.File(filepath, "r") as file:
            return recursive_load(file)
