#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/alabi/projects/havenbridge-ha-service-platform"
TARGET_DIR="${PROJECT_ROOT}/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation"

FILES=(
  "unauthorized-client-pod.yaml"
  "unauthorized-client-result.txt"
  "api-egress-positive-validation.txt"
  "api-egress-negative-test-job.yaml"
  "api-egress-negative-validation.txt"
  "api-egress-negative-validation-steps.txt"
  "postgres-unauthorized-client.yaml"
  "postgres-ingress-validation-steps.txt"
  "postgres-ingress-validation.txt"
  "havenbridge-networkpolicy-ingress-vs-egress.txt"
)
mkdir -p "${TARGET_DIR}"

echo "Project root: ${PROJECT_ROOT}"
echo "Evidence directory: ${TARGET_DIR}"
echo

found=0
missing=0

for filename in "${FILES[@]}"; do
  destination="${TARGET_DIR}/${filename}"

  if [[ -f "${destination}" ]]; then
    echo "[ALREADY PRESENT] ${destination}"
    ((found+=1))
    continue
  fi

  source_file="$(
    find "${PROJECT_ROOT}" \
      -path "${TARGET_DIR}" -prune -o \
      -type f -name "${filename}" -print \
      | head -n 1
  )"

  if [[ -n "${source_file}" ]]; then
    cp -v -- "${source_file}" "${destination}"
    ((found+=1))
  else
    echo "[NOT FOUND] ${filename}"
    ((missing+=1))
  fi
done

echo
echo "Collection complete."
echo "Present or copied: ${found}"
echo "Not found: ${missing}"
echo
echo "Final evidence directory contents:"
ls -lah "${TARGET_DIR}"
