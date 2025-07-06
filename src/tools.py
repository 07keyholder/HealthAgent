import os
from neo4j import GraphDatabase
import requests
import fitz
from langchain_community.tools import tool
from dotenv import load_dotenv
import tiktoken
import json

load_dotenv()

# Neo4j Tool
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
DB = os.getenv("NEO4J_DATABASE")


@tool
def query_neo4j_database(query_description: str):
    """Query the Neo4j pharmaceutical database with natural language using AI-generated Cypher queries.

    This tool uses AI to generate appropriate Cypher queries based on the user's question
    and the database schema. It can answer questions about drugs, manufacturers, adverse
    events, patient demographics, and relationships between entities.

    Examples:
    - "Which manufacturers make drugs containing aspirin?"
    - "What adverse reactions are reported for Kisqali?"
    - "How many cases involve elderly patients?"
    - "Which drugs are most commonly primary suspects in cases?"
    """

    # Import and use the actual LLM to generate queries
    def get_llm_response(prompt, max_tokens=500):
        """Generate Cypher query using the LLM."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            # Fallback logic only if LLM fails
            query_lower = query_description.lower()

            if "most" in query_lower and "suspect" in query_lower:
                return "MATCH (c:Case)-[:IS_PRIMARY_SUSPECT]->(d:Drug) RETURN d.name as drug_name, count(c) as cases ORDER BY cases DESC LIMIT 15"
            elif (
                "manufacturer" in query_lower
                or "company" in query_lower
                or "companies" in query_lower
            ):
                # Check if a specific drug is mentioned
                for word in query_description.split():
                    # Clean the word of punctuation
                    clean_word = word.strip(".,?!:;").upper()
                    if len(clean_word) > 3 and clean_word in [
                        "TRAMADOL",
                        "ASPIRIN",
                        "IBUPROFEN",
                        "METFORMIN",
                        "PFIZER",
                        "ROCHE",
                        "NOVARTIS",
                    ]:
                        if clean_word in ["PFIZER", "ROCHE", "NOVARTIS"]:
                            # Manufacturer to drugs query
                            return f"MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)<-[:REGISTERED]-(m:Manufacturer {{manufacturerName: '{clean_word}'}}) RETURN DISTINCT d.name as drug_name, count(c) as case_count ORDER BY case_count DESC LIMIT 10"
                        else:
                            # Drug to manufacturers query
                            return f"MATCH (d:Drug {{name: '{clean_word}'}})<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)<-[:REGISTERED]-(m:Manufacturer) RETURN DISTINCT m.manufacturerName as manufacturer, count(c) as case_count ORDER BY case_count DESC LIMIT 10"
                # Generic manufacturer query if no specific drug mentioned
                return "MATCH (m:Manufacturer)-[:REGISTERED]->(c:Case) RETURN m.manufacturerName as manufacturer, count(c) as total_cases ORDER BY total_cases DESC LIMIT 10"
            elif (
                "reaction" in query_lower
                or "adverse" in query_lower
                or "side effect" in query_lower
            ):
                # Check for specific drug reactions
                for word in query_description.split():
                    clean_word = word.strip(".,?!:;").upper()
                    if len(clean_word) > 3 and clean_word in [
                        "TRAMADOL",
                        "ASPIRIN",
                        "IBUPROFEN",
                        "METFORMIN",
                    ]:
                        return f"MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT]-(c:Case)-[:HAS_REACTION]->(r:Reaction) WHERE toLower(d.name) CONTAINS '{clean_word.lower()}' RETURN r.description as reaction, count(c) as case_count ORDER BY case_count DESC LIMIT 15"
                # Generic reaction query
                return "MATCH (c:Case)-[:HAS_REACTION]->(r:Reaction) RETURN r.description as reaction, count(c) as cases ORDER BY cases DESC LIMIT 15"
            elif any(
                word in query_lower for word in ["age group", "outcome", "demographic"]
            ):
                # Multi-hop queries
                for word in query_description.split():
                    clean_word = word.strip(".,?!:;").upper()
                    if clean_word in ["TRAMADOL", "ASPIRIN", "IBUPROFEN", "METFORMIN"]:
                        if "age" in query_lower:
                            return f"MATCH (d:Drug {{name: '{clean_word}'}})<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)-[:FALLS_UNDER]->(a:AgeGroup) RETURN a.ageGroup as age_group, count(c) as case_count ORDER BY case_count DESC"
                        elif "outcome" in query_lower:
                            return f"MATCH (d:Drug {{name: '{clean_word}'}})<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)-[:RESULTED_IN]->(o:Outcome) RETURN o.outcome as outcome, count(c) as case_count ORDER BY case_count DESC"
                return "MATCH (c:Case)-[:FALLS_UNDER]->(a:AgeGroup) RETURN a.ageGroup as age_group, count(c) as cases ORDER BY cases DESC LIMIT 10"
            else:
                return "MATCH (d:Drug) RETURN d.name as drug_name LIMIT 10"

    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()

            with driver.session(database=DB) as session:
                # Get the database schema
                schema_info = """
Neo4j Pharmaceutical Adverse Events Database Schema:

NODES:
- Case: primaryid (Long), age (Double), ageUnit (String), gender (String), eventDate (Date), reportDate (Date), reporterOccupation (String)
- Drug: name (String), primarySubstabce (String)
- Manufacturer: manufacturerName (String)
- Reaction: description (String)
- ReportSource: name (String), code (String)
- Outcome: code (String), outcome (String)
- Therapy: primaryid (Long)
- AgeGroup: ageGroup (String)

RELATIONSHIPS (Database Storage Directions):
- (Case)-[:IS_PRIMARY_SUSPECT]->(Drug): Cases where a drug is the primary suspect
- (Case)-[:IS_SECONDARY_SUSPECT]->(Drug): Cases where a drug is a secondary suspect  
- (Case)-[:IS_CONCOMITANT]->(Drug): Cases where a drug was taken concomitantly
- (Case)-[:IS_INTERACTING]->(Drug): Cases where a drug had interactions
- (Therapy)-[:PRESCRIBED]->(Drug): Therapies that prescribed specific drugs
- (Case)-[:RECEIVED]->(Therapy): Cases that received specific therapies
- (Manufacturer)-[:REGISTERED]->(Case): Manufacturers that registered/reported cases
- (Case)-[:HAS_REACTION]->(Reaction): Cases with specific reactions
- (Case)-[:REPORTED_BY]->(ReportSource): Cases reported by specific sources
- (Case)-[:RESULTED_IN]->(Outcome): Cases with specific outcomes
- (Case)-[:FALLS_UNDER]->(AgeGroup): Cases categorized by age groups

IMPORTANT: For drug-manufacturer queries, always use reverse traversal patterns:
Drug <-[IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]- Case <-[REGISTERED]- Manufacturer
(This traverses from Drug backwards through Cases to find Manufacturers)

EXAMPLE QUERIES:
1. Find drugs that are primary suspects:
   MATCH (c:Case)-[:IS_PRIMARY_SUSPECT]->(d:Drug) RETURN d.name, count(c) ORDER BY count(c) DESC

2. Find manufacturers for a specific drug (exact name) - ALWAYS USE WHEN DRUG NAME MENTIONED:
   MATCH (d:Drug {name: 'TRAMADOL'})<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)<-[:REGISTERED]-(m:Manufacturer)
   RETURN DISTINCT m.manufacturerName, count(c) as case_count ORDER BY case_count DESC

3. Find manufacturers for drugs containing a name (CONTAINS) - USE WHEN DRUG NAME IN QUESTION:
   MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)<-[:REGISTERED]-(m:Manufacturer)
   WHERE toLower(d.name) CONTAINS 'tramadol'
   RETURN DISTINCT m.manufacturerName, count(c) as case_count ORDER BY case_count DESC

4. Find reactions for a drug - ALWAYS FILTER BY DRUG NAME WHEN MENTIONED:
   MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT]-(c:Case)-[:HAS_REACTION]->(r:Reaction) 
   WHERE toLower(d.name) CONTAINS 'tramadol' RETURN r.description, count(c) ORDER BY count(c) DESC

5. Count cases for a specific drug - ALWAYS INCLUDE DRUG FILTER AND COUNT:
   MATCH (d:Drug {name: 'TRAMADOL'})<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)
   RETURN count(DISTINCT c) AS case_count

CRITICAL: When a drug name like TRAMADOL, ASPIRIN, etc. is mentioned in the question, 
you MUST include a WHERE clause to filter for that specific drug, like:
WHERE d.name = 'TRAMADOL' OR WHERE toLower(d.name) CONTAINS 'tramadol'
"""

                prompt = f"""
Based on the following Neo4j database schema, generate a precise Cypher query to answer this question: "{query_description}"

{schema_info}

CRITICAL RULES:
1. Use exact node labels and property names from the schema
2. Use appropriate relationship types and directions as shown in examples
3. For relationship alternatives, use the format [:REL1|REL2|REL3] (NO extra colons)
4. ⚠️ MANDATORY: When ANY drug name is mentioned (like TRAMADOL, ASPIRIN, etc.), you MUST filter for that specific drug using either:
   - WHERE toLower(d.name) CONTAINS 'drugname' 
   - OR (d:Drug {{name: 'DRUGNAME'}})
5. For count/aggregation queries, use count() and return the aggregated result
6. Include LIMIT clauses (typically 10-20 results)
7. Use case-insensitive text matching with CONTAINS when searching by name
8. Order results by relevance (usually count or alphabetically)
9. Return meaningful aliases for the results

DRUG FILTERING EXAMPLES:
- "TRAMADOL manufacturers" → MUST include: WHERE toLower(d.name) CONTAINS 'tramadol'
- "TRAMADOL side effects" → MUST include: WHERE toLower(d.name) CONTAINS 'tramadol'  
- "reactions to TRAMADOL" → MUST include: WHERE toLower(d.name) CONTAINS 'tramadol'

SPECIFIC PATTERNS:
- Drug manufacturers: MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT|IS_CONCOMITANT]-(c:Case)<-[:REGISTERED]-(m:Manufacturer) WHERE condition
- Drug reactions: MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT|IS_SECONDARY_SUSPECT]-(c:Case)-[:HAS_REACTION]->(r:Reaction) WHERE condition  
- Count queries: RETURN count(DISTINCT entity) AS count_alias
- Drug filtering: WHERE d.name = 'EXACT_NAME' OR WHERE toLower(d.name) CONTAINS 'partial_name'

Question: {query_description}

Response format: Provide ONLY the Cypher query, no explanations.
"""  # Get the generated query from the LLM
                cypher_query = get_llm_response(prompt, max_tokens=500)

                # Clean up the query (remove any markdown formatting)
                cypher_query = cypher_query.strip()
                if cypher_query.startswith("```"):
                    lines = cypher_query.split("\n")
                    cypher_query = "\n".join(lines[1:-1])
                if cypher_query.startswith("cypher"):
                    cypher_query = cypher_query[6:].strip()

                # Post-process to fix common issues
                cypher_query = post_process_query(cypher_query, query_description)

                # Execute the generated query
                try:
                    results = session.run(cypher_query).data()

                    if results:
                        formatted_output = f"Results for: '{query_description}'\n\n"

                        for i, result in enumerate(results, 1):
                            formatted_output += f"{i}. "

                            # Format the result dynamically based on what keys are present
                            result_parts = []
                            for key, value in result.items():
                                if value is not None:
                                    if isinstance(value, list):
                                        if len(value) > 5:
                                            value = value[:5] + ["..."]
                                        value = ", ".join(str(v) for v in value)
                                    result_parts.append(f"{key}: {value}")

                            formatted_output += " | ".join(result_parts) + "\n"

                        formatted_output += f"\nGenerated Query: {cypher_query}\n"
                        formatted_output += f"Total results: {len(results)}"

                        return truncate_to_token_limit(
                            formatted_output, max_tokens=2000
                        )

                    else:
                        return f"No results found for: '{query_description}'\n\nGenerated Query: {cypher_query}\n\nTry rephrasing your question or asking about:\n- Drug manufacturers\n- Adverse reactions\n- Patient demographics\n- Case statistics"

                except Exception as query_error:
                    # If the generated query fails, provide debugging info
                    error_msg = f"Generated query failed: {str(query_error)}\n\n"
                    error_msg += f"Generated Query: {cypher_query}\n\n"
                    error_msg += f"Original Question: {query_description}\n\n"
                    error_msg += "The LLM generated an invalid query. Please try rephrasing your question."

                    return error_msg

    except Exception as e:
        return f"Error querying Neo4j database: {str(e)}\n\nConnection details:\nURI: {URI}\nDatabase: {DB}"


# FDA API Tool
@tool
def get_adverse_events(drug_name: str, limit: int = 10):
    """What are the top 10 most recent adverse events registered for a drug containing a certain keyword in its name?"""
    try:
        # Try multiple search strategies for better results
        search_queries = [
            f"patient.drug.medicinalproduct:{drug_name.upper()}",
            f"patient.drug.medicinalproduct:*{drug_name.upper()}*",
            f"patient.drug.openfda.generic_name:{drug_name.lower()}",
            f"patient.drug.openfda.brand_name:*{drug_name.upper()}*",
        ]

        best_result = None

        for search_query in search_queries:
            url = f"https://api.fda.gov/drug/event.json?search={search_query}&limit={limit}&sort=receivedate:desc"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    best_result = data
                    break

        if not best_result:
            return f"No recent adverse events found for drugs containing '{drug_name}'. This could mean:\n1. No events reported recently\n2. Drug name not found in FDA database\n3. Try a different spelling or generic name"

        # Extract and format the most relevant information
        formatted_output = f"Top {len(best_result['results'])} most recent adverse events for drugs containing '{drug_name}':\n\n"

        for i, result in enumerate(best_result["results"], 1):
            report_date = result.get("receivedate", "Unknown")
            serious = (
                "Serious"
                if result.get("serious") == "1"
                else (
                    "Non-serious"
                    if result.get("serious") == "2"
                    else "Unknown severity"
                )
            )

            # Format date for readability
            if report_date and report_date != "Unknown" and len(report_date) == 8:
                try:
                    formatted_date = (
                        f"{report_date[4:6]}/{report_date[6:8]}/{report_date[:4]}"
                    )
                except:
                    formatted_date = report_date
            else:
                formatted_date = report_date

            # Get patient reactions - improved extraction
            reactions = []
            if "patient" in result:
                patient = result["patient"]
                if "reaction" in patient and isinstance(patient["reaction"], list):
                    for reaction in patient["reaction"]:
                        if "reactionmeddrapt" in reaction:
                            reactions.append(
                                reaction["reactionmeddrapt"]
                            )  # Get drug information for this event - find the specific drug that matches our search
            drug_info = "Unknown drug"
            matching_drugs = []

            if "patient" in result:
                patient = result["patient"]
                if "drug" in patient and isinstance(patient["drug"], list):
                    # First, try to find drugs that contain our search term
                    for drug in patient["drug"]:
                        if "medicinalproduct" in drug:
                            medicinal_product = drug["medicinalproduct"]
                            if drug_name.upper() in medicinal_product.upper():
                                matching_drugs.append(medicinal_product)

                    # If we found matching drugs, use the first one
                    if matching_drugs:
                        drug_info = matching_drugs[0]
                        if len(matching_drugs) > 1:
                            drug_info += f" (and {len(matching_drugs)-1} other {drug_name.upper()}-containing drugs)"
                    else:
                        # Fallback: use the first drug if no specific match found
                        if patient["drug"] and "medicinalproduct" in patient["drug"][0]:
                            drug_info = patient["drug"][0]["medicinalproduct"]

            # Limit reactions to avoid too much data
            if len(reactions) > 3:
                reactions = reactions[:3] + ["...and more"]

            formatted_output += f"Event #{i}:\n"
            formatted_output += f"  Drug: {drug_info}\n"
            formatted_output += f"  Date: {formatted_date}\n"
            formatted_output += f"  Severity: {serious}\n"
            formatted_output += f"  Reactions: {', '.join(reactions) if reactions else 'No reactions recorded'}\n\n"

        # Apply token limit and return formatted string
        return truncate_to_token_limit(formatted_output, max_tokens=2000)

    except Exception as e:
        return f"Error fetching adverse events: {str(e)}"


# Financial Report Tool
@tool
def read_financial_report(query: str = ""):
    """Search and read financial reports. This tool can:
    1. Find specific information, phrases, or sentences in PDF documents
    2. Search for people's names, company details, locations, etc.
    3. Answer questions about financial data, revenue, profits, etc.
    4. Extract specific text passages and their context
    5. Search across multiple PDF files automatically

    Examples: 'Grünenthal is headquartered', 'who wrote this report', 'revenue 2023', 'author name', 'headquarters location'
    """
    import os
    import glob

    data_folder = "data"

    try:
        # If query looks like a file path, use it directly
        if query.endswith(".pdf") and os.path.exists(query):
            pdf_path = query
        elif query.endswith(".pdf") and os.path.exists(
            os.path.join(data_folder, query)
        ):
            pdf_path = os.path.join(data_folder, query)
        else:
            # Look for PDF files in the data folder
            pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))

            if not pdf_files:
                return f"No PDF files found in the '{data_folder}' folder. Please place your financial report PDF in this folder.\n\nExample: {data_folder}/grunenthal_annual_report_2024.pdf"

            # If multiple PDFs, try to find the best match or use the first one
            if len(pdf_files) == 1:
                pdf_path = pdf_files[0]
            else:
                # Try to find a relevant file based on query keywords
                relevant_files = []
                search_terms = ["financial", "annual", "quarterly", "report"]
                for pdf_file in pdf_files:
                    filename_lower = os.path.basename(pdf_file).lower()
                    if any(term in filename_lower for term in search_terms):
                        relevant_files.append(pdf_file)

                if relevant_files:
                    pdf_path = relevant_files[0]  # Use first relevant file
                else:
                    pdf_path = pdf_files[
                        0
                    ]  # Fallback to first file        # Read the PDF with page tracking
        doc = fitz.open(pdf_path)
        text = ""
        page_texts = []  # Store text by page for page number tracking

        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            page_texts.append((page_num, page_text))
            text += f"\n--- PAGE {page_num} ---\n" + page_text
        doc.close()

        if not text.strip():
            return (
                f"Error: PDF file '{pdf_path}' appears to be empty or could not be read"
            )

        # If query is provided, try to find relevant sections with page numbers
        if query and not query.endswith(".pdf"):
            # Enhanced search to find exact phrases and provide page numbers
            query_lower = query.lower()
            relevant_sections = []

            # Search for exact phrase first
            for page_num, page_text in page_texts:
                if query_lower in page_text.lower():
                    # Find the specific line and context
                    lines = page_text.split("\n")
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            # Get context around the match
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = "\n".join(lines[start:end])
                            relevant_sections.append(f"[PAGE {page_num}] {context}")

            # If exact phrase not found, do keyword search
            if not relevant_sections:
                query_words = query_lower.split()
                for page_num, page_text in page_texts:
                    lines = page_text.split("\n")
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        if any(word in line_lower for word in query_words):
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = "\n".join(lines[start:end])
                            relevant_sections.append(f"[PAGE {page_num}] {context}")

            if relevant_sections:
                # Remove duplicates and limit results
                unique_sections = []
                seen = set()
                for section in relevant_sections:
                    if section not in seen:
                        unique_sections.append(section)
                        seen.add(section)
                        if len(unique_sections) >= 10:  # Limit to 10 sections
                            break

                text = "\n\n".join(unique_sections)

        # Format the output nicely
        filename = os.path.basename(pdf_path)
        formatted_output = f"Financial Report Summary (from {filename}):\n\n"
        formatted_output += text

        # Apply token limit (max 1500 tokens for this tool)
        return truncate_to_token_limit(formatted_output, max_tokens=1500)

    except Exception as e:
        return f"Error reading financial report: {str(e)}\n\nMake sure to place your PDF file in the '{data_folder}' folder."


# Token management
def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text for a given model"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(str(text)))
    except:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(str(text)) // 4


def truncate_to_token_limit(data, max_tokens: int = 2000, model: str = "gpt-4") -> str:
    """Truncate data to stay within token limits"""
    text = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)

    current_tokens = count_tokens(text, model)

    if current_tokens <= max_tokens:
        return text

    # If it's too long, truncate and add summary
    truncated_length = int(
        len(text) * (max_tokens / current_tokens) * 0.8
    )  # 80% safety margin
    truncated_text = text[:truncated_length]

    return f"{truncated_text}...\n\n[TRUNCATED - Original response was {current_tokens} tokens, truncated to ~{max_tokens} tokens]"


def post_process_query(cypher_query: str, original_question: str) -> str:
    """Post-process the generated Cypher query to fix common issues."""

    # Fix deprecated relationship syntax
    cypher_query = cypher_query.replace("|:", "|")

    # Enhanced drug detection - check for drug names anywhere in the question
    question_lower = original_question.lower()
    drug_mentioned = None

    # More comprehensive drug list and detection
    drugs_to_check = [
        "TRAMADOL",
        "ASPIRIN",
        "IBUPROFEN",
        "METFORMIN",
        "REVLIMID",
        "CUVITRU",
    ]

    for drug in drugs_to_check:
        if drug.lower() in question_lower:
            drug_mentioned = drug
            break

    # Also check for common drug-related keywords that suggest a specific drug query
    drug_keywords = [
        "manufactures",
        "manufacturer",
        "side effects",
        "reactions",
        "adverse",
    ]
    has_drug_context = any(keyword in question_lower for keyword in drug_keywords)

    if (
        drug_mentioned
        and ("d:Drug" in cypher_query or "Drug)" in cypher_query)
        and has_drug_context
    ):
        # Check if drug filter is missing
        has_filter = (
            f"{{name: '{drug_mentioned}'}}" in cypher_query
            or f"{{name:'{drug_mentioned}'}}" in cypher_query
            or (
                f"WHERE" in cypher_query
                and drug_mentioned.lower() in cypher_query.lower()
            )
        )

        if not has_filter:
            # Strategy 1: Replace (d:Drug) with property match - most reliable
            if "(d:Drug)" in cypher_query:
                cypher_query = cypher_query.replace(
                    "(d:Drug)",
                    f"(d:Drug {{name: '{drug_mentioned}'}})",
                    1,  # Only replace first occurrence
                )

            # Strategy 2: Add WHERE clause systematically
            elif "WHERE" not in cypher_query:
                # For single-line queries, add WHERE before RETURN
                if "\n" not in cypher_query and "RETURN" in cypher_query:
                    parts = cypher_query.split("RETURN")
                    if len(parts) == 2:
                        cypher_query = f"{parts[0].strip()} WHERE toLower(d.name) CONTAINS '{drug_mentioned.lower()}' RETURN{parts[1]}"

                # For multi-line queries
                else:
                    lines = cypher_query.split("\n")
                    new_lines = []
                    inserted_where = False

                    for line in lines:
                        new_lines.append(line)
                        # Insert WHERE after any MATCH line that contains d:Drug
                        if (
                            not inserted_where
                            and line.strip().startswith("MATCH")
                            and "d:Drug" in line
                        ):
                            new_lines.append(
                                f"WHERE toLower(d.name) CONTAINS '{drug_mentioned.lower()}'"
                            )
                            inserted_where = True

                    # If we couldn't insert after MATCH, try before RETURN
                    if not inserted_where:
                        final_lines = []
                        for line in new_lines:
                            if line.strip().startswith("RETURN") and not inserted_where:
                                final_lines.append(
                                    f"WHERE toLower(d.name) CONTAINS '{drug_mentioned.lower()}'"
                                )
                                inserted_where = True
                            final_lines.append(line)
                        new_lines = final_lines

                    cypher_query = "\n".join(new_lines)

    return cypher_query


# Simple Neo4j test tool
@tool
def test_neo4j_schema():
    """Test what's actually in the Neo4j database"""
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()

            with driver.session(database=DB) as session:
                # Get basic database info
                result = "Neo4j Database Schema Analysis:\n\n"

                # Node labels
                labels = session.run("CALL db.labels()").data()
                result += f"Node Labels: {[r['label'] for r in labels]}\n\n"

                # Relationship types
                rels = session.run("CALL db.relationshipTypes()").data()
                result += (
                    f"Relationship Types: {[r['relationshipType'] for r in rels]}\n\n"
                )

                # Sample nodes for each label
                for label_record in labels[:5]:  # Check first 5 labels
                    label = label_record["label"]
                    sample = session.run(f"MATCH (n:{label}) RETURN n LIMIT 3").data()
                    result += f"Sample {label} nodes:\n"
                    for i, node in enumerate(sample, 1):
                        props = dict(node["n"])
                        result += f"  {i}. {props}\n"
                    result += "\n"

                return result

    except Exception as e:
        return f"Error: {str(e)}"
