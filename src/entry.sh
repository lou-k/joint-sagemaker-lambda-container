#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "args is ${1:-}"
if [ "${1:-}" = "serve" ] ; then
    # This is a sagemaker serving thang....
    echo 'Starting sagemaker serving service....'
    exec /usr/local/bin/python serve.py
fi

if [ -z "${AWS_LAMBDA_RUNTIME_API:-}" ]; then
    echo 'Local execution. Running Lambda Runtime Interface Emulator...'
    exec /usr/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric ${1:-}
else
    echo 'Starting lambda...'
    exec /usr/local/bin/python -m awslambdaric ${1:-}
fi