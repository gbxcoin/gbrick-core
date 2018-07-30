#!/usr/bin/env bash
python3 -m unittest discover tests -p "test_*.py" || exit -1

