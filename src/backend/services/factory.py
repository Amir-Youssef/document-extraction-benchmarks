from backend.core.exceptions import UnsupportedDocumentTypeError
from backend.domain.interfaces import DocumentExtractionStrategy, LLMClient
from backend.domain.enumx.document_type import DocumentType
from backend.services.strategies.certificate import CertificateExtractionStrategy
from backend.services.strategies.cnh import CNHExtractionStrategy
from backend.services.strategies.epi import EPIExtractionStrategy
from backend.services.strategies.ficha_registro import FichaRegistroExtractionStrategy
from backend.services.strategies.ltcat import LTCATExtractionStrategy
from backend.services.strategies.nr12 import NR12ExtractionStrategy
from backend.services.strategies.pgr import PGRExtractionStrategy
from backend.services.strategies.pcmso import PCMSOExtractionStrategy
from backend.services.strategies.afogados import AfogadosExtractionStrategy
from backend.services.strategies.aso import ASOExtractionStrategy
from backend.services.strategies.arrais import ArraisExtractionStrategy
from backend.services.strategies.nr35 import NR35ExtractionStrategy
from backend.services.strategies.marinheiro import MarinheiroExtractionStrategy
from backend.services.strategies.nr10 import NR10ExtractionStrategy
from backend.services.strategies.nr10sep import NR10SEPExtractionStrategy
from backend.services.strategies.seguro import SeguroExtractionStrategy
from backend.services.strategies.nr5 import NR5ExtractionStrategy
from backend.services.strategies.operador_treinamento import OperadorTreinamentoExtractionStrategy
from backend.services.strategies.nr11 import NR11ExtractionStrategy
from backend.services.strategies.nr33 import NR33ExtractionStrategy
from backend.services.strategies.escavadeira import EscavadeiraExtractionStrategy

class ExtractorFactory:
    """Maps DocumentType to its corresponding extraction strategy."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client
        self._types_registry: dict[DocumentType, type[DocumentExtractionStrategy]] = {
            DocumentType.CNH: CNHExtractionStrategy,
            DocumentType.CERTIFICATE: CertificateExtractionStrategy,
            DocumentType.EPI: EPIExtractionStrategy,
            DocumentType.FICHA_REGISTRO: FichaRegistroExtractionStrategy,
            DocumentType.LTCAT: LTCATExtractionStrategy,
            DocumentType.NR12: NR12ExtractionStrategy,
            DocumentType.PGR: PGRExtractionStrategy,
            DocumentType.PCMSO: PCMSOExtractionStrategy,
            DocumentType.AFOGADOS: AfogadosExtractionStrategy,
            DocumentType.ASO: ASOExtractionStrategy,
            DocumentType.ARRAIS: ArraisExtractionStrategy,
            DocumentType.NR35: NR35ExtractionStrategy,
            DocumentType.MARINHEIRO: MarinheiroExtractionStrategy,
            DocumentType.NR10: NR10ExtractionStrategy,
            DocumentType.NR10SEP: NR10SEPExtractionStrategy,
            DocumentType.SEGURO: SeguroExtractionStrategy,
            DocumentType.NR5: NR5ExtractionStrategy,
            DocumentType.OPERADOR_TREINAMENTO: OperadorTreinamentoExtractionStrategy,
            DocumentType.NR11: NR11ExtractionStrategy,
            DocumentType.NR33: NR33ExtractionStrategy,
            DocumentType.ESCAVADEIRA: EscavadeiraExtractionStrategy,
        }

    def get_strategy(self, document_type: DocumentType) -> DocumentExtractionStrategy:
        """Return the strategy instance for the given document type.

        Args:
            document_type: The type of document to extract.

        Raises:
            UnsupportedDocumentTypeError: If no strategy is registered for the type.
        """
        strategy_class = self._types_registry.get(document_type)
        if strategy_class is None:
            raise UnsupportedDocumentTypeError(
                f"No extraction strategy registered for document type: {document_type.value!r}"
            )
        return strategy_class(llm_client=self._llm_client)
