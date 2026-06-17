#!/usr/bin/env bash
# Exit on error
set -o errexit

apt-get update
apt-get install -y tesseract-ocr
