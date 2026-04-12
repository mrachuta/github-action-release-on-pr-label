## Project name
Release on PR Label GitHub Action - a GitHub action to create releases based on PR labels.

## Table of contents
- [Project name](#project-name)
- [Table of contents](#table-of-contents)
- [General info](#general-info)
  - [Features](#features)
- [Technologies](#technologies)
- [Setup](#setup)
  - [Inputs](#inputs)
  - [Outputs](#outputs)
  - [Local Testing](#local-testing)
  - [Example Workflow](#example-workflow)
    - [Release validation and creation - simple usage](#release-validation-and-creation---simple-usage)
    - [Release validation and creation - more complex usage](#release-validation-and-creation---more-complex-usage)
- [Usage](#usage)
  - [Labels](#labels)
  - [Example flow](#example-flow)
    - [Success State](#success-state)
    - [Failure State](#failure-state)
- [License](#license)


## General info
This GitHub Action automates the creation of releases based on pull request labels. It can assess if a PR is eligible for a release, add comments with summaries, and create a new tag and release once the PR is merged.

### Features

- **Validation**: Checks if the target branch matches the default branch.
- **Versioning**: Calculates the new version based on labels (`release:major`, `release:minor`, `release:patch`) or accepts a custom tag.
- **Modes**:
  - `validate`: Analyzes the PR, posts a summary comment about release eligibility, and outputs the calculated tag.
  - `release`: Creates a GitHub release/tag if the PR is merged and eligible.
- **Automated Notes**: Generates release notes automatically via GitHub's API.

## Technologies
* Python3
* Bash
* Docker

## Setup

### Inputs

| Input             | Description                                          | Required | Default |
|-------------------|------------------------------------------------------|----------|---------|
| `token`           | GitHub access token (usually `secrets.GITHUB_TOKEN`) | Yes      | N/A     |
| `repository`      | The full repository name (e.g., `owner/repo`)        | Yes      | N/A     |
| `pull_request_id` | The ID of the pull request to process                | Yes      | N/A     |
| `mode`            | Execution mode: `validate` or `release`              | Yes      | N/A     |
| `debug`           | Enable debug logging via flag `--debug`              | No       | ``      |
| `custom_tag`      | Custom tag to use in release mode (skips calculation)| No       | ``      |

### Outputs

| Output            | Description          |
|------------------ |----------------------|
| `new_tag`         | The proposed new tag |

### Local Testing

You can run the script locally if you have Python installed:

```bash
pip install requests=="2.*" pytest=="9.*"
pytest tests/test_github.py
python3 release-on-pr-label.py --token YOUR_TOKEN --repository owner/repo --pull-request-id 123 --mode comment
```

### Example Workflow

#### Release validation and creation - simple usage

Create a file named `.github/workflows/release-creation.yml` in your repository:

```yaml
name: Release creation build
run-name: >
  Release job triggered by ${{ case(github.event_name == 'pull_request', 'change', 'comment') }} 
  on pull request #${{ github.event.pull_request.number || github.event.issue.number }}

on:
  pull_request:
    branches: [master]
    types: [opened, labeled, unlabeled, closed]
  issue_comment:
    types: [created]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  pull-requests: write
  contents: write
  statuses: write

jobs:
  validate-for-release:
    if: |
      (
        github.event_name == 'pull_request' &&
          (
            github.event.action == 'opened' ||
            github.event.action == 'labeled' ||
            github.event.action == 'unlabeled'
          )
      ) || (
        github.event_name == 'issue_comment' &&
        startsWith(
          github.event.comment.body, '/validate-for-release'
        )
      )
    runs-on: ubuntu-latest
    outputs:
      new_tag: ${{ steps.validate_for_release.outputs.new_tag }}
    steps:
      - name: Validate for release
        uses: mrachuta/github-action-release-on-pr-label@master
        id: validate_for_release
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          pull_request_id: ${{ github.event.pull_request.number || github.event.issue.number }}
          mode: validate
          debug: ${{ runner.debug }}

  create-release:
    needs: validate-for-release
    if: |
      github.event_name == 'pull_request' && 
      github.event.action == 'closed' && 
      github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Create release
        uses: mrachuta/github-action-release-on-pr-label@master
        id: create_release
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          pull_request_id: ${{ github.event.pull_request.number }}
          mode: release
          custom_tag: ${{ needs.validate-for-release.outputs.new_tag }}
          debug: ${{ runner.debug }}

```
#### Release validation and creation - more complex usage

Create a file named `.github/workflows/cd.yml` in your repository:

```yaml
name: Continuous Delivery build
run-name: >
  Release job triggered by ${{ github.event_name }} 
  on pull request #${{ github.event.pull_request.number }}

on:
  pull_request:
    branches: 
      - master
    types: 
      - closed

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  pull-requests: write
  contents: write
  statuses: write

jobs:
  validate-for-release:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Validate for release
        uses: mrachuta/github-action-release-on-pr-label@master
        id: validate_for_release
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          pull_request_id: ${{ github.event.pull_request.number }}
          mode: validate
          debug: ${{ runner.debug }}
    outputs:
      new_tag: ${{ steps.validate_for_release.outputs.new_tag }}

  do-something-with-tag:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    needs: 
      - validate-for-release
    steps:
      - name: Print info
        run: "tar -cvf my-app-${{ needs.validate-for-release.outputs.new_tag }}.tar my-app"

  create-release:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    needs: 
      - validate-for-release
    steps:
      - name: Create release
        uses: mrachuta/github-action-release-on-pr-label@master
        id: create_release
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          pull_request_id: ${{ github.event.pull_request.number }}
          mode: release
          custom_tag: ${{ needs.validate-for-release.outputs.new_tag }}
          debug: ${{ runner.debug }}

```

## Usage

### Labels

The action expects exactly one of the following labels to be present on the pull request:
- `release:major`: Increments the major version (e.g., `v1.2.3` -> `v2.0.0`).
- `release:minor`: Increments the minor version (e.g., `v1.2.3` -> `v1.3.0`).
- `release:patch`: Increments the patch version (e.g., `v1.2.3` -> `v1.2.4`).
- if there is no release yet, starting point is on `v0.0.0`.

### Example flow

This action provides interactive feedback during the development process:

1.  **Automated Validation**: Whenever you add or remove a label (e.g., `release:minor`), the action automatically validates the PR and posts an eligibility summary.
2.  **Manual Re-run**: If you want to force a refresh of the status, simply comment `/validate-for-release` on the PR.
3.  **Status Comments**: The action posts a markdown summary to the PR, indicating if the branch is correct and if exactly one release label is present.

#### Success State
> ### Release Eligibility Summary ✅
> - **Branch Check**: Target branch matches default branch.
> - **Labels Check**: Found exactly one release label: *release:minor*.
> - **Proposed Tag**: `v1.3.0` (minor)

#### Failure State
> ### Release Eligibility Summary ❌
> - **Branch Check**: Target branch (feature-branch) != default (master).
> - **Labels Check**: Found 0 release labels (expected 1).


## License

MIT
