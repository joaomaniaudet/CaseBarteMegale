# Manifesto da entrega

## Conteúdo incluído

| Item | Local | Finalidade |
|---|---|---|
| Código executável | `run.py`, `demo.py`, `src/` | pipeline CLI e interface Streamlit |
| Configuração | `config/regras.yaml`, `.env.example` | políticas, thresholds e template sem segredos |
| Dependências | `requirements.txt`, `Makefile` | instalação e comandos reproduzíveis |
| Testes | `tests/` | golden set, limites, IA e contas a pagar |
| Data pack principal | `data_pack/` | arquivos originais de julho |
| Data pack adversarial | `data_pack_estresse/` | casos para provocar os limites do motor |
| Saídas geradas | `out/`, `out_estresse/` | CSVs, métricas JSON e relatório HTML |
| Fluxos e operação | `FLUXOS.md`, `ROTEIRO_DEMO.md`, `MOMENTOS.md` | visão funcional, técnica e roteiro de demonstração |
| Materiais executivos | `ppt/`, `MENSAGEM_CTO.md` | apresentações e mensagem de alinhamento |
| Contexto de construção | `prompts/` | registros disponíveis das sessões de trabalho |

## Conteúdo intencionalmente excluído do ZIP

- `.env`: pode conter chaves locais e nunca deve ser compartilhado;
- `.venv/`: ambiente Python local, grande e específico da máquina;
- `node_modules/`: dependências recompiláveis do PowerPoint;
- caches Python, pytest e IA;
- `out_upload/`, `out_debug/` e `out_demo/`: execuções temporárias da interface;
- arquivos do sistema operacional e logs locais.

## Como verificar

```bash
python run.py --sem-ia
python -m pytest -q
python run.py --sem-ia --dados data_pack_estresse --saida out_estresse
```

O pipeline deve terminar com as invariantes aritméticas aprovadas. Os testes
devem apresentar `47 passed` na versão atual. Compare os arquivos regenerados
com as pastas de saída incluídas.

## Plataforma e credenciais

A solução não depende de plataforma online. O Streamlit roda em localhost.
Também não existe conta compartilhada na entrega. Para testar a camada opcional
de IA, o avaliador copia `.env.example` para `.env` e adiciona a própria chave.
O modo oficial `--sem-ia` funciona sem qualquer chave.
