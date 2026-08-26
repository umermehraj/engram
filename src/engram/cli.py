"""CLI entry point for Engram."""

from __future__ import annotations

import argparse
import asyncio
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="engram",
        description="Engram — Hybrid memory layer for AI agents",
    )
    subparsers = parser.add_subparsers(dest="command")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the Engram server")
    serve_parser.add_argument("--mcp", action="store_true", help="Run as MCP server (stdio)")
    serve_parser.add_argument("--host", default="0.0.0.0", help="API host (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")

    # viz command
    viz_parser = subparsers.add_parser("viz", help="Visualize knowledge graph")
    viz_parser.add_argument("--user-id", required=True, help="User ID to visualize")
    viz_parser.add_argument("--output", default="engram_graph.html", help="Output HTML file")
    viz_parser.add_argument("--storage-path", default="./engram_data", help="Storage path")

    # demo command
    subparsers.add_parser("demo", help="Run the interactive demo")

    args = parser.parse_args()

    if args.command == "serve":
        if args.mcp:
            from engram.integrations.mcp import run_stdio
            asyncio.run(run_stdio())
        else:
            import uvicorn
            uvicorn.run(
                "engram.api.main:app",
                host=args.host,
                port=args.port,
                reload=False,
            )

    elif args.command == "viz":
        asyncio.run(_run_viz(args))

    elif args.command == "demo":
        # Import and run the demo
        sys.path.insert(0, ".")
        from demo import run_demo
        asyncio.run(run_demo())

    else:
        parser.print_help()


async def _run_viz(args):
    from engram.config import EngramConfig
    from engram.storage.kuzu_backend import KuzuBackend
    from engram.viz.graph_view import visualize_user_graph

    config = EngramConfig(local=True, storage_path=args.storage_path)
    graph = KuzuBackend(config)
    await graph.initialize()

    path = await visualize_user_graph(
        graph_backend=graph,
        user_id=args.user_id,
        output_path=args.output,
    )
    print(f"Graph saved to: {path}")

    import webbrowser
    from pathlib import Path
    webbrowser.open(f"file://{Path(path).resolve()}")

    await graph.close()


if __name__ == "__main__":
    main()
