.PHONY: setup demo rodar rodar-sem-ia estresse testes validar pacote limpar tudo

setup:
	python -m pip install -r requirements.txt

demo:              ## interface local em http://localhost:8501
	streamlit run demo.py --server.port 8501

rodar:            ## pipeline completo sobre data_pack/ -> out/
	python run.py

rodar-sem-ia:     ## só camadas determinísticas (não precisa de chave de API)
	python run.py --sem-ia

estresse:         ## data pack adversarial -> out_estresse/
	python run.py --sem-ia --dados data_pack_estresse --saida out_estresse

testes:
	python -m pytest -q

validar: testes rodar-sem-ia estresse

pacote:           ## gera dist/vantara-concilia-entrega.zip sem segredos/caches
	bash scripts/empacotar_entrega.sh

tudo: validar

limpar:
	@echo "Limpeza manual somente: as saídas oficiais fazem parte da entrega."
