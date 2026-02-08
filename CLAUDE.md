# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Course Materials RAG (Retrieval-Augmented Generation) chatbot — a full-stack app where users ask questions about course materials and get AI-powered answers backed by semantic search over document chunks.

## Commands

```bash
# Install dependencies
uv sync

# Run the server (from repo root)
cd backend && uv run uvicorn app:app --reload --port 8000

# Or use the shell script
./run.sh
```

App runs at http://localhost:8000, API docs at http://localhost:8000/docs.

There are no tests or linting configured in this project.

## Environment Setup

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`. The `.env` file is loaded by `backend/config.py` via `python-dotenv`.

## Architecture

### Backend (`backend/`) — Python/FastAPI

**Request flow:** `app.py` endpoint → `RAGSystem.query()` → `AIGenerator` calls Claude with tool definitions → Claude may invoke `search_course_content` tool → `ToolManager` dispatches to `CourseSearchTool` → `VectorStore` queries ChromaDB → results return to Claude for final answer synthesis.

Key components:

- **`rag_system.py` — `RAGSystem`**: Central orchestrator. Wires together all components. On query: wraps prompt, fetches session history, calls AI generator with tools, collects sources, saves exchange to session.
- **`ai_generator.py` — `AIGenerator`**: Wraps Anthropic SDK. Makes up to 2 Claude API calls per query: first with tools enabled, second (if tool was used) with tool results and tools disabled.
- **`search_tools.py` — `CourseSearchTool` / `ToolManager`**: Implements the Anthropic tool-use pattern. `CourseSearchTool` defines the `search_course_content` tool schema and executes searches. `ToolManager` is a registry that dispatches tool calls by name. Sources from the last search are tracked on the tool instance and collected after each query.
- **`vector_store.py` — `VectorStore`**: ChromaDB interface with two collections: `course_catalog` (metadata, used for fuzzy course name resolution) and `course_content` (text chunks). Embeddings via `all-MiniLM-L6-v2` (sentence-transformers).
- **`document_processor.py` — `DocumentProcessor`**: Parses `.txt` files with a specific format (headers: `Course Title:`, `Course Instructor:`, `Lesson N:`) into `Course`/`CourseChunk` models. Chunks text by sentences with configurable size (800 chars) and overlap (100 chars).
- **`session_manager.py` — `SessionManager`**: In-memory per-session conversation history. History is formatted as plain text and injected into the system prompt for Claude.
- **`config.py`**: Dataclass with all tunables (model names, chunk size, max results, ChromaDB path). Single `config` instance imported everywhere.

### Frontend (`frontend/`) — Vanilla HTML/CSS/JS

Served as static files by FastAPI (mounted at `/`). Chat interface sends `POST /api/query` with `{query, session_id}`, renders Markdown responses via `marked.js`, shows collapsible sources. Course sidebar populated via `GET /api/courses`.

### Data (`docs/`)

Course material `.txt` files loaded automatically on server startup via `app.py`'s `startup` event → `rag_system.add_course_folder("../docs")`. Existing courses are skipped (deduplication by title).

### API Endpoints

- `POST /api/query` — `{query: str, session_id?: str}` → `{answer, sources[], session_id}`
- `GET /api/courses` → `{total_courses, course_titles[]}`

## Rules

- Always use `uv` instead of `pip` for package management (install, add, remove dependencies).

## Key Patterns

- **Tool-use loop**: Claude decides whether to search. The `AIGenerator` checks `stop_reason == "tool_use"`, executes tools, then makes a second API call with results. The second call has no tools to prevent infinite loops.
- **Course name resolution**: When a tool call includes `course_name`, `VectorStore._resolve_course_name()` does a vector search against `course_catalog` to fuzzy-match to an exact title before filtering `course_content`.
- **Working directory matters**: The server runs from `backend/`, so relative paths like `"../docs"` and `"../frontend"` are relative to that directory. `ChromaDB` persists to `./chroma_db` inside `backend/`.
