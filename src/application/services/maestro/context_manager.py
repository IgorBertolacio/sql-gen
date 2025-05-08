# src/application/services/maestro/context_manager.py

from typing import Dict, Any, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Gerencia a etapa de recuperação de contexto do processo RAG.
    Responsável por extrair e organizar o conteúdo relevante das tabelas encontradas.
    """
    
    @staticmethod
    def extract_context_from_results(similar_tables_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extrai o contexto relevante dos resultados da busca vetorial.
        
        Args:
            similar_tables_result: Lista de resultados da busca vetorial.
            
        Returns:
            Um dicionário contendo o contexto extraído e informações relacionadas.
        """
        try:
            # Inicializa estruturas para armazenar o contexto
            retrieved_context_parts: Dict[str, str] = {}  # Usar dict para evitar duplicatas pelo nome qualificado
            unique_context_sources = set()  # Rastrear quais tabelas forneceram contexto
            
            # Verifica se há resultados para processar
            if not similar_tables_result:
                logger.info("Nenhum resultado de busca para extrair contexto.")
                return {
                    "sucesso": True,
                    "contexto_partes": {},
                    "fontes_contexto": set()
                }
            
            # Processa os resultados da busca
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
            
            # Retorna o contexto extraído
            return {
                "sucesso": True,
                "contexto_partes": retrieved_context_parts,
                "fontes_contexto": unique_context_sources
            }
            
        except Exception as e:
            logger.error(f"Erro durante a extração de contexto: {str(e)}")
            return {
                "sucesso": False,
                "erro": "Erro durante a extração de contexto",
                "detalhes": str(e),
                "contexto_partes": {},
                "fontes_contexto": set()
            }
    
    @staticmethod
    def format_context_for_prompt(context_parts: Dict[str, str]) -> str:
        """
        Formata o contexto extraído para inclusão no prompt final.
        
        Args:
            context_parts: Dicionário com partes do contexto (nome_tabela -> conteúdo).
            
        Returns:
            String formatada com o contexto para o prompt.
        """
        context_str = "Contexto do Banco de Dados:\n"
        
        if context_parts:
            for table_name, content in context_parts.items():
                context_str += f"--- Table: {table_name} ---\n"
                context_str += f"{content}\n"
                context_str += f"--- End Table: {table_name} ---\n\n"
        else:
            context_str += "Nenhuma informação de tabela relevante foi encontrada.\n\n"
            
        return context_str