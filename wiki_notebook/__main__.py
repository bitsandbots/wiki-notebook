#!/usr/bin/env python3
"""CLI entry point for wiki-notebook."""

from __future__ import annotations

import sys


def main() -> None:
    """Start the Flask development server."""
    from wiki_notebook.app import create_app
    from wiki_notebook.config import config

    app = create_app()

    print(f"Starting Wiki Notebook on {config.bind_host}:{config.port}")
    print(f"Database: {config.db_path}")
    print(f"Ollama: {config.ollama_url} (model: {config.ollama_model})")
    print(f"Health: http://127.0.0.1:{config.port}/api/health")

    app.run(host=config.bind_host, port=config.port, debug=False)


if __name__ == "__main__":
    main()
