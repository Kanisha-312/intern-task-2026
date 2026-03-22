# Language Feedback API

An LLM-powered language feedback API that analyzes learner-written sentences and returns structured correction feedback. Built for Pangea Chat's Gen AI Intern Task (Summer 2026).

## What It Does

Given a sentence in a target language and the learner's native language, the API returns:
- A corrected sentence (minimal edits preserving the learner's voice)
- A list of errors with type, original text, correction, and explanation in the learner's native language
- Whether the sentence is correct (boolean)
- A CEFR difficulty rating (A1–C2)

## Design Decisions

### Model Choice: GPT-4o-mini
I chose `gpt-4o-mini` because it strikes the best balance for production:
- **Fast**: responses well within the 30-second limit
- **Cheap**: ~$0.00015 per 1K tokens — affordable at scale
- **Accurate**: strong multilingual grammar understanding across Latin and non-Latin scripts

### Prompt Engineering
The system prompt is carefully structured to:
- Give the model clear, strict rules about output format
- Include concrete examples (few-shot prompting) to anchor the expected JSON structure
- Explicitly list allowed `error_type` and `difficulty` values to prevent hallucination
- Instruct the model to write explanations in the learner's native language
- Handle edge cases: correct sentences return `is_correct: true` with empty errors array

### Caching
Identical requests (same sentence + languages) return cached results instantly. This means:
- Zero extra API cost for repeated requests
- Faster response times for common sentences
- Simple MD5 hash used as cache key

### Retry Logic
The API retries up to 3 times on failure. This handles occasional LLM timeouts or malformed JSON responses gracefully without exposing errors to the user.

### Multilingual Support
The API handles any language without language-specific logic — the LLM does the heavy lifting. Tested across Latin and non-Latin scripts including Spanish, French, German, Portuguese, Japanese, Hindi, Tamil, Chinese, and Russian.

### Verifying Accuracy for Unknown Languages
Since I don't speak all tested languages, I verified accuracy by:
- Cross-checking corrections with known grammar rules for languages I do know
- Using the LLM itself to verify corrections in languages I don't know
- Checking that non-Latin scripts (Hindi, Tamil, Chinese, Japanese) returned structurally valid responses

## How to Run

### Prerequisites
- Docker Desktop
- OpenAI API key

### Run with Docker (recommended)
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
docker compose up --build
```

Server starts at http://localhost:8000

### Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
uvicorn app.main:app --reload
```

### Test the API
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"sentence": "Yo soy fue al mercado ayer.", "target_language": "Spanish", "native_language": "English"}'
```

### Run Tests
```bash
# Unit tests (no API key needed)
pytest tests/test_feedback_unit.py tests/test_schema.py -v

# Integration tests (requires API key)
pytest tests/test_feedback_integration.py -v
```

## API Endpoints

### POST /feedback
Analyzes a learner's sentence and returns structured feedback.

**Request:**
```json
{
  "sentence": "Yo soy fue al mercado ayer.",
  "target_language": "Spanish",
  "native_language": "English"
}
```

**Response:**
```json
{
  "corrected_sentence": "Yo fui al mercado ayer.",
  "is_correct": false,
  "errors": [
    {
      "original": "soy fue",
      "correction": "fui",
      "error_type": "conjugation",
      "explanation": "You mixed two verb forms. Use 'fui' to say you went somewhere yesterday."
    }
  ],
  "difficulty": "A2"
}
```

### GET /health
Returns 200 if the server is running.

## Tech Stack
- **Python** + **FastAPI** — fast, modern web framework
- **OpenAI gpt-4o-mini** — cost-effective, accurate LLM
- **Docker** — containerized for consistent deployment
- **pytest** — unit, schema, and integration tests