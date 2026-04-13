export interface DocumentTypeOption {
  value: string;
  label: string;
}

export interface LLMModelOption {
  value: string;
  label: string;
}

export interface ExtractedDocument {
  document_type: string;
  data: Record<string, unknown>;
}

export interface ApiError {
  detail: string;
}
