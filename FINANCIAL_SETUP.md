# 📊 Financial Report Setup Guide

## 🎯 Quick Start

### Step 1: Place Your PDF
Put your financial report PDF in the `data/` folder:
```
\data\your_financial_report.pdf
```

### Step 2: Ask Questions
The AI will automatically find and read your PDF. Try these examples:
- "What was our revenue this year?"
- "Show me the financial highlights"
- "What are the key business metrics?"
- "Tell me about our profitability"

## File Placement Examples
```
data/
├── grunenthal_annual_report_2024.pdf
├── quarterly_results_Q1_2025.pdf
├── financial_highlights_2024.pdf
└── test_financial_report.pdf (example file)
```

## How It Works
1. **Auto-Discovery**: The tool automatically finds PDF files in the `data/` folder
2. **Smart Search**: When you ask about "revenue" or "profits", it searches the PDF for relevant sections
3. **Context-Aware**: Returns the most relevant information based on your question
4. **Token-Optimized**: Limits response size to prevent excessive token usage

## Example Questions
- **Revenue**: "What was the total revenue?" or "Show me revenue growth"
- **Profitability**: "What's our profit margin?" or "How profitable were we?"
- **Segments**: "Which business segment performed best?"
- **Metrics**: "What are the key financial ratios?"
- **Outlook**: "What's the financial outlook?" or "What are the projections?"

## Troubleshooting
- **No PDF found**: Make sure your PDF is in the `data/` folder
- **Can't read PDF**: Some PDFs may be corrupted or protected - try a different file
- **No relevant content**: Try more specific keywords in your question.
