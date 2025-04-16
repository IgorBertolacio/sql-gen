from typing import Dict, Any, Optional
import numpy as np
from src.infrastructure.config.prompts.base_instructions import BaseInstructions
from src.infrastructure.external_services.llm_service import LLMService
from src.infrastructure.external_services.embedding_service import EmbeddingService
from src.infrastructure.config.api.api_config import GeminiConfig
from src.application.utils.llm_response_parser import extract_tables
from src.application.services.search_service import SearchService
class RAGService:
    """
    Serviço que orquestra o fluxo de execução do RAG.
    Responsável por controlar toda a arquitetura da RAG para optimizar consultas SQL
    """
    @staticmethod
    def extrair_estrutura_sql(prompt_usuario: str) -> Dict[str, Any]:
        """
        Processa o prompt do usuário: obtém resposta do LLM, cria embedding,
        busca tabelas similares e retorna a estrutura.

        Args:
            prompt_usuario: O prompt fornecido pelo usuário.

        Returns:
            Um dicionário contendo as tabelas extraídas, seus embeddings,
            e as tabelas similares encontradas, ou um dicionário de erro.
        """
        try:
            GeminiConfig.initialize()

            instrucoes_extracao = BaseInstructions.get_stract_infos_instruction()
            prompt_completo = f"{instrucoes_extracao}\n\nPrompt do usuário:\n{prompt_usuario}"

            # 3. Envia prompt com instrucao 6. Retorna a resposta bruta
            resposta_api_bruta = LLMService.get_api_response(prompt_completo)

            # 7. Envia resposta bruta 8. Retorna a resposta refinada
            texto_resposta_llm = LLMService.get_response_text(resposta_api_bruta)

            # 9. Envia prompt refinado 10. Retorna lista tabelas
            extracted_tables_list = extract_tables(texto_resposta_llm) # Ex: ['cliente', 'pedido']
            if not extracted_tables_list:
                 # Handle case where no tables were extracted if necessary
                 # For now, assume it might return an empty list
                 return {
                     "prompt": prompt_usuario,
                     "extracted_tables": [],
                     "similar_tables": [],
                     "message": "Nenhuma tabela extraída do prompt do usuário."
                 }


            # 11. Envia lista tabelas 12. Retorna o array NumPy de embeddings NORMALIZADOS
            # (Corrigido: Não assume mais um dicionário como retorno)
            embedding_result_array = EmbeddingService.embed_texts(extracted_tables_list) # Assume que retorna SÓ o array np

            # Verifica se o retorno é válido antes de prosseguir
            # AGORA 'np' ESTÁ DEFINIDO DEVIDO AO IMPORT ACIMA
            if not isinstance(embedding_result_array, np.ndarray) or embedding_result_array.size == 0:
                 print(f"RAGService WARNING: EmbeddingService.embed_texts não retornou um array numpy válido para {extracted_tables_list}. Retornando erro.")
                 # Ou retorne um resultado indicando falha no embedding
                 return {
                     "prompt": prompt_usuario,
                     "extracted_tables": extracted_tables_list,
                     "similar_tables": [],
                     "message": f"Falha ao gerar embeddings para as tabelas: {extracted_tables_list}"
                 }


            # Atribui o array retornado diretamente
            query_embeddings = embedding_result_array

            # Os nomes das tabelas são os mesmos que foram enviados para o embedding
            query_table_names = extracted_tables_list

            # --- START: Step 13 & 14 ---
            # 13. Envia os Vetores e nomes originais para comparação
            # 14. Retorna lista de dicionários com top 3 nomes de tabelas mais próximas e %
            print(f"RAGService: Enviando {query_embeddings.shape[0]} embeddings e {len(query_table_names)} nomes para SearchService.") # Log para depuração
            similar_tables_result = SearchService.find_top_similar_tables(
                query_embeddings=query_embeddings,
                query_table_names=query_table_names,
                k=3 # Find top 3
            )
            # --- END: Step 13 & 14 ---

            # Prepare the final result
            final_result = {
                "prompt": prompt_usuario,
                "extracted_tables": query_table_names,
                # "embeddings_for_extracted_tables": query_embeddings.tolist(), # Optional: Convert to list if needed for JSON
                "similar_tables_found": similar_tables_result
            }
            return final_result

        except Exception as e:
            import traceback
            print(f"Erro crítico no RAGService.extrair_estrutura_sql: {e}")
            traceback.print_exc()
            return {
                "erro": f"Falha interna no processamento RAG: {str(e)}",
                "detalhes": "Verifique os logs do servidor para mais informações."
            }