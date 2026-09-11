"""Prompts for audio explanations and text-to-speech script generation."""

AUDIO_SCRIPT_PROMPT_TEMPLATE = """You are an expert tutor explaining a page from a document.
Read the following page content and summarize its key points as an engaging, spoken explanation.
CRITICAL RULES:
- Do not use ANY Markdown formatting, bullet points, or special characters.
- Explain equations or tables in plain conversational English.
- Keep it under 150 words.

Page Content: {page_content}"""
