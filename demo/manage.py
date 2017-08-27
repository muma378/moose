#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("MOOSE_SETTINGS_MODULE", "demo.settings")

    from moose.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
