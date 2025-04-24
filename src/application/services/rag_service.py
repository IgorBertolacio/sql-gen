# src/application/services/rag_service.py

from typing import Dict, Any, Optional, List, Set
import numpy as np
import logging 

from src.infrastructure.config.prompts.base_instructions import BaseInstructions
from src.infrastructure.config.prompts.sql_instructions import SQLInstructions
from src.infrastructure.external_services.llm_service import LLMService
from src.infrastructure.external_services.embedding_service import EmbeddingService
from src.infrastructure.config.api.api_config import GeminiConfig
from src.application.utils.llm_response_parser import parse_llm_structured_response, extract_tables
from src.application.services.search_service import SearchService

logger = logging.getLogger(__name__)

class RAGService:
    """
    Serviço que orquestra o fluxo de execução do RAG.
    Responsável por controlar toda a arquitetura da RAG para gerar consultas SQL.
    """
    # Define o dialeto SQL (pode vir da requisição ou config)
    SQL_DIALECT = "postgresql" # Exemplo - pode ser dinâmico

    @staticmethod
    def generate_sql_from_prompt(prompt_usuario: str) -> Dict[str, Any]:
        """
        Processa o prompt do usuário:
        1. Extrai entidades (tabelas, colunas) do prompt usando LLM.
        2. Gera embeddings para as tabelas extraídas.
        3. Busca tabelas similares no índice vetorial.
        4. Recupera o conteúdo (schema/descrição) das tabelas encontradas.
        5. Constrói um prompt final com instruções SQL, contexto e prompt original.
        6. Chama o LLM para gerar a consulta SQL final.
        7. Retorna a consulta SQL gerada e informações intermediárias.

        Args:
            prompt_usuario: O prompt fornecido pelo usuário.

        Returns:
            Um dicionário contendo a consulta SQL gerada, o contexto usado,
            e outras informações, ou um dicionário de erro.
        """
        logger.info(f"RAGService: Iniciando processamento para o prompt: '{prompt_usuario[:100]}...'")
        try:
            # --- 1. Inicialização e Extração Inicial ---
            GeminiConfig.initialize()
            logger.debug("GeminiConfig inicializado.")

            instrucoes_extracao = BaseInstructions.get_stract_infos_instruction()
            prompt_extracao = f"{instrucoes_extracao}\n\nPrompt do usuário:\n{prompt_usuario}"

            logger.info("Enviando prompt inicial para extração de entidades...")
            resposta_extracao_bruta = LLMService.get_api_response(prompt_extracao)
            texto_resposta_extracao = LLMService.get_response_text(resposta_extracao_bruta)
            logger.debug(f"Resposta LLM (extração): {texto_resposta_extracao}")

            try:
                # Usar a função específica para maior clareza e robustez
                extracted_tables_list = extract_tables(texto_resposta_extracao)
                # Poderíamos extrair schemas e colunas também se necessário para a lógica futura
                # parsed_elements = parse_llm_structured_response(texto_resposta_extracao)
                # extracted_schemas_list = parsed_elements.get('schemas', [])
                # extracted_columns_list = parsed_elements.get('colunas', [])
                logger.info(f"Tabelas extraídas do prompt: {extracted_tables_list}")
            except ValueError as e_parse:
                logger.error(f"Falha ao parsear resposta da LLM para extração: {e_parse}")
                return {"erro": "Falha ao interpretar a resposta inicial da LLM.", "detalhes": str(e_parse)}


            # --- 2. Geração de Embeddings (se houver tabelas) ---
            query_embeddings = None
            if extracted_tables_list:
                logger.info(f"Gerando embeddings para {len(extracted_tables_list)} tabelas extraídas...")
                embedding_result_array = EmbeddingService.embed_texts(extracted_tables_list)

                if not isinstance(embedding_result_array, np.ndarray) or embedding_result_array.size == 0:
                    logger.warning(f"Falha ao gerar embeddings para as tabelas: {extracted_tables_list}. Continuando sem busca vetorial.")
                    # Podemos decidir continuar sem a busca ou retornar erro.
                    # Por enquanto, vamos continuar, mas a busca não retornará nada.
                    similar_tables_result = [] # Define como vazio para evitar erro posterior
                else:
                     query_embeddings = embedding_result_array
                     logger.info(f"Embeddings gerados com sucesso: shape {query_embeddings.shape}")

            else:
                logger.info("Nenhuma tabela extraída do prompt inicial. Pulando embedding e busca vetorial.")
                similar_tables_result = [] # Define como vazio

            # --- 3. Busca Vetorial (se embeddings foram gerados) ---
            if query_embeddings is not None:
                logger.info(f"Buscando tabelas similares no índice vetorial para {len(extracted_tables_list)} tabelas...")
                similar_tables_result = SearchService.find_top_similar_tables(
                    query_embeddings=query_embeddings,
                    query_table_names=extracted_tables_list,
                    k=5
                )
                logger.info(f"Busca vetorial concluída. {len(similar_tables_result)} resultados obtidos.")
                # Log detalhado dos resultados da busca (opcional, pode ser verboso)
                # logger.debug(f"Resultados da busca: {similar_tables_result}")


            # --- 4. Recuperação de Contexto (Chunks) ---
            retrieved_context_parts: Dict[str, str] = {} # Usar dict para evitar duplicatas pelo nome qualificado
            unique_context_sources = set() # Rastrear quais tabelas forneceram contexto

            if similar_tables_result: # Verifica se a busca retornou algo
                logger.info("Coletando conteúdo (chunks) das tabelas encontradas...")
                for result_item in similar_tables_result:
                    query_table = result_item.get("query_table", "unknown_query")
                    matches = result_item.get("matches", [])
                    if not matches:
                        logger.debug(f"Nenhuma correspondência encontrada para a tabela de consulta '{query_table}'.")
                        continue

                    # Pega o melhor match (primeiro da lista, já que SearchService deve ordenar)
                    best_match = matches[0]
                    table_name = best_match.get("table_name")
                    content = best_match.get("content")
                    similarity = best_match.get("similarity_percentage")

                    if table_name and content:
                        # Adiciona ao contexto se ainda não tivermos este table_name
                        if table_name not in retrieved_context_parts:
                             logger.info(f"Adicionando contexto para '{table_name}' (Similaridade: {similarity}%)")
                             retrieved_context_parts[table_name] = content
                             unique_context_sources.add(f"{table_name} (sim: {similarity}%)")

                        else:
                             logger.debug(f"Contexto para '{table_name}' já adicionado. Pulando duplicata.")
                    else:
                        logger.warning(f"Melhor correspondência para '{query_table}' ('{table_name}') está sem nome ou conteúdo.")


            # --- 5. Construção do Prompt Final para Geração SQL ---
            logger.info("Construindo prompt final para geração de SQL...")

            # Instruções Base de SQL
            sql_instructions = SQLInstructions.get_sql_generation_instruction()
            # Instruções Específicas do Dialeto
            dialect_instructions = SQLInstructions.get_sql_dialect_instruction(RAGService.SQL_DIALECT)

            # Formata o Contexto Recuperado
            context_str = "Contexto do Banco de Dados:\n"
            if retrieved_context_parts:
                for table_name, content in retrieved_context_parts.items():
                    context_str += f"--- Table: {table_name} ---\n"
                    context_str += f"{content}\n"
                    context_str += f"--- End Table: {table_name} ---\n\n"
            else:
                context_str += "Nenhuma informação de tabela relevante foi encontrada.\n\n"

            # Combina tudo
            prompt_final_sql = f"""
            {sql_instructions}

            {dialect_instructions}

            {context_str}
            ---
            Prompt Original do Usuário:
            {prompt_usuario}
            ---

            Com base nas instruções acima, no contexto fornecido e no prompt do usuário, gere APENAS a consulta SQL ({RAGService.SQL_DIALECT}) solicitada.
            Não adicione explicações extras antes ou depois do código SQL.
            """
            # Log do prompt final (cuidado com tamanho/sensibilidade)
            logger.debug(f"Prompt final para LLM (SQL Gen):\n{prompt_final_sql[:500]}...") # Log truncado

            # --- 6. Chamada Final ao LLM para Geração de SQL ---
            logger.info("Enviando prompt final para LLM para gerar SQL...")
            # Usamos processar_prompt para obter também metadados de uso, se quisermos
            # Ou podemos usar get_api_response e get_response_text se só precisarmos do SQL
            resposta_sql_completa = LLMService.processar_prompt(prompt_final_sql, modelo='gemini-2.0-flash') # Ou outro modelo adequado
            # resposta_sql_api = LLMService.get_api_response(prompt_final_sql)
            # generated_sql = LLMService.get_response_text(resposta_sql_api).strip()
            # Limpeza básica da resposta SQL (remover ```sql e ``` se presentes)
            generated_sql = resposta_sql_completa.get("resposta", "").strip()
            if generated_sql.startswith("```sql"):
                generated_sql = generated_sql[len("```sql"):].strip()
            if generated_sql.endswith("```"):
                generated_sql = generated_sql[:-len("```")].strip()

            logger.info(f"SQL gerado pela LLM:\n{generated_sql}")

            # --- 7. Montagem do Resultado Final ---
            final_result = {
                "prompt_usuario": prompt_usuario,
                "dialeto_sql": RAGService.SQL_DIALECT,
                "tabelas_extraidas_prompt": extracted_tables_list,
                "busca_vetorial_resultados": similar_tables_result, # Inclui a similaridade e o conteúdo usado
                "contexto_utilizado_llm": context_str, # O contexto formatado enviado
                "tabelas_contexto_fonte": list(unique_context_sources), # Lista das tabelas que forneceram contexto
                "prompt_final_llm": prompt_final_sql, # O prompt completo enviado (para depuração)
                "sql_gerado": generated_sql,
                "uso_llm_sql_gen": resposta_sql_completa.get("uso", {}), # Dados de uso da chamada final
                # Poderia adicionar uso da primeira chamada LLM também
            }
            logger.info("Processamento RAG concluído com sucesso.")
            return final_result

        except Exception as e:
            import traceback
            logger.critical(f"Erro crítico no RAGService.generate_sql_from_prompt: {e}", exc_info=True)
            # traceback.print_exc() # logger inclui exc_info=True
            return {
                "erro": f"Falha interna no processamento RAG: {str(e)}",
                "detalhes": "Verifique os logs do servidor para mais informações.",
                "prompt_usuario": prompt_usuario # Inclui o prompt original no erro
            }