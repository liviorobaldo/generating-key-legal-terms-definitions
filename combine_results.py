"""
Script to combine all results from different stages:
- Original definitions from GPT-4o-mini, Llama-3-70b, and Deepseek-r1-70b
- Adjudicated final definitions (using Claude Sonnet 4)
Combines them into a comprehensive output file.
"""

import json
import os
from datetime import datetime

def combine_results(gpt4o_file='definitions_gpt4o_mini.json',
                   llama_file='definitions_llama.json',
                   deepseek_file='definitions_deepseek.json',
                   adjudicated_file='definitions_adjudicated.json',
                   output_file='key_phrase_definitions.json'):
    """
    Combine all definition results into a comprehensive output.
    
    Args:
        gpt4o_file: GPT-4o-mini definitions file
        llama_file: Llama-3.3-70b definitions file
        deepseek_file: Deepseek-r1-70b definitions file
        adjudicated_file: Adjudicated definitions file
        output_file: Output file for combined results
    """
    print("Loading all definition files...")
    
    # Load all files
    files_to_load = {
        "gpt4o_mini": gpt4o_file,
        "llama": llama_file,
        "deepseek": deepseek_file,
        "adjudicated": adjudicated_file
    }
    
    loaded_data = {}
    for name, filepath in files_to_load.items():
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_data[name] = json.load(f)
                print(f"  ✓ Loaded {name}: {len(loaded_data[name])} definitions")
            except Exception as e:
                print(f"  ✗ Error loading {name} from {filepath}: {str(e)}")
                loaded_data[name] = []
        else:
            print(f"  ⚠ File not found: {filepath}")
            loaded_data[name] = []
    
    # Create dictionaries keyed by key_phrase
    gpt4o_dict = {d.get("key_phrase"): d for d in loaded_data.get("gpt4o_mini", [])}
    llama_dict = {d.get("key_phrase"): d for d in loaded_data.get("llama", [])}
    deepseek_dict = {d.get("key_phrase"): d for d in loaded_data.get("deepseek", [])}
    adjudicated_dict = {d.get("key_phrase"): d for d in loaded_data.get("adjudicated", [])}
    
    # Get all unique key phrases
    all_key_phrases = set()
    all_key_phrases.update(gpt4o_dict.keys())
    all_key_phrases.update(llama_dict.keys())
    all_key_phrases.update(deepseek_dict.keys())
    all_key_phrases.update(adjudicated_dict.keys())
    
    print(f"\nCombining results for {len(all_key_phrases)} unique key phrases...")

    # Combine results
    results = []
    for key_phrase in sorted(all_key_phrases):
        combined_item = {
            "key_phrase": key_phrase
        }
        
        # Add adjudicated result
        if key_phrase in adjudicated_dict:
            adj = adjudicated_dict[key_phrase]
            combined_item["definition"] = adj.get("definition", "")
            combined_item["reasoning"] = adj.get("reasoning", "")
            combined_item["act_url"] = adj.get("act_url", "")
            combined_item["paragraphs_urls"] = adj.get("paragraphs_urls", "")
        #Recovery strategy: if a key phrase is not in the adjudicated results, we take the first occurrence found in any of the other models.
        elif key_phrase in gpt4o_dict:
            combined_item["definition"] = gpt4o_dict[key_phrase].get("definition", "")
            combined_item["reasoning"] = gpt4o_dict[key_phrase].get("reasoning", "")
            combined_item["act_url"] = gpt4o_dict[key_phrase].get("act_url", "")
            combined_item["paragraphs_urls"] = gpt4o_dict[key_phrase].get("paragraphs_urls", "")
        elif key_phrase in llama_dict:
            combined_item["definition"] = llama_dict[key_phrase].get("definition", "")
            combined_item["reasoning"] = llama_dict[key_phrase].get("reasoning", "")
            combined_item["act_url"] = llama_dict[key_phrase].get("act_url", "")
            combined_item["paragraphs_urls"] = llama_dict[key_phrase].get("paragraphs_urls", "")
        elif key_phrase in deepseek_dict:
            combined_item["definition"] = deepseek_dict[key_phrase].get("definition", "")
            combined_item["reasoning"] = deepseek_dict[key_phrase].get("reasoning", "")
            combined_item["act_url"] = deepseek_dict[key_phrase].get("act_url", "")
            combined_item["paragraphs_urls"] = deepseek_dict[key_phrase].get("paragraphs_urls", "")            
        results.append(combined_item)
        

    # Save combined results
    print(f"\nSaving combined results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Combined {len(results)} definitions")
    print(f"  - GPT-4o-mini: {len(gpt4o_dict)}")
    print(f"  - Llama-3.3-70b: {len(llama_dict)}")
    print(f"  - Deepseek-r1-70b: {len(deepseek_dict)}")
    print(f"  - Adjudicated: {len(adjudicated_dict)}")
    
    return results


if __name__ == "__main__":
    combine_results()

