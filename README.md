# DocPilot 🚀

**Document-Verified Code Generation** - A RAG-powered system that searches official documentation and provides verified answers with citations.

## Architecture

```
Cursor IDE → MCP Server → FastAPI Backend → Modal (Embeddings) → PostgreSQL + pgvector
                                ↑
                    Worker (Doc Crawler)
```

## Quick Start

### 1. Start services
```bash
docker compose up -d
```

### 2. Deploy Modal embedding service
```bash
pip install modal
modal deploy modal_embed/main.py
```

### 3. Configure MCP in Cursor
Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "docpilot": {
      "command": "python",
      "args": ["<path>/mcp_server/server.py"]
    }
  }
}
```

## Components

| Component | Description |
|-----------|-------------|
| `backend/` | FastAPI server with `/answer` endpoint |
| `worker/` | Documentation crawler |
| `mcp_server/` | MCP server for Cursor integration |
| `modal_embed/` | Serverless embedding service (Modal) |

## API Endpoints

- `GET /health` - Health check
- `GET /stats` - Indexed doc statistics
- `POST /answer` - RAG query with citations

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `EMBEDDING_API_URL` | Modal embedding endpoint |

## License

MIT
