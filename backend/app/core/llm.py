import json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util
import torch
from .config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_relevant_faqs(query: str, faqs_data: list, top_k: int = 3):
    if not faqs_data:
        return []
    faq_questions = [item['question'] for item in faqs_data]
    faq_embeddings = embedding_model.encode(faq_questions, convert_to_tensor=True)
    query_embedding = embedding_model.encode(query, convert_to_tensor=True)
    cos_scores = util.pytorch_cos_sim(query_embedding, faq_embeddings)[0]
    top_results = torch.topk(cos_scores, k=min(top_k, len(faqs_data)))
    relevant_faqs = []
    for score, idx in zip(top_results[0], top_results[1]):
        if score > 0.5:
            relevant_faqs.append(faqs_data[idx])
    return relevant_faqs

def generate_llm_response(query: str, chat_history: list, relevant_faqs: list, bot_name: str):
    history_str = "\n".join([f"{msg.role}: {msg.message}" for msg in chat_history] if chat_history else [])
    context_str = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in relevant_faqs])

    prompt = f"""
You are '{bot_name}', an advanced AI assistant.
Your Persona: You are empathetic, professional, and concise.

**Your Core Directives (Follow in this order):**
1.  **Use Context for Factual Queries:** If "CONTEXT" is available, answer the user's question based strictly on it.
2.  **Reason About Context:** If the user asks a follow-up question related to the context (e.g., "What does 'original condition' mean?"), provide a helpful, general explanation based on common understanding, but explicitly state that the policy details are not specified in your knowledge base.
3.  **Acknowledge User Feedback:** If the user provides feedback or suggests an improvement (e.g., "You should add this to your FAQs", "Tell your admin"), you MUST acknowledge their feedback positively. Example: "Thank you for that suggestion. I will pass it along to the team to improve our knowledge base." Do not re-state that you cannot answer.
4.  **Handle Small Talk:** If no context is found and the query is a simple greeting or question about you, respond conversationally.
5.  **Intelligent Escalation:** If the query fits none of the above, escalate by politely stating you cannot help and recommending contact with a human agent.

**Output Format:** After your response, you MUST include a markdown-fenced JSON object with one key: "suggestions". This should be an array of 2-3 relevant follow-up questions. For feedback, small talk, or escalations, this array should be empty.

---
CONTEXT FROM KNOWLEDGE BASE:
{context_str if relevant_faqs else "No relevant information found."}
---
CONVERSATION HISTORY:
{history_str}
---
User Query: {query}

Response:
"""
    try:
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        response = gemini_model.generate_content(prompt)
        if not response.parts:
            return {"answer": "I'm sorry, my response was blocked. Please rephrase.", "suggestions": []}
        full_text = response.text
        answer, suggestions = full_text, []
        json_start = full_text.find("```json")
        if json_start != -1:
            answer = full_text[:json_start].strip()
            json_str_part = full_text[json_start + 7:]
            json_end = json_str_part.find("```")
            if json_end != -1:
                json_str = json_str_part[:json_end].strip()
                try:
                    suggestions = json.loads(json_str).get("suggestions", [])
                except json.JSONDecodeError:
                    print("Warning: Failed to parse suggestions JSON from LLM response.")
        return {"answer": answer, "suggestions": suggestions}
    except Exception as e:
        print(f"Error generating or parsing LLM response: {e}")
        return {"answer": "I'm sorry, I encountered a technical issue.", "suggestions": []}

def summarize_conversation_for_user(chat_history: list) -> str:
    if not chat_history:
        return "This chat session is empty."
    transcript = "\n".join([f"{msg.role}: {msg.message}" for msg in chat_history])
    prompt = f"""
Summarize the following conversation from the user's perspective. Use the second person ("You asked...", "The bot told you..."). The tone should be a helpful reminder of the conversation's key points. Avoid mentioning technical difficulties.

CONVERSATION TRANSCRIPT:
---
{transcript}
---
SUMMARY FOR USER:
"""
    try:
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        response = gemini_model.generate_content(prompt)
        return response.text.strip() if response.parts else "Could not generate a summary."
    except Exception as e:
        return f"An error occurred during summarization: {e}"

def summarize_conversation_for_admin(chat_history: list) -> str:
    if not chat_history:
        return "This chat session has no messages."
    transcript = "\n".join([f"{msg.role}: {msg.message}" for msg in chat_history])
    prompt = f"""
As a support manager, summarize the following conversation objectively.
1. Identify the user's primary problem.
2. State the bot's solution.
3. Note if the issue was resolved or required escalation.

CONVERSATION TRANSCRIPT:
---
{transcript}
---
OBJECTIVE SUMMARY:
"""
    try:
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        response = gemini_model.generate_content(prompt)
        return response.text.strip() if response.parts else "Could not generate a summary."
    except Exception as e:
        return f"An error occurred during summarization: {e}"

def generate_analytics_summary(summaries: list) -> dict:
    default_response = {"trending_topics": [], "unanswered_questions": [], "suggested_new_faqs": []}
    if not summaries:
        return default_response
    summary_texts = "\n- ".join(summaries)
    prompt = f"""
You are a data analyst. Analyze these chat summaries to identify key insights.
Respond with a single JSON object with three keys: "trending_topics", "unanswered_questions", and "suggested_new_faqs".

1.  **trending_topics**: List the top 3-5 most frequently discussed topics.
2.  **unanswered_questions**: List specific questions users asked that the bot could not answer.
3.  **suggested_new_faqs**: Suggest 2-3 new question-and-answer pairs for the knowledge base.

CHAT SUMMARIES:
- {summary_texts}
---
JSON ANALYSIS:
"""
    try:
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        return json.loads(response.text) if response.parts else default_response
    except Exception as e:
        print(f"Error generating analytics: {e}")
        return {"trending_topics": ["Error generating report due to an internal issue."], "unanswered_questions": [], "suggested_new_faqs": []}
