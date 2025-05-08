# src/interfaces/api/llm_controller.py

"""
Define e inicia a API Flask para geração de SQL via RAG.
"""

from flask import Flask, request, jsonify
# Ajuste os caminhos de importação se necessário, baseado em como você roda o run_api.py
# Se run_api.py está na raiz e chama 'from .llm_controller', então os imports dentro
# de llm_controller devem ser relativos à raiz do projeto 'src'.
from config.core.logging_config import setup_logging, get_logger # Caminho relativo a 'src'
from application.services.rag_service import RAGService # Caminho relativo a 'src'
from flask_cors import CORS
from flask import send_from_directory
import os

# Inicializa Logs (considerar fazer isso apenas uma vez na inicialização do app, não no import)
# setup_logging(profile="api_server") # Mover para dentro de iniciar_servidor ou if __name__ == "__main__"
logger = get_logger(__name__)

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir requisições do frontend

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend/build', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend/build', path)

@app.route('/sql-gen', methods=['POST']) 
def processar_rag_sql_gen():
    logger.info("\n[LLM CONTROLLER] Recebida requisição em /sql-gen")
    try:
        dados = request.json
        if not dados or 'prompt' not in dados:
            logger.warning("\n[LLM CONTROLLER] Requisição inválida: campo 'prompt' ausente.")
            return jsonify({"erro": "O campo 'prompt' é obrigatório"}), 400

        prompt = dados['prompt']
        logger.info(f"\n[LLM CONTROLLER] Processando prompt: '{prompt[:100]}...'")
        
        rag_service_result = RAGService.generate_sql_from_prompt(prompt)

        if rag_service_result.get("sucesso"):
            logger.info("\n[LLM CONTROLLER] Processamento RAG concluído com sucesso. Retornando resultado do RAGService para o frontend.")
            # Envia o payload completo do RAGService que já contém 'sql_gerado_final' formatado e 'sucesso', etc.
            return jsonify(rag_service_result), 200
        else:
            error_msg = rag_service_result.get("erro", "Erro desconhecido no processamento RAG.")
            logger.error(f"\n[LLM CONTROLLER] Erro retornado pelo RAGService: {error_msg}")
            logger.debug(f"\n[LLM CONTROLLER] Logs intermediários do RAGService em falha: {rag_service_result.get('logs_intermediarios')}")
            # Você pode enviar o rag_service_result mesmo em caso de falha,
            # pois ele contém 'sucesso: false' e 'erro'.
            # Ou construir um JSON de erro mais simples se preferir.
            # Por consistência, enviar rag_service_result é bom:
            return jsonify(rag_service_result), 500 # O status HTTP indica o erro

    except Exception as e:
        logger.critical(f"\n[LLM CONTROLLER] Erro inesperado no endpoint /sql-gen: {str(e)}", exc_info=True)
        return jsonify({"sucesso": False, "erro": f"Erro interno grave no servidor."}), 500

def iniciar_servidor(host='0.0.0.0', porta=5000, modo_debug=False):
    """
    Inicia o servidor Flask.
    """
    # Configurar o logging aqui, uma vez na inicialização, é melhor
    setup_logging(profile="api_server") 
    logger.info(f"\n[LLM CONTROLLER] Iniciando servidor Flask em {host}:{porta} (Debug: {modo_debug})")
    app.run(host=host, port=porta, debug=modo_debug)

# O bloco if __name__ == "__main__": aqui pode ser redundante
# se você sempre inicia pelo run_api.py. Removê-lo pode evitar confusão.
# Mas se você às vezes roda llm_controller.py diretamente, mantenha-o.
# if __name__ == "__main__":
#     porta = int(os.environ.get("PORT", 5000))
#     logger.info(f"Script llm_controller.py iniciando servidor na porta {porta}")
#     iniciar_servidor(porta=porta, modo_debug=True)