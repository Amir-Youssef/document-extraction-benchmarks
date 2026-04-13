import type { DocumentTypeOption, ExtractedDocument, LLMModelOption } from "./types";

const BASE_URL = "http://localhost:8000";

export async function fetchDocumentTypes(): Promise<DocumentTypeOption[]> {
  const response = await fetch(`${BASE_URL}/v1/document-types`);
  if (!response.ok) {
    throw new Error("Falha ao carregar tipos de documento");
  }
  return response.json() as Promise<DocumentTypeOption[]>;
}

export async function fetchLLMModels(): Promise<LLMModelOption[]> {
  const response = await fetch(`${BASE_URL}/v1/llm-models`);
  if (!response.ok) {
    throw new Error("Falha ao carregar modelos LLM");
  }
  return response.json() as Promise<LLMModelOption[]>;
}

export async function extractDocument(
  file: File,
  documentType: string,
  llmModel?: string
): Promise<ExtractedDocument> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  if (llmModel) {
    formData.append("llm_model", llmModel);
  }

  const response = await fetch(`${BASE_URL}/v1/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json();
    const message = body.detail ?? "Erro desconhecido";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return response.json() as Promise<ExtractedDocument>;
}
