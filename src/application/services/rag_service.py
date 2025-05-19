# src/application/services/rag_service.py

from typing import Dict, Any, List
from application.services.maestro.extraction_manager import ExtractionManager
from application.services.maestro.embedding_manager import EmbeddingManager
from infrastructure.vector_database.search_service import SearchService
from application.services.maestro.filter_tables import FilterTables
from config.core.logging_config import setup_logging, get_logger

setup_logging(profile="api_server")
logger = get_logger(__name__)

class RAGService:

    @staticmethod
    def generate_sql_from_prompt(prompt_usuario: str) -> Dict[str, Any]:
        max_iteracoes = 10
        iteracao_atual = 0
        tabelas_mantidas_acumuladas: List[Dict[str, Any]] = []
        resposta_final = None
        tabelas_a_buscar: List[str] = []

        logger.info(f"\n[RAG SERVICE] Prompt recebido: '{prompt_usuario}'")

        while iteracao_atual <= max_iteracoes:
            logger.info(f"\n[RAG SERVICE] Iteração {iteracao_atual + 1}/{max_iteracoes + 1}")

            tabelas_extraidas_nesta_iteracao: List[str]
            if iteracao_atual == 0:
                logger.info(f"\n[RAG SERVICE] Extraindo entidades do prompt inicial")
                resultado_extracao = ExtractionManager.extract_entities_from_prompt(prompt_usuario, nivel_modelo="medio")
                tabelas_extraidas_nesta_iteracao = resultado_extracao.get("tabelas", [])
            else:
                logger.info(f"\n[RAG SERVICE] Usando tabelas solicitadas da iteração anterior: {tabelas_a_buscar}")
                tabelas_extraidas_nesta_iteracao = tabelas_a_buscar

            resultados_busca_atual: List[Dict[str, Any]] = []
            if tabelas_extraidas_nesta_iteracao:
                logger.info(f"\n[RAG SERVICE] Gerando embeddings para: {tabelas_extraidas_nesta_iteracao}")
                resultado_embeddings = EmbeddingManager.generate_embeddings_for_tables(tabelas_extraidas_nesta_iteracao)
                embeddings_gerados = resultado_embeddings.get("embeddings")

                if embeddings_gerados is not None and embeddings_gerados.size > 0:
                    logger.info(f"\n[RAG SERVICE] Buscando tabelas similares")
                    resultados_busca_atual = SearchService.find_top_similar_tables(
                        query_embeddings=embeddings_gerados,
                        query_table_names=tabelas_extraidas_nesta_iteracao,
                        k=5 # Ajuste o k conforme necessário
                    )
                else:
                    logger.warning(f"\n[RAG SERVICE] Nenhum embedding gerado para {tabelas_extraidas_nesta_iteracao}. Pulando busca.")
            else:
                logger.info(f"\n[RAG SERVICE] Nenhuma tabela para buscar nesta iteração.")


            # Contexto para verificação: tabelas da busca atual + tabelas já mantidas
            # `verify_data_sufficiency` espera uma lista de resultados de busca,
            # então precisamos formatar `tabelas_mantidas_acumuladas` se quisermos incluí-las diretamente.
            # Por ora, `verify_data_sufficiency` parece analisar apenas a nova leva de tabelas (`resultados_busca_atual`).
            # Se a intenção é que a LLM analise *todo* o contexto acumulado,
            # `tabelas_para_verificacao` deve agregar `resultados_busca_atual` e `tabelas_mantidas_acumuladas`
            # em um formato que `verify_data_sufficiency` entenda.

            # Para simplificar, vamos assumir que `verify_data_sufficiency` analisa o contexto da busca atual
            # e `ExtractionManager.final_response` usa `tabelas_mantidas_acumuladas`.
            tabelas_para_verificacao = resultados_busca_atual

            logger.info(f"\n[RAG SERVICE] Verificando suficiência dos dados. Contexto para LLM (apenas busca atual): {len(tabelas_para_verificacao)} resultados.")
            resultado_verificacao = ExtractionManager.verify_data_sufficiency(
                prompt_usuario=prompt_usuario,
                tabelas_similares=tabelas_para_verificacao # Passa os resultados da busca mais recente
            )

            codigo_verificacao = resultado_verificacao.get('codigo')

            if codigo_verificacao == '2002':
                logger.info(f"\n[RAG SERVICE] Dados suficientes. Gerando resposta final.")
                # Adiciona os "matches" da última busca às tabelas mantidas, se houver
                for resultado_busca in resultados_busca_atual: # `resultados_busca_atual` é List[Dict]
                    for match in resultado_busca.get("matches", []):
                         # Evitar duplicatas em tabelas_mantidas_acumuladas
                        if not any(t.get("table_name") == match.get("table_name") for t in tabelas_mantidas_acumuladas):
                            tabelas_mantidas_acumuladas.append(match)

                resposta_final = ExtractionManager.final_response(
                    prompt_usuario=prompt_usuario,
                    resultados_similares=tabelas_mantidas_acumuladas, # Usa todas as tabelas acumuladas
                    nivel_modelo="forte"
                )
                logger.info(f"\n[RAG SERVICE] Resposta final gerada.")
                break

            elif codigo_verificacao == '1001':
                tabelas_mantidas_pela_llm = resultado_verificacao.get('tabelas_mantidas', [])
                tabelas_solicitadas_pela_llm = resultado_verificacao.get('tabelas_solicitadas', [])
                motivo = resultado_verificacao.get('motivo', '')

                logger.info(f"\n[RAG SERVICE] LLM solicitou mais tabelas. Mantidas: {tabelas_mantidas_pela_llm}, Solicitadas: {tabelas_solicitadas_pela_llm}. Motivo: {motivo}")

                # Filtra e adiciona as tabelas que a LLM decidiu manter DA BUSCA ATUAL
                tabelas_filtradas_da_busca_atual = FilterTables.filtrar_tabelas_mantidas(
                    tabelas_mantidas_pela_llm,
                    resultados_busca_atual # Filtra dos resultados da busca corrente
                )

                for tabela_filtrada in tabelas_filtradas_da_busca_atual:
                    if not any(t.get("table_name") == tabela_filtrada.get("table_name") for t in tabelas_mantidas_acumuladas):
                        tabelas_mantidas_acumuladas.append(tabela_filtrada)

                logger.info(f"\n[RAG SERVICE] Tabelas mantidas acumuladas: {[t.get('table_name') for t in tabelas_mantidas_acumuladas]}")
                tabelas_a_buscar = tabelas_solicitadas_pela_llm

                if not tabelas_a_buscar: # LLM pediu para manter, mas não solicitou novas. Evita loop infinito.
                    logger.warning("\n[RAG SERVICE] LLM não solicitou novas tabelas, mas não retornou 2002. Forçando resposta final.")
                    resposta_final = ExtractionManager.final_response(
                        prompt_usuario=prompt_usuario,
                        resultados_similares=tabelas_mantidas_acumuladas,
                        nivel_modelo="forte"
                    )
                    break

                if iteracao_atual == max_iteracoes:
                    logger.warning(f"\n[RAG SERVICE] Máximo de iterações atingido. Gerando resposta com dados disponíveis.")
                    resposta_final = ExtractionManager.final_response(
                        prompt_usuario=prompt_usuario,
                        resultados_similares=tabelas_mantidas_acumuladas,
                        nivel_modelo="forte"
                    )
                    break
            else: # Erro na verificação ou código desconhecido
                logger.error(f"\n[RAG SERVICE] Erro na verificação da LLM ou código desconhecido: {resultado_verificacao.get('motivo', 'Resposta inválida')}")
                resposta_final = ExtractionManager.final_response(
                    prompt_usuario=prompt_usuario,
                    resultados_similares=tabelas_mantidas_acumuladas, # Tenta com o que tem
                    nivel_modelo="forte"
                )
                logger.info(f"\n[RAG SERVICE] Resposta final gerada após erro na verificação.")
                break

            iteracao_atual += 1

        if resposta_final is None:
            logger.error("\n[RAG SERVICE] Nenhuma resposta final foi gerada após o loop. Isso não deveria acontecer.")
            # Fallback para uma resposta genérica de erro ou com o contexto que tiver
            if tabelas_mantidas_acumuladas:
                logger.info("\n[RAG SERVICE] Tentando gerar resposta final com tabelas acumuladas como último recurso.")
                resposta_final = ExtractionManager.final_response(
                    prompt_usuario=prompt_usuario,
                    resultados_similares=tabelas_mantidas_acumuladas,
                    nivel_modelo="forte"
                )
            else:
                resposta_final = "Não foi possível gerar uma resposta para a sua pergunta com as informações disponíveis após múltiplas tentativas."

        return {
            "sucesso": True, # O RAGService em si completou, a qualidade da resposta depende da LLM
            "sql_gerado_final": resposta_final, # Este campo deve conter a resposta final da LLM
            "resposta_texto": "Processamento RAG concluído.", # Mensagem genérica
            "erro": None
        }