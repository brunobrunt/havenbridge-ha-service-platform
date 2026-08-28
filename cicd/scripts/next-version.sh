#!/usr/bin/env bash

# ---------------------------------------------------------------------------
# HavenBridge Semantic Version Calculator
# ---------------------------------------------------------------------------
#
# Purpose:
#   Determine the next HavenBridge semantic version from committed Git history.
#
# Important:
#   This script examines COMMITTED Git history only.
#   It does NOT inspect uncommitted or unstaged working-directory changes.
#
# Example:
#
#   Latest release:
#     v0.5.0
#
#   New committed change:
#     feat: add referral workflow
#
#   Result:
#     v0.6.0
#
# Release rules:
#
#   feat:   -> MINOR
#   fix:    -> PATCH
#   feat!:  -> MAJOR
#
#   docs:, test:, chore:, etc. do not create a release by themselves.
#
# Automated CI/CD release flow:
#
#   Developer
#      |
#      | git push
#      v
#   main
#      |
#      v
#   HavenBridge CI
#      |
#      | tests / build / validation
#      |
#      +---- FAIL -----------------------> STOP
#      |
#      +---- PASS
#             |
#             v
#      HavenBridge Release
#             |
#             | semantic version calculation
#             |
#             +---- docs / chore only
#             |          |
#             |          v
#             |      no release
#             |          |
#             |          v
#             |        STOP
#             |
#             +---- feat / fix / breaking change
#                        |
#                        v
#                  new version / tag
#                        |
#                        v
#                  HavenBridge CD
#                        |
#                        v
#                  self-hosted runner
#                        |
#                        v
#             restricted Kubernetes RBAC
#                        |
#                        v
#                exact release image
#                        |
#                        v
#                rollout + validation
#
# This script is responsible for the semantic-version decision inside the
# HavenBridge Release stage. It does not perform CI or Kubernetes deployment.
#
# GitHub Actions uses the values written to GITHUB_OUTPUT later in this script.
# ---------------------------------------------------------------------------

set -euo pipefail

# Run Git commands from the repository root so path checks are consistent.
cd "$(git rev-parse --show-toplevel)"

# Find the most recent semantic-version tag.
LATEST_TAG="$(
  git describe \
    --tags \
    --abbrev=0 \
    --match 'v[0-9]*.[0-9]*.[0-9]*' \
    2>/dev/null ||
  echo "v0.0.0"
)"

# Read application commits created after the last release.
#
# Restricting the Git log to applications/havenbridge-api means documentation,
# infrastructure, observability, and CI/CD-only changes do not accidentally
# create a HavenBridge API application version.
COMMITS="$(
  git log \
    "${LATEST_TAG}..HEAD" \
    --pretty='%s%n%b' \
    -- applications/havenbridge-api
)"

# Split a tag such as v0.7.0 into:
#   MAJOR=0
#   MINOR=7
#   PATCH=0
IFS='.' read -r MAJOR MINOR PATCH <<< "${LATEST_TAG#v}"

if grep -Eq '^feat(\([^)]*\))?!:|^BREAKING CHANGE:' <<< "${COMMITS}"; then
  ((MAJOR+=1))
  MINOR=0
  PATCH=0
  BUMP="major"

elif grep -Eq '^feat(\([^)]*\))?:' <<< "${COMMITS}"; then
  ((MINOR+=1))
  PATCH=0
  BUMP="minor"

elif grep -Eq '^fix(\([^)]*\))?:' <<< "${COMMITS}"; then
  ((PATCH+=1))
  BUMP="patch"

else
  echo "No release-causing commit found."
  echo "No HavenBridge application release is required."

  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    {
      echo "release_needed=false"
      echo "bump=none"
      echo "tag="
      echo "app_version="
    } >> "${GITHUB_OUTPUT}"
  fi

  exit 0
fi

NEXT_TAG="v${MAJOR}.${MINOR}.${PATCH}"

echo "Latest release: ${LATEST_TAG}"
echo "Release type:  ${BUMP}"
echo "Next release:  ${NEXT_TAG}"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "release_needed=true"
    echo "bump=${BUMP}"
    echo "tag=${NEXT_TAG}"
    echo "app_version=${NEXT_TAG#v}"
  } >> "${GITHUB_OUTPUT}"
fi
