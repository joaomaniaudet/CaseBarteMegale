"""
Adapters de ingestão.

Regra da camada: consumir o arquivo COMO ELE VEM. Nenhuma limpeza manual
antes, nenhum "abre no Excel e salva como UTF-8". Se o arquivo estiver
quebrado, o adapter registra um aviso e segue — porque em produção o pipeline
não pode parar às 6h da manhã por causa de uma linha torta.

Adicionar a próxima conta = escrever um adapter novo aqui. O motor não muda.
"""

from .protheus import IngestorProtheus
from .omie import IngestorOmie
from .banco_itau import IngestorExtratoItau
from .inbox_ap import IngestorInboxAP

__all__ = [
    "IngestorProtheus",
    "IngestorOmie",
    "IngestorExtratoItau",
    "IngestorInboxAP",
]
