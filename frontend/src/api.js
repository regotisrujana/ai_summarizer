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
