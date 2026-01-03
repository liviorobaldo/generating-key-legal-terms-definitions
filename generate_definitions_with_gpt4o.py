"""
Script to generate definitions for legislation terms using GPT-4o-mini API.
Processes items from selected.json and generates definitions with confidence levels.
"""

import re
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file. Please add it.")

client = OpenAI(api_key=api_key)

def load_prompt_template():
    """Load the prompt template from prompt.txt"""
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("prompt.txt file not found!")


def call_gpt4o_mini(prompt_text):
    """
    Call GPT-4o-mini API with the prompt and return the response.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=4096,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error calling GPT-4o-mini API: {str(e)}")
        raise


def generate_definition_for_item(item):
    """
    Generate definition for a single item from selected.json
    Returns a dictionary with the definition and metadata
    """
    # Load prompt template
    prompt_template = load_prompt_template()
    
    prompt_text = prompt_template + "\n\n"
    
    # Add key legal term
    key_phrase = item.get("key_phrase", "")
    prompt_text += f"Key legal term: {key_phrase}\n\n"
    
    # Add UK act URL (if exists)
    legislation_urls = item.get("legislation_urls", [])
    act_url = ""
    if legislation_urls:
        # Truncate URL at "/section"
        act_url = legislation_urls[0].split("/section")[0]
    prompt_text += f"URL of the UK act from which the term is taken: {act_url}\n\n"
    
    # Add paragraphs
    paragraphs_urls = []
    paragraphs_texts = []
    for i, paragraph in enumerate(item.get("paragraphs", []), start=1):
        text = paragraph.get("paragraph_text", "")
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        prompt_text += f"Paragraph #{i}: {cleaned_text}\n\n"
        
        # Collect paragraph URLs and texts
        paragraphs_urls.append(paragraph.get("case_law_url", ""))
        paragraphs_texts.append(text)
    
    # Call GPT-4o-mini to get definition JSON string
    definition_str = call_gpt4o_mini(prompt_text)
    
    # Parse JSON response
    try:
        definition_json = json.loads(definition_str)
    except json.JSONDecodeError as e:
        print(f"JSON decoding failed for key phrase: {key_phrase}")
        print(f"Response: {definition_str[:500]}...")
        raise
    
    # Build the result object
    result = {
        "key_phrase": definition_json.get("key legal term", key_phrase),
        "definition": definition_json.get("definition", ""),
        "reasoning": definition_json.get("reasoning", ""),
        "confidence": definition_json.get("confidence", "Low"),
        "model": "gpt-4o-mini",
        "act_url": act_url,
        "paragraphs_urls": paragraphs_urls,
    }
    
    # Add paragraphs texts dynamically
    for idx, para_text in enumerate(paragraphs_texts, start=1):
        result[f"paragraphs_texts_{idx}"] = para_text
    
    return result


def main(input_file='selected.json', output_file='definitions_gpt4o_mini.json', limit=None):
    """
    Main function to process selected.json and generate definitions using GPT-4o-mini.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        limit: Number of items to process (None for all)
    """
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Limit to first N items if specified
    if limit:
        data = data[:limit]
        print(f"Processing first {limit} items...")
    
    results = []
    total = len(data)
    
    for idx, item in enumerate(data, 1):
        key_phrase = item.get("key_phrase", "")
        print(f"\n[{idx}/{total}] Processing: {key_phrase}")
        
        try:
            result = generate_definition_for_item(item)
            results.append(result)
            print(f"✓ Generated definition with confidence: {result.get('confidence', 'Unknown')}")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error processing {key_phrase}: {str(e)}")
            # Continue with next item
            continue
    
    # Save results
    print(f"\nSaving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Generated {len(results)} definitions using GPT-4o-mini")
    return results


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit=limit)

