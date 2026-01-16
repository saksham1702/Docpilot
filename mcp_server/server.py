#!/usr/bin/env python3
"""
DocPilot MCP Server
Exposes doc-verified code generation as MCP tools for Cursor/Claude.
"""
import os
import json
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Backend API URL (default to localhost, can be overridden)
BACKEND_URL = os.getenv("DOCPILOT_BACKEND_URL", "http://localhost:8000")

server = Server("docpilot")

@server.list_tools()
async def list_tools():
    """List available DocPilot tools."""
    return [
        Tool(
            name="ask_docs",
            description="Search documentation and get verified answers with citations. Use this when you need to find accurate, up-to-date information from official docs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to search for in documentation"
                    },
                    "library": {
                        "type": "string",
                        "description": "Optional: Filter by library name (e.g., 'fastapi', 'react')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3)",
                        "default": 3
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="docs_stats",
            description="Get statistics about indexed documentation (total chunks, libraries).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "ask_docs":
        return await ask_docs(arguments)
    elif name == "docs_stats":
        return await docs_stats()
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def ask_docs(arguments: dict):
    """Call the backend /answer endpoint."""
    try:
        # Build request with only non-None values
        request_body = {
            "question": arguments.get("question", ""),
            "top_k": arguments.get("top_k", 3)
        }
        
        # Only include library if it's provided and not empty
        library = arguments.get("library")
        if library and library.strip():
            request_body["library"] = library.strip()
        
        response = requests.post(
            f"{BACKEND_URL}/answer",
            json=request_body,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Format the response nicely
            result = f"## Answer for: {data['question']}\n\n"
            result += f"### Context:\n{data['context'][:2000]}...\n\n"
            
            if data['citations']:
                result += "### Citations:\n"
                for i, citation in enumerate(data['citations'], 1):
                    result += f"{i}. [{citation['library']} {citation['version']}]({citation['url']})\n"
            
            return [TextContent(type="text", text=result)]
        else:
            return [TextContent(type="text", text=f"Error: Backend returned {response.status_code}")]
    
    except requests.exceptions.ConnectionError:
        return [TextContent(type="text", text="Error: Cannot connect to DocPilot backend. Is it running on localhost:8000?")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def docs_stats():
    """Get documentation statistics."""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [TextContent(
                type="text", 
                text=f"📊 DocPilot Stats:\n- Total chunks: {data.get('total_chunks', 0)}\n- Libraries indexed: {data.get('total_libraries', 0)}"
            )]
        else:
            return [TextContent(type="text", text=f"Error: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
