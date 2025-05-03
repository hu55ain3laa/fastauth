#!/usr/bin/env python3
"""
FastAuth Database Initialization CLI Tool

This script initializes the database, creates standard roles, and sets up a superadmin user
for a FastAuth application.

Usage:
    python fastauth_init.py --db-url=sqlite:///./app.db --secret-key=your-secret-key

Optional flags:
    --init-db             Create database tables
    --init-roles          Initialize standard roles
    --create-superadmin   Create a superadmin user
    --username            Specify a superadmin username
    --password            Specify a superadmin password

If no optional flags are specified, all initialization steps will be performed.
"""
import sys
from fastauth.cli import main

if __name__ == "__main__":
    sys.exit(main())
