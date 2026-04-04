import os
import argparse
import logging
from .github_api import GithubPullRequest, GithubRelease

def run():
    parser = argparse.ArgumentParser(description="GitHub Release on PR Label")
    parser.add_argument("-t", "--token", required=True, help="GitHub Token")
    parser.add_argument(
        "-p", "--pull-request-id", required=True, type=int, help="PR ID"
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["validate", "release"],
        default="validate",
        help="Execution mode",
    )
    parser.add_argument(
        "-r",
        "--repository",
        default=os.getenv("GITHUB_REPOSITORY"),
        help="GitHub Repository",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    logger = logging.getLogger(__name__)

    # 1. Fetch and Assess PR
    pr = GithubPullRequest(args.repository, args.token, args.pull_request_id)
    pr.assess_for_release()

    # 2. Prepare Version
    release = GithubRelease(args.repository, args.token, pr.release_type)
    release.get_latest_release()
    release.calculate_version()

    # 3. Handle Modes
    if args.mode == "validate":
        status_icon = "✅" if pr.release_eligible else "❌"
        summary = (
            f"### Release Eligibility Summary {status_icon}\n"
            f"- **Branch Check**: {pr.assessment_results['branch']}\n"
            f"- **Labels Check**: {pr.assessment_results['labels']}\n"
        )
        if pr.release_eligible:
            summary += f"- **Proposed Tag**: `{release.new_tag}` ({pr.release_type})\n"
            summary += f"  - WARNING: This tag is calculated based on the latest release and PR changes. Please verify before merging!\n"
            summary += f"    You can use `/validate-for-release` command via PR comment to trigger a re-assessment.\n"

        pr.add_comment(summary)
        logger.info("Comment added to PR.")

    elif args.mode == "release":
        if pr.release_eligible and pr.is_merged:
            logger.info(f"Creating release {release.new_tag}...")
            release.create_release(
                tag_name=release.new_tag, commit_sha=pr.merge_commit_sha
            )
            logger.info("Release created successfully.")
        else:
            if not pr.is_merged:
                logger.warning("PR is not merged. Skipping release.")
            if not pr.release_eligible:
                logger.warning("PR is not eligible for release. Skipping.")


if __name__ == "__main__":
    run()
