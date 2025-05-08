from typing import Dict, Any, List
from config.prompts.base_instructions import BaseInstructions
from infrastructure.external_services.llm_service import LLMService
from shared.utils.llm_response_parser import parse_llm_structured_response
from config.core.logging_config import get_logger

logger = get_logger(__name__)

class ExtractionManager:
    
    @staticmethod
    def extract_entities_from_prompt(prompt_usuario: str, nivel_modelo: str = "fraco") -> Dict[str, Any]:
        instrucoes_extracao = BaseInstructions.get_stract_infos_instruction()
        prompt_completo = f"{instrucoes_extracao}\n\nPrompt do usuário:\n{prompt_usuario}"

        # Passando o nível do modelo para o LLMService
        resposta_texto = LLMService.processar_prompt(prompt_completo, nivel_modelo=nivel_modelo)
        
        parsed = parse_llm_structured_response(resposta_texto)
        logger.info(f"\n[Extraction Manager] Entidades extraídas do prompt:\n Schemas: {parsed.get('schemas', [])}\n Tabelas: {parsed.get('tabelas', [])}\n Colunas: {parsed.get('colunas', [])}")
        
        return {
            "schemas": parsed.get("schemas", []),
            "tabelas": parsed.get("tabelas", []),
            "colunas": parsed.get("colunas", [])
        }

    @staticmethod
    def verify_data_sufficiency(prompt_usuario: str, tabelas_similares: List[Dict[str, Any]], nivel_modelo: str = "medio") -> Dict[str, Any]:
        """
        Verifica se os dados encontrados são suficientes para responder à pergunta do usuário.
        
        Args:
            prompt_usuario: O prompt original do usuário.
            tabelas_similares: Lista de dicionários com as tabelas similares encontradas.
            nivel_modelo: Nível do modelo LLM a ser usado (padrão: medio).
            
        Returns:
            Dict: Dicionário com o código de retorno, tabelas mantidas, tabelas solicitadas e motivo.
        """
        # Formatar os dados das tabelas encontradas para enviar ao LLM
        chunks_tabelas = []
        for resultado in tabelas_similares:
            matches = resultado.get("matches", [])
            
            for match in matches:
                table_name = match.get("table_name", "")
                similarity = match.get("similarity_percentage", 0)
                content = match.get("content", "")
                
                # Adiciona informações formatadas sobre a tabela
                chunks_tabelas.append(f"Tabela: {table_name} (Similaridade: {similarity:.2f}%)\nConteúdo: {content}\n")
        
        # Obter o prompt de verificação de colunas
        instrucao_verificacao = BaseInstructions.get_verification_columns()
        
        # Montar o prompt completo para o LLM
        prompt_verificacao = f"""
            {instrucao_verificacao}

            Prompt original do usuário:
            {prompt_usuario}

            Chunks de tabelas encontradas:
            {''.join(chunks_tabelas)}
            """
        
        # Enviar para o LLM com o modelo especificado
        logger.info(f"\n[Extraction Manager] Verificando se os dados encontrados são suficientes para responder à pergunta")
        resposta_verificacao = LLMService.processar_prompt(prompt_verificacao, nivel_modelo=nivel_modelo)
        
        # Logar a resposta da verificação
        logger.info(f"\n[Extraction Manager] Resposta da verificação: {resposta_verificacao}")
        
        # Parsear a resposta usando a nova função
        from shared.utils.llm_response_parser import parse_verification_response
        resultado_verificacao = parse_verification_response(resposta_verificacao)
        
        return resultado_verificacao

    @staticmethod
    def final_response(prompt_usuario: str, resultados_similares: List[Dict[str, Any]], nivel_modelo: str = "extremo") -> str:
        """
        Gera a resposta final para o usuário com base nos resultados similares encontrados.
        
        Args:
            prompt_usuario: O prompt original do usuário.
            resultados_similares: Lista de dicionários com as tabelas similares encontradas.
            nivel_modelo: Nível do modelo LLM a ser usado (padrão: forte).
            
        Returns:
            str: Resposta final para o usuário.
        """
        # Formatar os dados das tabelas encontradas para enviar ao LLM
        chunks_tabelas = []
        # Verifica se os resultados têm a estrutura esperada
        if resultados_similares and isinstance(resultados_similares[0], dict):
            # Verifica se tem o atributo "matches" (estrutura do SearchManager)
            if "matches" in resultados_similares[0]:
                # Formato vindo do SearchManager
                for resultado in resultados_similares:
                    matches = resultado.get("matches", [])
                    for match in matches:
                        table_name = match.get("table_name", "")
                        similarity = match.get("similarity_percentage", 0)
                        content = match.get("content", "")
                        chunks_tabelas.append(f"Tabela: {table_name} (Similaridade: {similarity:.2f}%)\nConteúdo: {content}\n")
            else:
                # Formato da lista acumulada (já direto com table_name, similarity_percentage, content)
                for item in resultados_similares:
                    table_name = item.get("table_name", "")
                    similarity = item.get("similarity_percentage", 0)
                    content = item.get("content", "")
                    chunks_tabelas.append(f"Tabela: {table_name} (Similaridade: {similarity:.2f}%)\nConteúdo: {content}\n")

        for resultado in resultados_similares:
            matches = resultado.get("matches", [])
            
            for match in matches:
                table_name = match.get("table_name", "")
                similarity = match.get("similarity_percentage", 0)
                content = match.get("content", "")
                
                # Adiciona informações formatadas sobre a tabela
                chunks_tabelas.append(f"Tabela: {table_name} (Similaridade: {similarity:.2f}%)\nConteúdo: {content}\n")
        
        # Obter o prompt de resposta final
        instrucao_resposta = BaseInstructions.get_resposta_final()
        
        # Montar o prompt completo para o LLM
        prompt_resposta = f"""
            {instrucao_resposta}

            Prompt original do usuário:
            {prompt_usuario}

            Chunks de tabelas disponíveis:
            {''.join(chunks_tabelas)}
            """
        
        # Enviar para o LLM com o modelo especificado
        logger.info(f"\n[Extraction Manager] Gerando resposta final com modelo {nivel_modelo}")
        resposta_final = LLMService.processar_prompt(prompt_resposta, nivel_modelo=nivel_modelo)
        
        # Logar a resposta final (resumida para não poluir o log)
        resposta_resumida = resposta_final[:100] + "..." if len(resposta_final) > 100 else resposta_final
        logger.info(f"\n[Extraction Manager] Resposta final gerada: {resposta_resumida}")
        
        return resposta_final
    