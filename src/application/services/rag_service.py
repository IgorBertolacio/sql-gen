from typing import Dict, Any, List
from application.services.maestro.extraction_manager import ExtractionManager
from application.services.maestro.embedding_manager import EmbeddingManager
from application.services.maestro.search_manager import SearchManager
from config.core.logging_config import setup_logging, get_logger

setup_logging(profile="api_server")
logger = get_logger(__name__)

class RAGService:

    @staticmethod
    def generate_sql_from_prompt(prompt_usuario: str) -> Dict[str, Any]:
        # Variáveis para controlar o loop
        max_iteracoes = 10
        iteracao_atual = 0
        tabelas_acumuladas = []
        tabelas_mantidas_acumuladas = []  # Lista para armazenar todas as tabelas mantidas com seus metadados
        resposta_final = None
        
        # Etapa 1: Recebe o prompt do usuario
        logger.info(f"\n[RAG SERVICE]\n Prompt recebido do usuário: '{prompt_usuario}'")
        
        # Loop principal - continua até obter código 2002 ou atingir o máximo de iterações
        while iteracao_atual <= max_iteracoes:
            logger.info(f"\n[RAG SERVICE]\n Iniciando iteração {iteracao_atual + 1} de {max_iteracoes + 1}")
            
            # Etapa 2: Passa o prompt para o ExtractionManager extrair entidades
            # Na primeira iteração, usa o prompt original. Nas seguintes, adiciona as tabelas solicitadas
            if iteracao_atual == 0:
                logger.info(f"\n[RAG SERVICE]\n Passando prompt para o ExtractionManager com modelo medio")
                resultado_extracao = ExtractionManager.extract_entities_from_prompt(prompt_usuario, nivel_modelo="medio")
                tabelas_extraidas = resultado_extracao.get("tabelas", [])
            else:
                # Nas iterações seguintes, usa as tabelas solicitadas da iteração anterior
                logger.info(f"\n[RAG SERVICE]\n Usando tabelas solicitadas da iteração anterior: {tabelas_solicitadas}")
                tabelas_extraidas = tabelas_solicitadas
            
            # Adiciona as tabelas extraídas às acumuladas (evitando duplicatas)
            for tabela in tabelas_extraidas:
                if tabela not in tabelas_acumuladas:
                    tabelas_acumuladas.append(tabela)
                logger.info(f"\n[RAG SERVICE] Tabelas mantidas acumuladas: {[t.get('table_name') for t in tabelas_mantidas_acumuladas]}")
                logger.info(f"\n[RAG SERVICE] Número de tabelas acumuladas: {len(tabelas_mantidas_acumuladas)}")

            # Verificar se todas as tabelas mantidas têm conteúdo
            for tabela in tabelas_mantidas_acumuladas:
                if not tabela.get("content"):
                    logger.warning(f"\n[RAG SERVICE] Tabela sem conteúdo: {tabela.get('table_name')}")

            # Etapa 3: Gera embeddings para as tabelas extraídas
            logger.info(f"\n[RAG SERVICE]\n Gerando embeddings para {len(tabelas_extraidas)} tabelas extraídas")
            resultado_embeddings = EmbeddingManager.generate_embeddings_for_tables(tabelas_extraidas)

            # Etapa 4: Busca tabelas similares usando os embeddings gerados
            logger.info(f"\n[RAG SERVICE]\n Buscando tabelas similares usando embeddings")
            embeddings_gerados = resultado_embeddings.get("embeddings")
            resultado_busca = SearchManager.find_similar_tables(
                query_embeddings=embeddings_gerados,
                table_names=tabelas_extraidas)

            # Etapa 5: Verificar se os dados encontrados são suficientes para responder à pergunta
            logger.info(f"\n[RAG SERVICE]\n Enviados dados para verificação")
            resultados_similares = resultado_busca.get("resultados", [])

            # Chamar o ExtractionManager para verificar se os dados são suficientes
            resultado_verificacao = ExtractionManager.verify_data_sufficiency(
                prompt_usuario=prompt_usuario,
                tabelas_similares=resultados_similares
            )

            # Processar o resultado da verificação
            codigo = resultado_verificacao.get('codigo')
            
            if codigo == '2002':
                logger.info(f"\n[RAG SERVICE] Dados suficientes para responder à pergunta.")
                
                # Adicionar todas as tabelas aos resultados mantidos
                for resultado in resultados_similares:
                    matches = resultado.get("matches", [])
                    for match in matches:
                        # Adiciona à lista de tabelas mantidas acumuladas
                        tabelas_mantidas_acumuladas.append({
                            "table_name": match.get("table_name", ""),
                            "similarity_percentage": match.get("similarity_percentage", 0),
                            "content": match.get("content", "")
                        })
                
                # Gerar resposta final com todas as tabelas mantidas acumuladas
                resposta_final = ExtractionManager.final_response(
                    prompt_usuario=prompt_usuario,
                    resultados_similares=tabelas_mantidas_acumuladas,
                    nivel_modelo="forte"
                )
                
                logger.info(f"\n[RAG SERVICE] Resposta final gerada com sucesso.")
                # Sai do loop quando obtém dados suficientes
                break
                
            elif codigo == '1001':
                tabelas_mantidas = resultado_verificacao.get('tabelas_mantidas', [])
                tabelas_solicitadas = resultado_verificacao.get('tabelas_solicitadas', [])
                motivo = resultado_verificacao.get('motivo', '')
                
                logger.info(f"\n[RAG SERVICE] Necessário buscar tabelas adicionais (iteração {iteracao_atual + 1}).")
                logger.info(f"\n[RAG SERVICE] Tabelas mantidas: {tabelas_mantidas}")
                logger.info(f"\n[RAG SERVICE] Tabelas solicitadas: {tabelas_solicitadas}")
                logger.info(f"\n[RAG SERVICE] Motivo: {motivo}")
                
                # Adicionar tabelas mantidas à lista acumulada
                from application.services.maestro.filter_tables import FilterTables
                tabelas_filtradas = FilterTables.filtrar_tabelas_mantidas(tabelas_mantidas, resultados_similares)
                
                # Adiciona as tabelas filtradas à lista acumulada
                for tabela in tabelas_filtradas:
                    # Verifica se a tabela já existe na lista acumulada
                    existe = False
                    for t in tabelas_mantidas_acumuladas:
                        if t.get("table_name") == tabela.get("table_name"):
                            existe = True
                            break
                    
                    # Se não existe, adiciona
                    if not existe:
                        tabelas_mantidas_acumuladas.append(tabela)
                
                logger.info(f"\n[RAG SERVICE] Tabelas mantidas acumuladas: {[t.get('table_name') for t in tabelas_mantidas_acumuladas]}")
                
                # Verifica se atingiu o máximo de iterações
                if iteracao_atual == max_iteracoes:
                    logger.warning(f"\n[RAG SERVICE] Atingido o número máximo de iterações ({max_iteracoes + 1}). Gerando resposta com os dados disponíveis.")
                    
                    # Gerar resposta final com os dados disponíveis, mesmo que incompletos
                    resposta_final = ExtractionManager.final_response(
                        prompt_usuario=prompt_usuario,
                        resultados_similares=tabelas_mantidas_acumuladas,
                        nivel_modelo="forte"
                    )
                    
                    logger.info(f"\n[RAG SERVICE] Resposta final gerada com dados parciais.")
                    break
            else:
                logger.warning(f"\n[RAG SERVICE] Erro na verificação: {resultado_verificacao.get('motivo')}")
                # Em caso de erro, tenta gerar uma resposta com os dados disponíveis
                resposta_final = ExtractionManager.final_response(
                    prompt_usuario=prompt_usuario,
                    resultados_similares=tabelas_mantidas_acumuladas if tabelas_mantidas_acumuladas else resultados_similares,
                    nivel_modelo="forte"
                )
                logger.info(f"\n[RAG SERVICE] Resposta final gerada com dados disponíveis após erro.")
                break
            
            # Incrementa o contador de iterações
            iteracao_atual += 1
        
        # Se chegou aqui sem resposta final (caso improvável), gera uma resposta de erro
        if resposta_final is None:
            resposta_final = "Não foi possível gerar uma resposta para a sua pergunta com os dados disponíveis."

        return {
            "sucesso": True,
            "sql_gerado_final": resposta_final,
            "resposta_texto": "Resposta gerada com sucesso.",
            "erro": None
        }