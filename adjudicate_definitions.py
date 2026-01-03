"""
Script to adjudicate definitions from multiple models.
- If all three models return Low or Medium confidence, Claude Sonnet 4 regenerates the definition
- If two or all three models provide High confidence, Claude Sonnet 4 selects the most accurate definition
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Initialize Anthropic client
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file. Please add it.")

client = Anthropic(api_key=api_key)

def load_prompt_template():
    """Load the original prompt template from prompt.txt"""
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("prompt.txt file not found!")


def load_adjudication_prompt_template():
    """Load the adjudication prompt template from prompt_for_ajudication.txt"""
    try:
        with open('prompt_for_ajudication.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("prompt_for_ajudication.txt file not found!")


def call_claude_sonnet(prompt_text):
    """
    Call Claude Sonnet 4 API with the prompt and return the response.
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


def get_confidence_level(confidence_str):
    """Convert confidence string to numeric level for comparison"""
    confidence_lower = confidence_str.lower() if confidence_str else "low"
    if confidence_lower == "high":
        return 3
    elif confidence_lower == "medium":
        return 2
    else:
        return 1


def adjudicate_definitions(item_data, definitions):
    """
    Adjudicate definitions based on confidence levels.
    
    Args:
        item_data: Original item data from selected.json
        definitions: List of definition dictionaries from different models
    
    Returns:
        Final adjudicated definition dictionary
    """
    # Count confidence levels
    confidence_levels = [get_confidence_level(d.get("confidence", "Low")) for d in definitions]
    high_count = sum(1 for c in confidence_levels if c == 3)
    
    # Get original item data for regeneration
    key_phrase = item_data.get("key_phrase", "")
    legislation_urls = item_data.get("legislation_urls", [])
    paragraphs = item_data.get("paragraphs", [])
    
    act_url = ""
    if legislation_urls:
        act_url = legislation_urls[0].split("/section")[0]
    
    if high_count >= 2:
        # Two or more models have High confidence - select best definition
        print(f"  → {high_count} models have High confidence. Selecting best definition...")
        
        adjudication_prompt = load_adjudication_prompt_template()
        adjudication_prompt += "\n\n"
        adjudication_prompt += f"Key legal term: {key_phrase}\n\n"
        adjudication_prompt += f"URL of the UK act from which the term is taken: {act_url}\n\n"
        
        # Add paragraphs
        for i, paragraph in enumerate(paragraphs, start=1):
            text = paragraph.get("paragraph_text", "")
            import re
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            adjudication_prompt += f"Paragraph #{i}: {cleaned_text}\n\n"
        
        # Add definitions from models with High confidence
        high_definitions = [d for d in definitions if get_confidence_level(d.get("confidence", "Low")) == 3]
        adjudication_prompt += "\nDefinitions to select from:\n\n"
        for idx, defn in enumerate(high_definitions, 1):
            adjudication_prompt += f"Definition {idx} (from {defn.get('model', 'unknown')}):\n"
            adjudication_prompt += f"{defn.get('definition', '')}\n\n"
        
        # Call Claude to select best definition
        response_str = call_claude_sonnet(adjudication_prompt)
        
        try:
            response_json = json.loads(response_str)
            final_definition = {
                "key_phrase": response_json.get("key legal term", key_phrase),
                "definition": response_json.get("definition", ""),
                "reasoning": response_json.get("reasoning", ""),
                "confidence": "High (Selected)",
                "adjudication_method": "selection",
                "models_used": [d.get("model") for d in high_definitions],
                "act_url": act_url,
                "paragraphs_urls": [p.get("case_law_url", "") for p in paragraphs],
            }
            
            # Add paragraphs texts
            for idx, para in enumerate(paragraphs, start=1):
                final_definition[f"paragraphs_texts_{idx}"] = para.get("paragraph_text", "")
            
            return final_definition
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parsing error in selection: {str(e)}")
            # Fall back to first high confidence definition
            return high_definitions[0]
    
    else:
        # All models have Low or Medium confidence - regenerate
        print(f"  → All models have Low/Medium confidence. Regenerating with Claude Sonnet 4...")
        
        original_prompt = load_prompt_template()
        original_prompt += "\n\n"
        original_prompt += f"Key legal term: {key_phrase}\n\n"
        original_prompt += f"URL of the UK act from which the term is taken: {act_url}\n\n"
        
        # Add paragraphs
        for i, paragraph in enumerate(paragraphs, start=1):
            text = paragraph.get("paragraph_text", "")
            import re
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            original_prompt += f"Paragraph #{i}: {cleaned_text}\n\n"
        
        # Call Claude to regenerate
        response_str = call_claude_sonnet(original_prompt)
        
        try:
            response_json = json.loads(response_str)
            final_definition = {
                "key_phrase": response_json.get("key legal term", key_phrase),
                "definition": response_json.get("definition", ""),
                "reasoning": response_json.get("reasoning", ""),
                "confidence": response_json.get("confidence", "Low"),
                "adjudication_method": "regeneration",
                "models_used": [d.get("model") for d in definitions],
                "act_url": act_url,
                "paragraphs_urls": [p.get("case_law_url", "") for p in paragraphs],
            }
            
            # Add paragraphs texts
            for idx, para in enumerate(paragraphs, start=1):
                final_definition[f"paragraphs_texts_{idx}"] = para.get("paragraph_text", "")
            
            return final_definition
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parsing error in regeneration: {str(e)}")
            # Fall back to first definition
            return definitions[0]


def main(claude_definitions_file=None,
         gpt4o_definitions_file='definitions_gpt4o_mini.json',
         llama_definitions_file='definitions_llama.json',
         deepseek_definitions_file='definitions_deepseek.json',
         original_data_file='selected.json',
         output_file='definitions_adjudicated.json',
         limit=None):
    """
    Main function to adjudicate definitions from multiple models.
    Claude Sonnet 4 is used for adjudication/regeneration, not in the first step.
    
    Args:
        claude_definitions_file: Not used (Claude only for adjudication)
        gpt4o_definitions_file: File with GPT-4o-mini definitions
        llama_definitions_file: File with Llama definitions
        deepseek_definitions_file: File with Deepseek definitions
        original_data_file: Original selected.json file
        output_file: Output file for adjudicated definitions
        limit: Number of items to process (None for all)
    """
    print("Loading definitions from all models...")
    
    # Load all definition files
    with open(gpt4o_definitions_file, 'r', encoding='utf-8') as f:
        gpt4o_defs = json.load(f)
    
    with open(llama_definitions_file, 'r', encoding='utf-8') as f:
        llama_defs = json.load(f)
    
    with open(deepseek_definitions_file, 'r', encoding='utf-8') as f:
        deepseek_defs = json.load(f)
    
    # Load original data
    with open(original_data_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Limit if specified
    if limit:
        gpt4o_defs = gpt4o_defs[:limit]
        llama_defs = llama_defs[:limit]
        deepseek_defs = deepseek_defs[:limit]
        original_data = original_data[:limit]
    
    # Create dictionaries keyed by key_phrase for easier lookup
    gpt4o_dict = {d.get("key_phrase"): d for d in gpt4o_defs}
    llama_dict = {d.get("key_phrase"): d for d in llama_defs}
    deepseek_dict = {d.get("key_phrase"): d for d in deepseek_defs}
    
    results = []
    total = len(original_data)
    
    for idx, item in enumerate(original_data, 1):
        key_phrase = item.get("key_phrase", "")
        print(f"\n[{idx}/{total}] Adjudicating: {key_phrase}")
        
        # Get definitions from all three models
        definitions = []
        if key_phrase in gpt4o_dict:
            definitions.append(gpt4o_dict[key_phrase])
            print(f"  GPT-4o-mini: {gpt4o_dict[key_phrase].get('confidence', 'Unknown')}")
        if key_phrase in llama_dict:
            definitions.append(llama_dict[key_phrase])
            print(f"  Llama-3.3-70b: {llama_dict[key_phrase].get('confidence', 'Unknown')}")
        if key_phrase in deepseek_dict:
            definitions.append(deepseek_dict[key_phrase])
            print(f"  Deepseek-r1-70b: {deepseek_dict[key_phrase].get('confidence', 'Unknown')}")
        
        if not definitions:
            print(f"  ✗ No definitions found for {key_phrase}")
            continue
        
        try:
            # Adjudicate
            final_definition = adjudicate_definitions(item, definitions)
            results.append(final_definition)
            print(f"  ✓ Adjudicated using method: {final_definition.get('adjudication_method', 'unknown')}")
            
        except Exception as e:
            print(f"  ✗ Error adjudicating {key_phrase}: {str(e)}")
            # Use first available definition as fallback
            if definitions:
                results.append(definitions[0])
            continue
    
    # Save results
    print(f"\nSaving adjudicated results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Adjudicated {len(results)} definitions")
    return results


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit=limit)

