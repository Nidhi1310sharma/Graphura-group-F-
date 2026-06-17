#!/usr/bin/env bash
# Exit on error
set -o errexit

# Update and install tesseract
apt-get update
apt-get install -y tesseract-ocr

# Install python dependencies
pip install -r requirements.txt
