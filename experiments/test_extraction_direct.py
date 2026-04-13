import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz e o 'src' ao PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))

from backend.core.config import settings, MODEL_IDENTIFIERS, VERTEX_MG_MODELS, OLLAMA_VISION_MODELS
from backend.domain.enumx.llm_model import LLMModel
from backend.domain.enumx.document_type import DocumentType
from backend.infra.llm.model_factory import ModelFactory
from backend.infra.llm.gemini_client import PydanticAILLMClient
from backend.infra.llm.vertex_client import VertexAILLMClient
from backend.infra.llm.routing_client import RoutingLLMClient
from backend.infra.llm.vertex_gemma_client import VertexGemmaClient
from backend.infra.llm.ollama_client import OllamaClient
from backend.infra.llm.vllm_client import VLLMClient
from backend.domain.interfaces import LLMClient
from backend.services.factory import ExtractorFactory
from experiments.dataset_loader import load_ground_truth, resolve_file_path
from experiments.metrics import (
    compute_field_matches,
    levenshtein_similarity,
    precision_recall_f1,
    accuracy,
    mean_levenshtein_similarity,
    compute_latency_stats,
)
import time

# ============================================================================
# CONFIGURAÇÃO: MODELO → TIPOS DE DOCUMENTO
# Cada modelo tem sua própria lista de doc types para processar.

#   "afogados", "arrais", "aso", "cnh", "epi", "escavadeira",
#   "ficha_registro", "ltcat","marinheiro", "nr5", "nr10", "nr10sep", "nr11",
#   "nr12", "nr33", "nr35", "operador_treinamento", "pcmso", "pgr", "seguro",

# ============================================================================
MODELS_CONFIG: dict[LLMModel, list[str]] = {
    #LLMModel.GEMINI_31_PRO: [],
    #LLMModel.GEMINI_FLASH: [],
    #LLMModel.KIMI_K2_5: [],
    #LLMModel.GEMMA_3_27B: [],
    #LLMModel.GEMMA_3_12B: [],
    #LLMModel.OLLAMA_GEMMA_3_27B: [], 
    #LLMModel.OLLAMA_GEMMA_3_12B: [],
      
    #LLMModel.QWEN3_VL: [],
    
    #LLMModel.OLLAMA_QWEN3_VL_30B: [], 

    LLMModel.OLLAMA_QWEN3_VL: ["afogados", "pgr"],

    #LLMModel.QWEN_3_5_9B: [],
        
    #LLMModel.QWEN_3_5_27B: [],
    
    #LLMModel.QWEN_3_5_35B: [],

} 

# Mapeamento de nomes curtos para organizar pastas de resultado
_MODEL_SHORT_NAMES: dict[LLMModel, str] = {
    LLMModel.GEMINI_31_PRO: "gemini31_pro",
    LLMModel.GEMINI_FLASH: "gemini_flash",
    LLMModel.KIMI_K2_5: "kimi_k25",
    LLMModel.GEMMA_3_27B: "gemma3_27b",
    LLMModel.GEMMA_3_12B: "gemma3_12b",
    LLMModel.OLLAMA_GEMMA_3_12B: "ollama_gemma3_12b",
    LLMModel.OLLAMA_GEMMA_3_27B: "ollama_gemma3_27b",
    LLMModel.QWEN3_VL: "qwen3_vl",
    LLMModel.OLLAMA_QWEN3_VL: "ollama_qwen3_vl",
    LLMModel.QWEN_3_5_27B: "qwen3.5_27b",
    LLMModel.QWEN_3_5_35B: "qwen3.5_35b",
    LLMModel.QWEN_3_5_9B: "qwen3.5_9b",
    LLMModel.OLLAMA_QWEN3_VL_30B: "ollama_qwen3_vl_30b",
}


_FOLDER_OVERRIDES: dict[str, str] = {
    "ficha_registro": "ficha",
    "nr10sep": "nr10-sep",
}


def _resolve_dataset_folder(dataset_root: Path, doc_type_value: str) -> str | None:
    """Encontra a pasta do dataset para um tipo de documento."""
    if doc_type_value in _FOLDER_OVERRIDES:
        folder = _FOLDER_OVERRIDES[doc_type_value]
        if (dataset_root / folder).exists():
            return folder

    for candidate in [doc_type_value, doc_type_value.replace("_", "")]:
        if (dataset_root / candidate).exists():
            return candidate

    return None


def _build_field_comparison(expected_dict: dict, predicted_dict: dict) -> list[dict]:
    """Compara campo a campo, retornando esperado, extraído, match e levenshtein."""
    field_matches = compute_field_matches(expected_dict, predicted_dict)
    campos = []
    for field_name, exp_norm, pred_norm, match in field_matches:
        extraido_raw = predicted_dict.get(field_name, "")
        campos.append({
            "campo": field_name,
            "esperado": expected_dict.get(field_name, ""),
            "extraido": extraido_raw[:200] if isinstance(extraido_raw, str) else extraido_raw,
            "match": match,
            "levenshtein": round(levenshtein_similarity(exp_norm, pred_norm), 4),
        })
    return campos


async def _run_single_doc_type(
    doc_type: DocumentType,
    model: LLMModel,
    factory: ExtractorFactory,
    dataset_root: Path,
    base_results_dir: Path,
    timestamp: datetime,
):
    """Executa a extração e métricas para um tipo de documento com um modelo."""
    strategy = factory.get_strategy(doc_type)

    target_folder = _resolve_dataset_folder(dataset_root, doc_type.value)
    if not target_folder:
        print(f"  [PULAR] Pasta do dataset para '{doc_type.value}' não encontrada.\n")
        return

    gt_dir = dataset_root.parent / "ground_truth"
    gt_file = gt_dir / f"ground_truth_{target_folder}.json"
    if not gt_file.exists():
        print(f"  [PULAR] Ground truth não encontrado: {gt_file}\n")
        return
    entries = load_ground_truth(gt_file)
    print(f"  Encontrados {len(entries)} documentos na pasta '{target_folder}'.\n")

    if True:
        short_name = _MODEL_SHORT_NAMES.get(model, model.value)
        results_dir = base_results_dir / f"results_{short_name}"
        results_dir.mkdir(parents=True, exist_ok=True)

        print(f"  --- Modelo: {model.value} ({short_name}) ---")
        resultados_por_arquivo = []
        latencias = []
        total_p, total_r, total_f1, total_acc, total_lev = 0.0, 0.0, 0.0, 0.0, 0.0
        processed_count = 0
        erros_count = 0
        field_stats: dict[str, list[tuple[bool, float]]] = defaultdict(list)

        MAX_RETRIES = 2

        for entry in entries:
            print(f"    > Processando: {entry.doc}")

            file_path = resolve_file_path(dataset_root, target_folder, entry.doc)
            with open(file_path, "rb") as f:
                file_content = f.read()

            last_error: str | None = None
            success = False

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    start_time = time.perf_counter()
                    extracted_data = await strategy.extract(
                        file_content=file_content, llm_model=model
                    )
                    latency = round(time.perf_counter() - start_time, 4)
                    latencias.append(latency)

                    predicted_dict = {
                        k: str(v) for k, v in extracted_data.model_dump(mode="json").items()
                    }
                    expected_dict = entry.respostas

                    p, r, f1 = precision_recall_f1(expected_dict, predicted_dict)
                    acc = accuracy(expected_dict, predicted_dict)
                    lev = mean_levenshtein_similarity(expected_dict, predicted_dict)

                    total_p += p
                    total_r += r
                    total_f1 += f1
                    total_acc += acc
                    total_lev += lev
                    processed_count += 1

                    campos = _build_field_comparison(expected_dict, predicted_dict)

                    for c in campos:
                        field_stats[c["campo"]].append((c["match"], c["levenshtein"]))

                    if acc < 1.0:
                        erros_count += 1
                        print(f"      [!] Divergência (Acc: {acc:.2f}, Latência: {latency}s)")
                        campos_com_erro = [c for c in campos if not c["match"]]
                        resultados_por_arquivo.append({
                            "arquivo": entry.doc,
                            "metricas": {
                                "precision": round(p, 4),
                                "recall": round(r, 4),
                                "f1": round(f1, 4),
                                "accuracy": round(acc, 4),
                                "levenshtein": round(lev, 4),
                                "latencia": latency,
                            },
                            "campos": campos_com_erro,
                        })
                    else:
                        print(f"      [OK] 100% de acerto (Latência: {latency}s)")

                    success = True
                    break

                except Exception as e:
                    last_error = str(e)[:200]
                    if attempt < MAX_RETRIES:
                        print(f"      [RETRY {attempt}/{MAX_RETRIES}] Erro: {last_error}")
                    else:
                        print(f"      [FALHA] Erro após {MAX_RETRIES} tentativas: {last_error}")

            if not success:
                erros_count += 1
                resultados_por_arquivo.append({
                    "arquivo": entry.doc,
                    "erro": last_error,
                })

        # Calcula médias
        metricas_por_campo = {}
        for field_name, values in sorted(field_stats.items()):
            total = len(values)
            metricas_por_campo[field_name] = {
                "accuracy": round(sum(1 for m, _ in values if m) / total, 4),
                "mean_levenshtein": round(sum(lev for _, lev in values) / total, 4),
            }

        report = {
            "timestamp": timestamp.isoformat(),
            "tipo_documento": doc_type.value,
            "modelo": short_name,
            "metricas_gerais": {
                "mean_precision": round(total_p / processed_count, 4) if processed_count else 0,
                "mean_recall": round(total_r / processed_count, 4) if processed_count else 0,
                "mean_f1": round(total_f1 / processed_count, 4) if processed_count else 0,
                "mean_accuracy": round(total_acc / processed_count, 4) if processed_count else 0,
                "mean_levenshtein": round(total_lev / processed_count, 4) if processed_count else 0,
                "latencia": compute_latency_stats(latencias),
                "total_docs": len(entries),
                "docs_processados": processed_count,
                "docs_com_divergencia": erros_count,
            },
            "metricas_por_campo": metricas_por_campo,
            "resultados_por_arquivo": resultados_por_arquivo,
        }

        report_name = (
            f"metrics_{doc_type.value}_{short_name}"
            f"_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        output_path = results_dir / report_name
        with open(output_path, "w", encoding="utf-8") as jf:
            json.dump(report, jf, indent=4, ensure_ascii=False)

        mg = report["metricas_gerais"]
        print(f"\n    +--- RESUMO: {doc_type.value.upper()} x {model.value} ---")
        print(f"    | Docs total: {mg['total_docs']}  |  Processados: {mg['docs_processados']}  |  Falhas: {mg['docs_com_divergencia']}")
        print(f"    | Accuracy:    {mg['mean_accuracy']:.4f}")
        lat = mg['latencia']
        print(f"    | Latencia:    mean={lat['mean']:.2f}s")
        print(f"    +-----------------------------------")


# ============================================================================
# MAPEAMENTO DOS MODOS DE CHAMADA 
# ============================================================================

# Deploy mode
_VERTEX_DEPLOY_MAP: list[tuple[LLMModel, str, str, str, bool]] = [
    (LLMModel.VERTEX_AI, "vertex_endpoint_id", "", "", True),
]

# Gemma multimodal
_VERTEX_GEMMA_MAP: list[tuple[LLMModel, str, str, str]] = [
    (LLMModel.GEMMA_3_27B, "gemma_3_27b_endpoint_id", "gemma_3_27b_location", "gemma_3_27b_dedicated_domain"),
    (LLMModel.GEMMA_3_12B, "gemma_3_12b_endpoint_id", "gemma_3_12b_location", "gemma_3_12b_dedicated_domain"),
    (LLMModel.QWEN3_VL, "qwen3_vl_endpoint_id", "qwen3_vl_location", "qwen3_vl_dedicated_domain"),
    (LLMModel.KIMI_K2_5, "kimi_k2_5_endpoint_id", "kimi_k2_5_location", "kimi_k2_5_dedicated_domain"),
]

# Ollama mode
_OLLAMA_MAP: list[tuple[LLMModel, str]] = [
    (LLMModel.OLLAMA_GEMMA_3_12B, MODEL_IDENTIFIERS[LLMModel.OLLAMA_GEMMA_3_12B]),
    (LLMModel.OLLAMA_GEMMA_3_27B, MODEL_IDENTIFIERS[LLMModel.OLLAMA_GEMMA_3_27B]),
    (LLMModel.OLLAMA_QWEN3_VL, MODEL_IDENTIFIERS[LLMModel.OLLAMA_QWEN3_VL]),
    (LLMModel.OLLAMA_QWEN3_VL_30B, MODEL_IDENTIFIERS[LLMModel.OLLAMA_QWEN3_VL_30B]),
]


def _sanitize_dedicated_domain(domain: str) -> str:
    cleaned = domain.strip()
    if not cleaned:
        return ""
    if "." not in cleaned or not (
        cleaned.endswith(".googleapis.com") or cleaned.endswith(".run.app")
    ):
        return ""
    return cleaned


def _build_vertex_clients() -> dict[LLMModel, LLMClient]:
    if not settings.vertex_project_id:
        return {}

    clients: dict[LLMModel, LLMClient] = {}

    for model, ep_attr, loc_attr, domain_attr, multimodal in _VERTEX_DEPLOY_MAP:
        endpoint_id = getattr(settings, ep_attr, "")
        if not endpoint_id:
            continue
        loc_override = getattr(settings, loc_attr, "")
        dedicated = getattr(settings, domain_attr, "")
        clients[model] = VertexAILLMClient(
            project_id=settings.vertex_project_id,
            location=loc_override or settings.vertex_location,
            endpoint_id=endpoint_id,
            model_name=MODEL_IDENTIFIERS[model],
            dedicated_domain=dedicated,
            multimodal=multimodal,
        )

    for model, ep_attr, loc_attr, domain_attr in _VERTEX_GEMMA_MAP:
        endpoint_id = getattr(settings, ep_attr, "")
        if not endpoint_id:
            continue
        loc_override = getattr(settings, loc_attr, "")
        dedicated = getattr(settings, domain_attr, "")
        dedicated = _sanitize_dedicated_domain(dedicated)
        clients[model] = VertexGemmaClient(
            project_id=settings.vertex_project_id,
            location=loc_override or settings.vertex_location,
            endpoint_id=endpoint_id,
            model_name=MODEL_IDENTIFIERS[model],
            dedicated_domain=dedicated,
        )

    # Qwen 3.5 External vLLM
    if settings.qwen_3_5_27b_url:
        clients[LLMModel.QWEN_3_5_27B] = VLLMClient(
            url=settings.qwen_3_5_27b_url,
            api_key=settings.qwen_3_5_27b_api_key,
            model_name=MODEL_IDENTIFIERS[LLMModel.QWEN_3_5_27B],
        )
    if settings.qwen_3_5_35b_url:
        clients[LLMModel.QWEN_3_5_35B] = VLLMClient(
            url=settings.qwen_3_5_35b_url,
            api_key=settings.qwen_3_5_35b_api_key,
            model_name=MODEL_IDENTIFIERS[LLMModel.QWEN_3_5_35B],
        )
    if settings.qwen_3_5_9b_url:
        clients[LLMModel.QWEN_3_5_9B] = VLLMClient(
            url=settings.qwen_3_5_9b_url,
            api_key=settings.qwen_3_5_9b_api_key,
            model_name=MODEL_IDENTIFIERS[LLMModel.QWEN_3_5_9B],
        )

    if settings.ollama_base_url:
        for model, model_id in _OLLAMA_MAP:
            clients[model] = OllamaClient(
                base_url=settings.ollama_base_url,
                api_key=settings.ollama_api_key,
                model=model_id,
                llm_model=model,
            )

    return clients


async def main():
    if not settings.gemini_api_key:
        print("[AVISO] DOC_EXTRACTOR_GEMINI_API_KEY não configurada.")

    model_factory = ModelFactory(settings)
    default_client = PydanticAILLMClient(model_factory, LLMModel.GEMINI_31_PRO)
    vertex_clients = _build_vertex_clients()

    llm_client = RoutingLLMClient(
        default_client=default_client,
        vertex_clients=vertex_clients,
        default_model=settings.default_llm_model,
    )
    factory = ExtractorFactory(llm_client)

    dataset_root = PROJECT_ROOT / "data"
    base_results_dir = PROJECT_ROOT / "results"
    base_results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now()

    print("=" * 60)
    print(f"  TESTE DE EXTRACAO - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Modelos: {[m.value for m in MODELS_CONFIG]}")
    print("=" * 60 + "\n")

    async def _run_model(model: LLMModel, doc_types: list[str]):
        short_name = _MODEL_SHORT_NAMES.get(model, model.value)
        print(f"\n{'#' * 60}")
        print(f"  MODELO: {model.value} ({short_name})")
        print(f"  Doc types: {doc_types}")
        print(f"{'#' * 60}\n")

        for doc_type_str in doc_types:
            try:
                doc_type = DocumentType(doc_type_str.lower())
            except ValueError:
                continue
            print(f"=== [{short_name}] {doc_type.value.upper()} ===")
            await _run_single_doc_type(doc_type, model, factory, dataset_root, base_results_dir, timestamp)

    # Separa modelos paralelos (vLLM, Vertex, Gemini) dos sequenciais (Ollama)
    parallel_models = {m: dt for m, dt in MODELS_CONFIG.items() if m not in OLLAMA_VISION_MODELS}
    sequential_models = {m: dt for m, dt in MODELS_CONFIG.items() if m in OLLAMA_VISION_MODELS}

    # Roda modelos paralelos + sequenciais ao mesmo tempo
    # Os sequenciais rodam um após o outro dentro da sua própria task
    async def _run_ollama_sequential():
        for model, doc_types in sequential_models.items():
            await _run_model(model, doc_types)

    tasks = [_run_model(m, dt) for m, dt in parallel_models.items()]
    if sequential_models:
        tasks.append(_run_ollama_sequential())

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
