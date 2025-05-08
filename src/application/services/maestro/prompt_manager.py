# src/application/services/maestro/prompt_manager.py

from typing import Dict, Any
# Removido Optional se não for mais necessário
# import logging # Use o logger já configurado globalmente, se for o caso
from config.core.logging_config import get_logger # Assumindo que você usa seu logging_config

from config.prompts.sql_instructions import SQLInstructions

# Substitua logging.getLogger por get_logger se você estiver usando seu setup_logging
# logger = logging.getLogger(__name__)
logger = get_logger(__name__) # Ou mantenha o seu se for diferente

class PromptManager:
    """
    Gerencia a etapa de construção do prompt final para o Assistente DBA.
    Responsável por combinar as diretrizes do assistente, contexto e prompt do usuário.
    """
    
    @staticmethod
    def build_sql_generation_prompt( # O nome pode ficar, ou mudar para algo como build_dba_assistant_prompt
        prompt_usuario: str,
        context_str: str,
        sql_dialect: str = "postgresql"
    ) -> Dict[str, Any]:
        """
        Constrói o prompt final para o Assistente DBA, que pode gerar SQL,
        responder perguntas, ou fornecer análises com base no contexto.
        
        Args:
            prompt_usuario: Prompt original do usuário.
            context_str: Contexto formatado com informações das tabelas (schemas, FKs, etc.).
            sql_dialect: Dialeto SQL a ser considerado pelo assistente (padrão: postgresql).
            
        Returns:
            Um dicionário contendo o prompt final e informações relacionadas.
        """
        try:
            logger.info(f"Construindo prompt final para o Assistente DBA (Dialeto: {sql_dialect})...")
            
            # Obter as diretrizes e persona completas do Assistente DBA
            # Este método agora engloba todas as instruções necessárias.
            dba_assistant_instructions = SQLInstructions.get_professional_dba_assistant_persona_and_guidelines(
                dialect=sql_dialect
            )
            
            # Monta o prompt final
            # A ordem é importante:
            # 1. Instruções/Persona do Assistente
            # 2. Contexto do Banco de Dados
            # 3. Pergunta do Usuário
            # 4. Espaço para a resposta do Assistente
            
            prompt_final = f"""
{dba_assistant_instructions}

**Contexto do Banco de Dados Fornecido:**
--- INÍCIO DO CONTEXTO DO BANCO DE DADOS ---
{context_str}
--- FIM DO CONTEXTO DO BANCO DE DADOS ---

**Solicitação do Usuário:**
{prompt_usuario}

**Sua Resposta (lembre-se de seguir TODAS as diretrizes da sua persona, incluindo a formatação para SQL ```sql ... ``` se for o caso, ou uma resposta em linguagem natural clara e útil):**
"""
            
            # Log do prompt final (cuidado com tamanho/sensibilidade)
            # Aumentei um pouco o log para ver mais das novas instruções, ajuste conforme necessário
            logger.debug(f"Prompt final para LLM (Assistente DBA):\n{prompt_final[:1500]}...") 
            
            return {
                "sucesso": True,
                "prompt_final": prompt_final.strip(), # .strip() para remover espaços em branco no início/fim
                "componentes": {
                    "instrucoes_assistente_dba": dba_assistant_instructions, # Agora é uma única string grande
                    "contexto": context_str,
                    "prompt_usuario": prompt_usuario,
                    "dialeto_solicitado": sql_dialect
                }
            }
            
        except Exception as e:
            logger.error(f"Erro durante a construção do prompt final: {str(e)}", exc_info=True) # Adicionado exc_info=True para stack trace
            return {
                "sucesso": False,
                "erro": "Erro durante a construção do prompt final",
                "detalhes": str(e),
                "prompt_final": "" # Retorna string vazia em caso de erro para evitar problemas downstream
            }