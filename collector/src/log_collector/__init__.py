"""Standalone Docker log snapshot collector.

This package contains the dedicated collector application that replaces the
host-side shell collector with a typed Python implementation. Its job is
deterministic only:

- discover configured Docker containers
- fetch bounded log snapshots
- write the current snapshot files
- archive the previous snapshot set

It does not perform any LLM analysis or backend orchestration.
"""
