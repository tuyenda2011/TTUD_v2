#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main entry point for Shipper Route Optimizer.
Usage:
    python main.py --benchmark
    python main.py
"""
import sys
import os

# Add shipper_optimizer root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main as run_main

if __name__ == "__main__":
    run_main()
