# Graphiti Memory System Deployment Guide

The "Graphiti Brain" has been integrated into the GHL Real Estate AI. This system provides persistent, semantic memory (knowledge graph) alongside the existing file-based history.

## 1. Activation Requirements

The code is currently in "Safe Mode" (Graphiti features disabled) because the `graphiti-core` library is not installed. To activate:

### A. Install Dependencies
```bash
pip install graphiti-core>=0.5.0 neo4j  # or graphiti-core[redis] for FalkorDB
```
*Note: Ensure you have the correct driver package for your database.*

### B. Environment Variables
Add these to your `.env` file or deployment environment:

```env
# Graphiti Configuration
GRAPHITI_HOST=localhost       # Host of your Graph DB (Neo4j or FalkorDB)
GRAPHITI_PORT=7687            # Port (7687 for Neo4j, 6379 for FalkorDB)
GRAPHITI_USER=neo4j           # Database User
GRAPHITI_PASSWORD=password    # Database Password
GRAPHITI_DRIVER=neo4j         # 'neo4j' or 'falkordb'
```

### C. Database Setup
You must have a running instance of a supported Graph Database.
- **Neo4j:** [Download Desktop](https://neo4j.com/download/) or use [AuraDB (Cloud)](https://neo4j.com/cloud/aura/).
- **FalkorDB:** run via Docker: `docker run -p 6379:6379 -it falkordb/falkordb`

## 2. System Architecture

- **`ghl_real_estate_ai/agent_system/memory/manager.py`**: The core driver connecting to the Graph DB. It handles `save_interaction` (Write) and `retrieve_context` (Read).
- **`ghl_real_estate_ai/services/memory_service.py`**: The service wrapper used by the application. It now writes to **both** file storage (JSON) and Graphiti.
- **`ghl_real_estate_ai/services/claude_assistant.py`**: The UI Brain. It fetches context from `MemoryService` and injects "Graphiti Recall" into the sidebar insights.

## 3. Maintenance ("The Dream Cycle")

Run the consolidation script nightly to optimize the knowledge graph:

```bash
python3 ghl_real_estate_ai/scripts/consolidate_memory.py
```

## 4. Verification

Run the included test script to verify the connection:

```bash
python3 test_memory_integration.py
```
If configured correctly, it will output: `✅ Graphiti Integration Verified`.
