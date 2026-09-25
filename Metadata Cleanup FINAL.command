#!/bin/bash
cd "$(dirname "$0")"
clear
echo "Michael Elliott Archive - FINAL Metadata Cleanup"
echo "================================================"
echo
python3 metadata_cleanup_final.py
