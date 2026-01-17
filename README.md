# DocPilot

**RAG-powered documentation search for AI code assistants** - Search official documentation and get verified answers with citations, integrated with Cursor via MCP.

## Features

- **Vector Search**: Semantic search across indexed documentation using pgvector
- **Multi-library Support**: Index multiple documentation sources
- **Citations**: Every answer includes source URLs
- **MCP Integration**: Works as a tool in Cursor/Claude
- **Cloud Ready**: Deployable to AWS with Terraform
- **CI/CD**: Auto-deploy with GitHub Actions

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Cursor IDE    │────▶│   MCP Server    │────▶│  FastAPI Backend│
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────┐     ┌────────▼────────┐
                        │   Modal Cloud   │◀────│   PostgreSQL    │
                        │  (Embeddings)   │     │   + pgvector    │
                        └─────────────────┘     └─────────────────┘
```

---

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Modal account (free tier works)

### 1. Clone the Repository
```bash
git clone https://github.com/saksham1702/Docpilot.git
cd Docpilot
```

### 2. Deploy Modal Embedding Service
```bash
pip install modal
modal setup  # Login to Modal

# Deploy the embedding service
modal deploy modal_embed/main.py
```
Note the URL: `https://YOUR_USERNAME--docpilot-embedder-model-embedding-webhook.modal.run`

### 3. Start Services
```bash
# Set your Modal URL
export EMBEDDING_API_URL="https://YOUR_USERNAME--docpilot-embedder-model-embedding-webhook.modal.run"

# Start containers
docker compose up -d
```

### 4. Configure MCP in Cursor
Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "docpilot": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server/server.py"],
      "env": {
        "DOCPILOT_BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
```

### 5. Test It
In a new Cursor chat:
> "Use ask_docs to find how to install Pathway"

---

## AWS Deployment

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform installed (`brew install terraform`)
- Modal account

### 1. Deploy Modal Embedding Service
```bash
pip install modal
modal setup
modal deploy modal_embed/main.py
```
Save your Modal URL.

### 2. Configure Terraform Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
aws_region        = "us-east-1"
project_name      = "docpilot"
db_password       = "YOUR_SECURE_PASSWORD"
embedding_api_url = "https://YOUR_MODAL_USERNAME--docpilot-embedder-model-embedding-webhook.modal.run"
```

### 3. Deploy Infrastructure
```bash
terraform init
terraform apply
```

This creates:
- VPC with public subnets
- RDS PostgreSQL with pgvector
- ECS Fargate cluster
- Application Load Balancer
- ECR repository

### 4. Initialize Database
```bash
PGPASSWORD='YOUR_PASSWORD' psql -h YOUR_RDS_ENDPOINT -U docpilot -d docpilot -f init.sql
```

### 5. Push Docker Image to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push (use linux/amd64 for Fargate)
docker buildx build --platform linux/amd64 -t YOUR_ECR_URL:latest ./backend --push

# Deploy to ECS
aws ecs update-service --cluster docpilot-cluster --service docpilot-backend --force-new-deployment
```

### 6. Configure MCP for AWS
Update `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "docpilot": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server/server.py"],
      "env": {
        "DOCPILOT_BACKEND_URL": "http://YOUR_ALB_DNS_NAME"
      }
    }
  }
}
```

### 7. Index Documentation
Run worker locally pointing to AWS RDS:
```bash
export DATABASE_URL='postgresql://docpilot:YOUR_PASSWORD@YOUR_RDS_ENDPOINT:5432/docpilot'
export EMBEDDING_API_URL='https://YOUR_MODAL_USERNAME--docpilot-embedder-model-embedding-webhook.modal.run'
cd worker && python main.py
```

---

## CI/CD with GitHub Actions

The repo includes auto-deploy on push to `master`.

### Setup
1. Go to your repo → Settings → Environments → Create "aws secrets"
2. Add these secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

Every push to `master` will:
1. Build Docker image
2. Push to ECR
3. Redeploy ECS

---

## Project Structure

```
├── backend/              # FastAPI backend
│   ├── main.py           # API endpoints
│   └── Dockerfile
├── worker/               # Documentation crawler
│   └── main.py
├── mcp_server/           # MCP server for Cursor
│   └── server.py
├── modal_embed/          # Serverless embedding service
│   └── main.py
├── terraform/            # AWS infrastructure
│   ├── main.tf           # Provider & variables
│   ├── vpc.tf            # Networking
│   ├── rds.tf            # PostgreSQL
│   ├── ecs.tf            # Fargate
│   ├── alb.tf            # Load Balancer
│   └── ecr.tf            # Container registry
├── .github/workflows/    # CI/CD
│   └── deploy.yml
├── docker-compose.yml    # Local development
└── init.sql              # Database schema
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/stats` | GET | Index statistics |
| `/answer` | POST | RAG query with citations |

### Example Request
```bash
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "How to install Pathway?", "library": "pathway", "top_k": 3}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `EMBEDDING_API_URL` | Modal embedding endpoint |
| `DOCPILOT_BACKEND_URL` | Backend URL for MCP server |

## License

MIT
