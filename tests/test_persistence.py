import os

import numpy as np
import pytest
import uuid
from unittest.mock import patch

from shapleysearch.persistence import CacheManager, serialize_candidate, LocalCache
from shapleysearch.util import sample_base_payoff


@pytest.fixture
def unique_test_id():
    return str(uuid.uuid4())


@patch("s3fs.S3FileSystem.open", side_effect=open)
@patch("s3fs.S3FileSystem.ls", side_effect=os.listdir)
@patch("s3fs.S3FileSystem.exists", side_effect=os.path.exists)
def test_instantiate_with_s3fs_success(
        mock_s3fs_exists, mock_s3fs_ls, mock_s3fs_open, tmpdir, unique_test_id
):
    path_cache_local = tmpdir.mkdir(f"cache-{unique_test_id}")
    path_base_remote = tmpdir.mkdir(f"remote-{unique_test_id}")

    CacheManager(
        path_cache_local,
        access_key="my-key",
        secret_key="my-secret",
        path_remote_base=path_base_remote,
        endpoint="http://localhost/",
    )

@patch("s3fs.S3FileSystem.open", side_effect=open)
@patch("s3fs.S3FileSystem.ls", side_effect=os.listdir)
@patch("s3fs.S3FileSystem.exists", side_effect=os.path.exists)
def test_get_candidate_success(
        mock_s3fs_exists, mock_s3fs_ls, mock_s3fs_open, tmpdir, unique_test_id
):
    path_cache_local = tmpdir.mkdir(f"cache-{unique_test_id}")
    path_base_remote = tmpdir.mkdir(f"remote-{unique_test_id}")

    cm = CacheManager(
        path_cache_local,
        access_key="my-key",
        secret_key="my-secret",
        path_remote_base=path_base_remote,
        endpoint="http://localhost/",
    )
    cand = {"": 0, "a": 1, "b": 1, "ab": 0.5122539}

    cm.get(cand)


def test_serialize_candidates():
    cand = {"": 0, "a": 1, "b": 1, "ab": 0.5122539}
    marshalled = serialize_candidate(cand)
    print(marshalled)
    assert len(marshalled) > 3
    assert f"{cand['ab']:.4f}" in marshalled


def test_serialization_length():
    cand = sample_base_payoff(5)
    for group in cand:
        cand[group] = float(np.random.random())
    marshalled = serialize_candidate(cand)
    print(len(marshalled), len(marshalled.encode('utf-16')))


def test_local_cache(tmpdir):
    n_players = 5

    population = []
    for _ in range(20):
        cand = sample_base_payoff(n_players)
        for group in cand:
            cand[group] = float(np.random.random())
        population.append((cand, float(np.random.random())))

    path_cache_local = tmpdir.mkdir(f"cache")
    cm = LocalCache(path_cache_local)
    cm.update(n_players, population)

    hit = cm.get(n_players, population[0][0])
    print("Found hit", hit)

