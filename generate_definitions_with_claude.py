"""
Script to generate definitions for legislation terms using Claude Sonnet API.
Reads final_dataser_of_key_phrases.csv, groups by legislation_term and legislation_id,
and generates definitions based on section_text and case law paragraphs.
"""

import re
import os
import pandas as pd
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
import time

# Load environment variables
load_dotenv()


# Initialize Anthropic client
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file. Please add it.")

client = Anthropic(api_key=api_key)

# Read the prompt template
def load_prompt_template():
    """Load the prompt template from prompt.txt"""
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error("prompt.txt file not found!")
        raise


def format_case_law_paragraphs(group_df):
    """
    Format case law paragraphs for the prompt.
    Groups paragraphs by case law URL and includes para_id.
    """
    paragraphs_list = []
    for idx, row in group_df.iterrows():
        url = row.get('url', 'Unknown URL')
        para_id = row.get('para_id', 'Unknown')
        paragraph = row.get('paragraphs', '')
        
        if pd.notna(paragraph) and paragraph.strip():
            paragraphs_list.append(f"Case Law: {url} (Paragraph: {para_id})\n{paragraph}\n")
    
    return "\n---\n\n".join(paragraphs_list)


def get_case_terms(group_df):
    """
    Extract unique case terms from the group.
    """
    case_terms = group_df['case_term'].dropna().unique().tolist()
    return ", ".join(case_terms) if case_terms else "None identified"


def call_claude_sonnet(prompt_text):
    """
    Call Claude Sonnet API with the prompt and return the response.
    """
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )
        
        # Extract text from response
        response_text = ""
        for content_block in message.content:
            if content_block.type == "text":
                response_text += content_block.text
        
        return response_text.strip()
    
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        raise

def json_to_excel():
    # Load JSON data
    with open("tovalidate.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for item in data:
        row = {}
        for key, value in item.items():
            # Skip unwanted keys
            if key in {"act_url", "paragraphs_urls"}:
                continue
            row[key] = value
        rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Write to Excel
    output_file = "results.xlsx"
    df.to_excel(output_file, index=False)

    print(f"Excel file created: {output_file}")


def main():
    """
    Main function to process the CSV and generate definitions.
    """
    
    # Load prompt template
    prompt_template = load_prompt_template()

    print("\n\n\n")
    with open('selected.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []  # Array to store all the JSON objects
    for item in data:
        tosendtoclaude = prompt_template + "\n\n"

        # Add key legal term
        key_phrase = item.get("key_phrase", "")
        tosendtoclaude += f"Key legal term: {key_phrase}\n\n"

        # Add UK act URL (if exists)
        legislation_urls = item.get("legislation_urls", [])
        act_url = ""
        if legislation_urls:
            # Truncate URL at "/section"
            act_url = legislation_urls[0].split("/section")[0]
        tosendtoclaude += f"URL of the UK act from which the term is taken: {act_url}\n\n"

        # Add paragraphs
        paragraphs_urls = []
        paragraphs_texts = []
        for i, paragraph in enumerate(item.get("paragraphs", []), start=1):
            text = paragraph.get("paragraph_text", "")
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            tosendtoclaude += f"Paragraph #{i}: {cleaned_text}\n\n"

            # Collect paragraph URLs and texts
            paragraphs_urls.append(paragraph.get("case_law_url", ""))
            paragraphs_texts.append(text)

        # Call Claude function to get definition JSON string
        definition_str = call_claude_sonnet(tosendtoclaude)

        # Convert string to JSON object
        #definition_json = json.loads(definition_str)
        
        try:
            definition_json = json.loads(definition_str)
        except json.JSONDecodeError as e:
            print("JSON decoding failed!")
            print("Key phrase causing the error:", key_phrase)
            print("Current contents of results:")
            print(json.dumps(results, ensure_ascii=False, indent=2))
            with open("tovalidate.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            json_to_excel()
            raise  # re-raise the exception so you still see the full traceback

        # Build the final JSON object in the required format
        final_obj = {
            "key_phrase": definition_json.get("key legal term", ""),
            "definition": definition_json.get("definition", ""),
            "reasoning": definition_json.get("reasoning", ""),
            "act_url": act_url,
            "paragraphs_urls": paragraphs_urls,
        }

        # Add paragraphs texts dynamically: paragraphs_texts_1, paragraphs_texts_2, etc.
        for idx, para_text in enumerate(paragraphs_texts, start=1):
            final_obj[f"paragraphs_texts_{idx}"] = para_text

        # Append to results array
        results.append(final_obj)

    with open("tovalidate.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    json_to_excel()


if __name__ == "__main__":
    main()

