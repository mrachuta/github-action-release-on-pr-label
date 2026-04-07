import re
import requests
import logging
import os

GITHUB_API_URL = "https://api.github.com"
# TODO: Update API version
GITHUB_API_VERSION = "2022-11-28"

logger = logging.getLogger(__name__)


class GithubPullRequest:
    def __init__(self, repository, token, pull_request_id):
        self.repository = repository
        self.pull_request_id = pull_request_id
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        self.default_branch = ""
        self.target_branch = ""
        self.is_merged = False
        self.merge_commit_sha = ""
        self.head_sha = ""
        self.allowed_labels = [
            "release:patch",
            "release:minor",
            "release:major",
        ]
        self.labels = []
        self.branch_assessment = False
        self.labels_assessment = False
        self.release_type = None
        self.assessment_results = {}
        self.release_eligible = False
        self._get_details()

    def _get_details(self):
        url = f"{GITHUB_API_URL}/repos/{self.repository}/pulls/{self.pull_request_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        self.default_branch = data.get("base", {}).get("repo", {}).get("default_branch")
        self.target_branch = data.get("base", {}).get("ref")
        self.is_merged = data.get("merged", False)
        self.merge_commit_sha = data.get("merge_commit_sha")
        self.head_sha = data.get("head", {}).get("sha")
        self.labels = [label.get("name") for label in data.get("labels", [])]

    def assess_for_release(self):
        if self.default_branch == self.target_branch:
            self.branch_assessment = True
            self.assessment_results["branch"] = "Target branch matches default branch."
        else:
            self.assessment_results[
                "branch"
            ] = f"Target branch ({self.target_branch}) != default ({self.default_branch})."

        found_labels = list(set(self.allowed_labels) & set(self.labels))
        if len(found_labels) == 1:
            self.labels_assessment = True
            label = found_labels[0]
            self.release_type = label.split(":")[1]
            self.assessment_results[
                "labels"
            ] = f"Found exactly one release label: *{label}*."
        else:
            self.assessment_results[
                "labels"
            ] = f"Found {len(found_labels)} release labels (expected 1)."

        self.release_eligible = self.branch_assessment and self.labels_assessment

    def add_comment(self, comment):
        url = f"{GITHUB_API_URL}/repos/{self.repository}/issues/{self.pull_request_id}/comments"
        requests.post(url, headers=self.headers, json={"body": comment}).raise_for_status()

    def set_commit_status(self, state, description, context=None):
        if not self.head_sha:
            logger.warning("No head_sha found, cannot set commit status.")
            return

        if not context:
            context = os.environ.get("GITHUB_JOB", "Release Check")

        url = f"{GITHUB_API_URL}/repos/{self.repository}/statuses/{self.head_sha}"
        payload = {"state": state, "description": description, "context": context}
        requests.post(url, headers=self.headers, json=payload).raise_for_status()


class GithubRelease:
    def __init__(self, repository, token, release_type):
        self.repository = repository
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        self.release_type = release_type
        self.latest_tag = "v0.0.0"
        self.new_tag = None

    def get_latest_release(self):
        url = f"{GITHUB_API_URL}/repos/{self.repository}/releases/latest"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            self.latest_tag = response.json().get("tag_name", "v0.0.0")
        else:
            logger.info("No previous release found, starting from v0.0.0")

    def calculate_version(self):
        pattern = r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$"
        match = re.match(pattern, self.latest_tag)

        if not match:
            logger.error(
                f"Latest tag {self.latest_tag} does not match semantic versioning."
            )
            return False

        major, minor, patch = map(int, match.groups())

        if self.release_type == "major":
            self.new_tag = f"v{major + 1}.0.0"
        elif self.release_type == "minor":
            self.new_tag = f"v{major}.{minor + 1}.0"
        elif self.release_type == "patch":
            self.new_tag = f"v{major}.{minor}.{patch + 1}"

        return True

    def create_release(self, tag_name, commit_sha):
        url = f"{GITHUB_API_URL}/repos/{self.repository}/releases"
        payload = {
            "tag_name": tag_name,
            "target_commitish": commit_sha,
            "name": tag_name,
            "body": f"Automated release {tag_name}",
            "generate_release_notes": True,
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
