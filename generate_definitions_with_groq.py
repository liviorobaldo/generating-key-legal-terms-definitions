"""
Script to generate definitions for legislation terms using Groq API.
Supports both Llama-40b and Deepseek-r1-70b models.
Processes items from selected.json and generates definitions with confidence levels.
"""

import re
import os
import json
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

# Groq API configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def load_prompt_template():
    """Load the prompt template from prompt.txt"""
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("prompt.txt file not found!")


def call_groq(prompt_text, model="llama-3.3-70b-versatile"):
    """
    Call Groq API with the prompt and return the response.
    
    Args:
        prompt_text: The prompt to send
        model: Model to use - Available Groq models:
              - "llama-3.3-70b-versatile" (Llama-3-70b)
              - "deepseek-r1-distill-llama-70b" (Deepseek-r1-70b)
              Check https://console.groq.com/docs/models for exact model names.
    """
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "max_tokens": 4096,
            "temperature": 0.1
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    except Exception as e:
        print(f"Error calling Groq API with model {model}: {str(e)}")
        raise


def generate_definition_for_item(item, model="llama-3.3-70b-versatile"):
    """
    Generate definition for a single item from selected.json using Groq.
    Returns a dictionary with the definition and metadata
    
    Args:
        item: Item from selected.json
        model: Model to use ("llama-3.3-70b-versatile" for Llama-3-70b or "deepseek-r1-distill-llama-70b" for Deepseek)
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
    
    # Call Groq to get definition JSON string
    definition_str = call_groq(prompt_text, model=model)
    
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
        "model": model,
        "act_url": act_url,
        "paragraphs_urls": paragraphs_urls,
    }
    
    # Add paragraphs texts dynamically
    for idx, para_text in enumerate(paragraphs_texts, start=1):
        result[f"paragraphs_texts_{idx}"] = para_text
    
    return result


def main(input_file='selected.json', output_file='definitions_groq.json', model="llama-3.3-70b-versatile", limit=None):
    """
    Main function to process selected.json and generate definitions using Groq.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        model: Model to use ("llama-3.3-70b-versatile" for Llama-3-70b or "deepseek-r1-distill-llama-70b" for Deepseek)
        limit: Number of items to process (None for all)
    """
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Limit to first N items if specified
    if limit:
        data = data[:limit]
        print(f"Processing first {limit} items with model {model}...")
    
    results = []
    total = len(data)
    
    for idx, item in enumerate(data, 1):
        key_phrase = item.get("key_phrase", "")
        print(f"\n[{idx}/{total}] Processing: {key_phrase}")
        
        try:
            result = generate_definition_for_item(item, model=model)
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
    
    print(f"✓ Generated {len(results)} definitions using {model}")
    return results


if __name__ == "__main__":
    import sys
    
    # Default model
    model = "llama-3.3-70b-versatile"
    limit = None
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        model = sys.argv[1]  # First arg: model name
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])  # Second arg: limit
    
    main(model=model, limit=limit)

