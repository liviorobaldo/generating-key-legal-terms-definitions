"""
Main orchestrator script to run the complete multi-model definition generation system.
Runs definitions on GPT-4o-mini, Llama-3-70b, and Deepseek-r1-70b in the first step.
Claude Sonnet 4 is used only for adjudication and regeneration.
"""

import os
import json
import sys
from generate_definitions_with_gpt4o import main as generate_gpt4o_mini
from generate_definitions_with_groq import main as generate_groq
from adjudicate_definitions import main as adjudicate
from combine_results import combine_results


def main(limit=2):
    """
    Main function to run the complete system.
    
    Args:
        limit: Number of key phrases to process (default: 2)
    """
    print("\n" + "="*80)
    print("MULTI-MODEL DEFINITION GENERATION SYSTEM")
    print("="*80)
    print(f"Processing {limit} key phrase(s)...\n")
    
    try:
        # Step 1: Generate with GPT-4o-mini
        print("\n" + "="*80)
        print("STEP 1: Generating definitions with GPT-4o-mini")
        print("="*80)
        generate_gpt4o_mini(input_file='selected.json', 
                           output_file='definitions_gpt4o_mini.json', 
                           limit=limit)
        
        # Step 2: Generate with Groq (Llama-3-70b)
        print("\n" + "="*80)
        print("STEP 2: Generating definitions with Groq (Llama-3.3-70b-versatile)")
        print("="*80)
        generate_groq(input_file='selected.json',
                     output_file='definitions_llama.json',
                     model="llama-3.3-70b-versatile",
                     limit=limit)
        
        # Step 3: Generate with Groq (Deepseek-r1-70b)
        print("\n" + "="*80)
        print("STEP 3: Generating definitions with Groq (deepseek-r1-distill-llama-70b)")
        print("="*80)
        generate_groq(input_file='selected.json',
                     output_file='definitions_deepseek.json',
                     model="deepseek-r1-distill-llama-70b",
                     limit=limit)
        
        # Step 4: Adjudicate definitions (Claude Sonnet 4 used here)
        print("\n" + "="*80)
        print("STEP 4: Adjudicating definitions with Claude Sonnet 4")
        print("="*80)
        adjudicate(claude_definitions_file=None,  # Claude not used in first step
                  gpt4o_definitions_file='definitions_gpt4o_mini.json',
                  llama_definitions_file='definitions_llama.json',
                  deepseek_definitions_file='definitions_deepseek.json',
                  original_data_file='selected.json',
                  output_file='definitions_adjudicated.json',
                  limit=limit)
        
        # Step 5: Combine results
        print("\n" + "="*80)
        print("STEP 5: Combining all results")
        print("="*80)
        combine_results(gpt4o_file='definitions_gpt4o_mini.json',
                       llama_file='definitions_llama.json',
                       deepseek_file='definitions_deepseek.json',
                       adjudicated_file='definitions_adjudicated.json',
                       output_file='final_combined_results.json')
        
        print("\n" + "="*80)
        print("✓ SYSTEM COMPLETE")
        print("="*80)
        print("\nOutput files generated:")
        print("  - definitions_gpt4o_mini.json")
        print("  - definitions_llama.json")
        print("  - definitions_deepseek.json")
        print("  - definitions_adjudicated.json")
        print("  - final_combined_results.json")
        print()
        
    except Exception as e:
        print(f"\n✗ Error in system execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    main(limit=limit)

