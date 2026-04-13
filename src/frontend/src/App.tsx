import { useEffect, useState } from "react";
import { extractDocument, fetchDocumentTypes, fetchLLMModels } from "./api";
import type { DocumentTypeOption, LLMModelOption } from "./types";

export default function App() {
  const [documentTypes, setDocumentTypes] = useState<DocumentTypeOption[]>([]);
  const [llmModels, setLLMModels] = useState<LLMModelOption[]>([]);
  const [selectedType, setSelectedType] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDocumentTypes()
      .then(setDocumentTypes)
      .catch(() => setError("Falha ao carregar tipos de documento"));
    fetchLLMModels()
      .then(setLLMModels)
      .catch(() => setError("Falha ao carregar modelos LLM"));
  }, []);

  const canSubmit = file !== null && selectedType !== "" && !loading;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !selectedType) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await extractDocument(file, selectedType, selectedModel || undefined);
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>Doc Extractor</h1>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="file">Arquivo (PDF ou imagem)</label>
          <input
            id="file"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.webp"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className="field">
          <label htmlFor="doc-type">Tipo de documento</label>
          <select
            id="doc-type"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="">Selecione...</option>
            {documentTypes.map((dt) => (
              <option key={dt.value} value={dt.value}>
                {dt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="llm-model">Modelo LLM</label>
          <select
            id="llm-model"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="">Padrão</option>
            {llmModels.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={!canSubmit}>
          {loading ? "Enviando..." : "Enviar"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <label>Resultado:</label>
          <pre>{result}</pre>
        </div>
      )}
    </div>
  );
}
