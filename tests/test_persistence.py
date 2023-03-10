import os

import numpy as np
import pytest
import uuid
from unittest.mock import patch

from shapleysearch.persistence import CacheManager, serialize_candidate


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
