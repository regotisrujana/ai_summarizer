/**
 * API helper — talks to the FastAPI backend.
 */
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function summarizeContent({ text, url }) {
  const response = await axios.post(`${API_URL}/summarize`, {
    text: text || "",
    url: url || "",
  });
  return response.data;
}

export async function askRagChatbot({ question, topK = 3 }) {
  const response = await axios.post(`${API_URL}/chat`, {
    question,
    top_k: topK,
  });
  return response.data;
}

export async function evaluateRag() {
  const response = await axios.get(`${API_URL}/rag/evaluate`);
  return response.data;
}
