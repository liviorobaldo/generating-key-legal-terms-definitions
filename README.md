# Generating Key Legal Terms Definitions

A multi-model system for generating legal term definitions from UK legislation and case law using multiple AI models with confidence-based adjudication.

## Overview

This system generates definitions for key legal terms by:
1. **First Step**: Generating definitions using three different AI models:
   - **GPT-4o-mini** (OpenAI)
   - **Llama-3.3-70b-versatile** (via Groq API)
   - **Deepseek-r1-distill-llama-70b** (via Groq API)

2. **Adjudication Step**: Using Claude Sonnet 4 to:
   - **Select the best definition** if 2 or more models return High confidence
   - **Regenerate the definition** if all 3 models return Low or Medium confidence

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: Generate Definitions (3 Models)              │
├─────────────────────────────────────────────────────────┤
│  • GPT-4o-mini (OpenAI)                                 │
│  • Llama-3.3-70b-versatile (Groq)                       │
│  • Deepseek-r1-distill-llama-70b (Groq)                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: Adjudication (Claude Sonnet 4)                 │
├─────────────────────────────────────────────────────────┤
│  IF 2+ models have High confidence:                     │
│    → Select best definition                            │
│  IF all models have Low/Medium confidence:              │
│    → Regenerate definition                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: Combine Results                               │
│  • All model outputs                                     │
│  • Adjudicated final definitions                        │
└─────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Input File

Ensure you have `selected.json` in the project root. This file should contain an array of objects with:
- `key_phrase`: The legal term to define
- `legislation_urls`: Array of UK legislation URLs
- `paragraphs`: Array of case law paragraphs with:
  - `case_law_url`: URL of the case law
  - `paragraph_text`: Text of the paragraph

## Usage

### Run the Complete System

Run the full pipeline on a specified number of key phrases:

```bash
python run_multi_model_system.py [NUMBER]
```

**Example** (process 2 key phrases):
```bash
python run_multi_model_system.py 2
```

**Example** (process all key phrases):
```bash
python run_multi_model_system.py
```

### Run Individual Components

#### Generate definitions with GPT-4o-mini:
```bash
python generate_definitions_with_gpt4o.py [LIMIT]
```

#### Generate definitions with Groq (Llama or Deepseek):
```bash
python generate_definitions_with_groq.py [MODEL_NAME] [LIMIT]
```

**Examples**:
```bash
# Llama-3.3-70b
python generate_definitions_with_groq.py llama-3.3-70b-versatile 2

# Deepseek-r1-70b
python generate_definitions_with_groq.py deepseek-r1-distill-llama-70b 2
```

#### Adjudicate definitions:
```bash
python adjudicate_definitions.py [LIMIT]
```

#### Combine results:
```bash
python combine_results.py
```

## File Structure

### Configuration Files

- **`prompt.txt`**: Prompt template for generating definitions
- **`prompt_for_ajudication.txt`**: Prompt template for adjudication/selection
- **`requirements.txt`**: Python dependencies
- **`.env`**: Environment variables (API keys) - **not committed to git**
- **`.gitignore`**: Git ignore rules

### Input/Output Files

- **`selected.json`**: Input file with key phrases and case law paragraphs
- **`definitions_gpt4o_mini.json`**: Output from GPT-4o-mini
- **`definitions_llama.json`**: Output from Llama-3.3-70b
- **`definitions_deepseek.json`**: Output from Deepseek-r1-70b
- **`definitions_adjudicated.json`**: Final adjudicated definitions
- **`final_combined_results.json`**: Combined results from all models
