# Grünenthal AI Health Agent - User Guide

## Overview
This AI health agent can answer questions using three powerful data sources:
1. **Neo4j Graph Database** - Drug relationships, manufacturers, adverse events
2. **FDA Adverse Events API** - Real-time adverse event reports from FDA
3. **Financial Reports PDF** - Company financial information

## How to Use
1. Start the application with: `python -m streamlit run src/main.py`
2. Enter your question in the chat interface
3. The AI will automatically decide which tools to use
4. View token usage and conversation history in the sidebar

## Example Questions to Try

### FDA Adverse Events API
- "What are the recent adverse events for TRAMADOL?"
- "Show me the latest side effects reported for METFORMIN"
- "Are there any serious adverse events for IBUPROFEN?"

### Neo4j Graph Database
- "What are the manufacturers of TRAMADOL?"
- "Which drugs are most commonly associated with adverse events?"
- "Show me the relationship between drugs and their manufacturers"
- "What cases are in the database for pain medications?"

## Setting Up Financial Reports

### Where to Place PDF Files
Place your financial report PDFs in the **`data/` folder**:
- `data/grunenthal_annual_report_2024.pdf`
- `data/quarterly_report_Q1_2025.pdf`
- `data/financial_highlights_2024.pdf`

### How to Query Financial Reports
The AI can automatically find and read your PDFs. You can ask questions like:
- "What was the revenue last quarter?" (searches all PDFs for revenue info)
- "Show me financial highlights" (finds relevant sections)
- "What are the key metrics from the annual report?" (searches for metrics)
- "Read the quarterly report" (reads the whole document)

### Supported File Types
- PDF files only (`.pdf` extension)
- The tool automatically detects and reads all PDFs in the `data/` folder
- If you have multiple PDFs, it will try to find the most relevant one for your query

### Combined Queries
- "Tell me about TRAMADOL - its manufacturers, recent adverse events, and any financial impact"
- "Compare the safety profiles of different pain medications"
- "What manufacturers have the most adverse event reports?"

## Technical Features
- **Token Monitoring**: Tracks token usage to prevent excessive costs
- **Conversation History**: Maintains context across multiple questions
- **Error Handling**: Graceful handling of API failures with helpful error messages
- **Multiple LLM Support**: Works with OpenAI, Gemini, Anthropic, and OpenRouter
- **Intelligent Tool Selection**: AI automatically chooses the best data source for each question

## Troubleshooting
- If Neo4j queries fail, check database connection in `.env`
- FDA API may have rate limits - wait a moment between requests
- For PDF issues, ensure the file exists in the `data/` folder
- Check token limits if responses seem truncated

## Configuration
Edit `.env` file to configure:
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` for Neo4j
- `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc. for LLM providers
- Default LLM provider in `src/agent.py`

## Recent Improvements
- Fixed FDA API to show correct drug names (not just first drug in report)
- Enhanced Neo4j tool with dynamic query generation
- Added token counting and truncation to prevent excessive usage
- Improved error handling and user feedback
- Added conversation history and clear chat functionality

## Development Documentation

### **Top 10 Development Prompts**
For development teams and advanced users, see `TOP_10_PROMPTS.md` which documents:
- The 10 most critical prompts used during agent development
- Why each prompt was essential for building robust functionality
- Technical insights and debugging strategies discovered
- Testing methodologies that ensured production readiness

This documentation provides valuable insights for:
- **Developers** extending or modifying the agent
- **QA Teams** testing similar AI systems
- **Product Managers** understanding development complexity
- **Users** who want to understand the agent's full capabilities

### **Validated Use Cases**
The agent has been thoroughly tested with real-world scenarios including:
- Multi-drug adverse event analysis
- Manufacturer relationship mapping
- Financial performance queries with page-specific searches
- Cross-tool queries combining all three data sources
- Error handling and edge case management
