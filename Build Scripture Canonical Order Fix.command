#!/bin/bash
cd "$(dirname "$0")"
clear
echo "Michael Elliott Archive - Scripture Canonical Bible Order Fix"
echo "============================================================="
echo
python3 build_scripture_canonical_order.py
