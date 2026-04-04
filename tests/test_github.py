import pytest
from src.github_api import GithubRelease

@pytest.fixture
def patch_release():
    return GithubRelease("test/repo", "token", "patch")

def test_calculate_version_patch(patch_release):
    patch_release.latest_tag = "v1.2.3"
    patch_release.release_type = "patch"
    patch_release.calculate_version()
    assert patch_release.new_tag == "v1.2.4"

def test_calculate_version_minor(patch_release):
    patch_release.latest_tag = "v1.2.3"
    patch_release.release_type = "minor"
    patch_release.calculate_version()
    assert patch_release.new_tag == "v1.3.0"

def test_calculate_version_major(patch_release):
    patch_release.latest_tag = "v1.2.3"
    patch_release.release_type = "major"
    patch_release.calculate_version()
    assert patch_release.new_tag == "v2.0.0"

def test_calculate_version_invalid_tag(patch_release):
    patch_release.latest_tag = "invalid"
    patch_release.release_type = "patch"
    patch_release.calculate_version()
    assert patch_release.new_tag == "v0.1.0" # Fallback
