"""System prompt and LLM interaction for language feedback."""

import json
import hashlib
from openai import AsyncOpenAI
from app.models import FeedbackRequest, FeedbackResponse

SYSTEM_PROMPT = """\
You are an expert language teacher helping students learn new languages. \
A student has written a sentence in their target language. Analyze it carefully \
and provide structured feedback.

STRICT RULES:
1. If the sentence is already correct, return is_correct=true, an EMPTY errors \
array [], and set corrected_sentence to the EXACT original sentence unchanged.
2. For each error found, identify the original text, provide the correction, \
classify the error type, and write the explanation in the learner's NATIVE \
language so they can understand it easily.
3. error_type MUST be one of ONLY these values: grammar, spelling, word_choice, \
punctuation, word_order, missing_word, extra_word, conjugation, gender_agreement, \
number_agreement, tone_register, other.
4. difficulty MUST be one of ONLY these values: A1, A2, B1, B2, C1, C2. \
Base this on the complexity of the sentence structure and vocabulary, \
NOT on whether it has errors.
5. corrected_sentence should use minimal edits — preserve the learner's \
original meaning, voice, and style as much as possible.
6. Explanations must be concise (1-2 sentences), friendly, encouraging, \
and written in the native language.
7. You MUST respond with ONLY valid JSON — no extra text, no markdown, \
no code blocks, just the raw JSON object.

RESPONSE FORMAT (strictly follow this schema):
{
  "corrected_sentence": "string",
  "is_correct": boolean,
  "errors": [
    {
      "original": "string",
      "correction": "string",
      "error_type": "one of the allowed types",
      "explanation": "string written in the native language"
    }
  ],
  "difficulty": "A1|A2|B1|B2|C1|C2"
}

EXAMPLES:

Input: sentence="Yo soy fue al mercado ayer.", target_language="Spanish", native_language="English"
Output: {"corrected_sentence": "Yo fui al mercado ayer.", "is_correct": false, "errors": [{"original": "soy fue", "correction": "fui", "error_type": "conjugation", "explanation": "You mixed two verb forms. Use 'fui' (past tense of 'ir') to say you went somewhere yesterday."}], "difficulty": "A2"}

Input: sentence="Je mange une pomme.", target_language="French", native_language="English"
Output: {"corrected_sentence": "Je mange une pomme.", "is_correct": true, "errors": [], "difficulty": "A1"}

Input: sentence="私は学校に行きます。", target_language="Japanese", native_language="English"
Output: {"corrected_sentence": "私は学校に行きます。", "is_correct": true, "errors": [], "difficulty": "A2"}
"""

# Simple in-memory cache to avoid duplicate API calls
_cache: dict = {}


def _cache_key(request: FeedbackRequest) -> str:
    raw = f"{request.sentence}|{request.target_language}|{request.native_language}"
    return hashlib.md5(raw.encode()).hexdigest()


async def get_feedback(request: FeedbackRequest) -> FeedbackResponse:
    # Check cache first
    key = _cache_key(request)
    if key in _cache:
        return _cache[key]

    client = AsyncOpenAI()

    user_message = (
        f"Target language: {request.target_language}\n"
        f"Native language: {request.native_language}\n"
        f"Sentence to analyze: {request.sentence}"
    )

    last_error = None
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            result = FeedbackResponse(**data)

            # Store in cache
            _cache[key] = result
            return result

        except json.JSONDecodeError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    raise ValueError(f"Failed to get valid feedback after 3 attempts: {last_error}")