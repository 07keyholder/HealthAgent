# Grünenthal Health Agent

A robust AI-powered agent for pharmaceutical data analysis, combining:
- Neo4j graph database (drug relationships, manufacturers, adverse events)
- FDA Adverse Events API (real-time safety data)
- Financial report PDF search (business intelligence)

## Features
- Natural language queries across all data sources
- LLM-powered tool selection (OpenAI, Gemini, Anthropic, OpenRouter)
- Token usage monitoring and cost control
- Conversation history and context retention
- Robust error handling
- Streamlit web UI

## Quick Start

1. **Clone the repository:**
   ```
   git clone https://github.com/your-org/health-agent.git
   cd health-agent
   ```
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Configure environment:**
   - Copy `.env.example` to `.env` and add your API keys (OpenAI, Neo4j, etc.)
4. **(Optional) Add your own PDFs:**
   - Place any financial report PDFs in the `data/` folder (do not commit confidential files)
5. **Run the app:**
   ```
   python -m streamlit run src/main.py
   ```
6. **Access the UI:**
   - Open [http://localhost:8501](http://localhost:8501) in your browser

## Example Prompts
- What are the top 10 most recent adverse events for TRAMADOL?
- What are the manufacturers of TRAMADOL?
- How much money did Grünenthal make in 2023?
- In which page is 'Grünenthal is headquartered in Aachen, Germany'?
- Tell me about TRAMADOL - its manufacturers, recent adverse events, and any financial impact

## Documentation
- `USER_GUIDE.md` – Full user manual and setup
- `TOP_10_PROMPTS.md` – The 10 most important agent test prompts (with explanations)

## Notes
- No proprietary data or PDFs are included in this repository.
- For private deployments, add your own financial reports to the `data/` folder (do not commit them).
- The file `FINANCIAL_SETUP.md` has been removed for public release.

## License
MIT
