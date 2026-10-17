#!/usr/bin/env python3
"""PyOS - entry point."""
import os, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

def main():
    try:
        from pyos.kernel.core import Kernel
    except Exception:
        print("PyOS failed to import kernel:")
        traceback.print_exc()
        sys.exit(2)
    Kernel().boot()

if __name__ == "__main__":
    main()