import hashlib
import os
import warnings
import numpy as np
import pandas as pd
import s3fs
from filelock import Timeout, FileLock
from joblib import Parallel, delayed


def serialize_candidate(cand: dict):
    #return "".join([f"{key}:{np.round(cand[key],6):.6f}" for key in sorted(cand.keys()) if len(key) > 0])
    #return "".join([f"{key}:{cand[key]:.4f}" for key in sorted(cand.keys()) if len(key) > 0])
    return "".join([f"{key}:{np.round(cand[key],4)}" for key in sorted(cand.keys()) if len(key) > 0])


class LocalCache(object):
    def __init__(self, path_base):
        self._path_base = os.path.expanduser(path_base)
        if not os.path.exists(self._path_base):
            os.makedirs(self._path_base)

    def _encode(self, cand_serialized):
        return hashlib.sha256(cand_serialized.encode("utf-8")).hexdigest()

    def get(self, n_players: int, cand):
        marshalled = serialize_candidate(cand)
        hashed = self._encode(marshalled)
        path_cand = os.path.join(self._path_base, f"game-{n_players}", f"game-{n_players}-{hashed}.txt")
        if not os.path.exists(path_cand):
            return None
        else:
            with open(path_cand, "r") as handle_read:
                found = None
                while (line := handle_read.readline().rstrip()):
                    if len(line) < 1:
                        continue
                    rep, phi_min = line.split(" ")
                    if marshalled == rep:
                        found = phi_min
                        break
                if found is None:
                    warnings.warn("Hash matched but did not find entry for candidate")
                    return None
                return float(found)

    def update(self, n_players, population):
        def process_update(cand, phi):
            if phi is None:
                return
            phi = float(phi)
            marshalled = serialize_candidate(cand)
            hashed = self._encode(marshalled)
            name_file = f"game-{n_players}-{hashed}.txt"
            path_base_locks = os.path.join(self._path_base, f"game-{n_players}-locks")
            if not os.path.exists(path_base_locks):
                os.makedirs(path_base_locks)
            path_base_game = os.path.join(self._path_base, f"game-{n_players}")
            if not os.path.exists(path_base_game):
                os.makedirs(path_base_game)
            path_cand = os.path.join(path_base_game, name_file)
            path_lock = os.path.join(path_base_locks, name_file)
            lock = FileLock(path_lock, 10)
            with lock:
                # Search whether cand is already persisted
                if os.path.exists(path_cand):
                    with open(path_cand, "r") as handle:
                        if marshalled in handle.read():
                            return

                with open(path_cand, "a+") as handle:
                    handle.write(f"{marshalled} {phi}\n")

        Parallel(n_jobs=8)(delayed(process_update)(cand, phi) for (cand, phi) in population)



class CacheManager(object):
    def __init__(
        self,
        path_base,
        context: str = None,
        access_key: str = None,
        secret_key: str = None,
        path_remote_base: str = None,
        endpoint: str = None,
    ):
        self._path_base = os.path.expanduser(path_base)
        self._s3_access_key = access_key
        self._s3_secret_key = secret_key
        self._s3_base = (
            path_remote_base if path_remote_base is not None else "/homes/stier/cache/"
        )
        self._s3_endpoint = (
            endpoint if endpoint is not None else "https://share.pads.fim.uni-passau.de"
        )

        self._data_local = {}

        self._initialize_s3fs()

    def _load_local(self, n_players):
        path_evals = os.path.join(self._path_base, f"games-size-{n_players}.hd5")
        if not os.path.exists(path_evals):
            return

        self._data_local[n_players] = pd.read_hdf(path_evals, key="table")


    def get(self, n_players, candidate):
        self._load_local(n_players)
        if n_players not in self._data_local:
            return None

        df = self._data_local[n_players]
        return df[(df["n"] == n_players) & (df["key"] == serialize_candidate(candidate))]


    def put(self, population):
        pass

    def _initialize_s3fs(self):
        self._s3fs = None
        if self._s3_access_key is not None:
            self._ensure_base_path()

            self._s3fs = s3fs.S3FileSystem(
                key=self._s3_access_key,
                secret=self._s3_secret_key,
                use_ssl=True,
                client_kwargs={
                    "endpoint_url": self._s3_endpoint,
                },
            )

            """try:
                self._sync_from(self._s3fs, self._s3_base, self._path_base)
            except OSError as e:
                warnings.warn(
                    f"Connection issues with <{self._s3_endpoint}> when trying to sync cache data from S3: {str(e)}"
                )"""

    def _ensure_base_path(self):
        if not os.path.exists(self._path_base):
            try:
                os.makedirs(self._path_base)
            except Exception:
                warnings.warn(
                    f"Could not create base path '{self._path_base}' for cache manager."
                )