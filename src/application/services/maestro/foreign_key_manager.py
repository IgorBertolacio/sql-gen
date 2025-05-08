# src/application/services/maestro/foreign_key_manager.py
import re
from typing import Dict, List, Set, Tuple
from config.core.logging_config import get_logger

logger = get_logger(__name__)

class ForeignKeyManager:
    """
    Gerenciador para extrair tabelas relacionadas por chaves estrangeiras
    (tanto de saída quanto de entrada) a partir dos chunks de schema.
    """

    @staticmethod
    def _remove_schema_prefix(table_name_with_schema: str) -> str:
        """
        Remove o prefixo 'schema.' do nome da tabela.
        Exemplo: 'schema.tabela' -> 'tabela', 'tabela' -> 'tabela'
        """
        if '.' in table_name_with_schema:
            return table_name_with_schema.split('.', 1)[-1]
        return table_name_with_schema

    @staticmethod
    def extract_related_tables_from_chunks(
        retrieved_context_parts: Dict[str, str],
        initial_table_list: List[str]
    ) -> Dict[str, any]:
        """
        Extrai tabelas referenciadas por chaves estrangeiras (saída e entrada)
        nos chunks de contexto. Os nomes das tabelas são retornados sem o prefixo do schema.

        Args:
            retrieved_context_parts: Dicionário onde as chaves são nomes de tabelas
                                     (ex: 'el_cpe_ex.ct_empenho') e os valores são os
                                     conteúdos dos chunks (schemas).
            initial_table_list: Lista inicial de tabelas já conhecidas,
                                  podendo conter o prefixo do schema.

        Returns:
            Um dicionário com:
                "sucesso": True/False,
                "all_identified_tables": Lista de todas as tabelas (iniciais + FKs descobertas),
                                          sem duplicatas, sem prefixo de schema e ordenadas.
                "erro": Mensagem de erro (se sucesso=False).
        """
        all_identified_tables_set: Set[str] = {
            ForeignKeyManager._remove_schema_prefix(t) for t in initial_table_list
        }

        # Regex para encontrar 'schema.tabela' após um '>' (saída) OU '<' (entrada) e antes de um '('
        # Exemplo OUTGOING: FK:id_contrato>el_compras.cp_contrato(id)[DIR:OUTGOING] -> captura 'el_compras.cp_contrato'
        # Exemplo INCOMING: FK:id<el_compras.cp_contrato_item(id_contrato)[DIR:INCOMING] -> captura 'el_compras.cp_contrato_item'
        # O grupo (?:>|<) é um non-capturing group para OR entre > e <.
        # O grupo (\w[\w\.]*) captura o nome da tabela (permitindo letras, números, _ e .)
        fk_table_pattern = re.compile(r"(?:>|<)(\w[\w\.]*)\(")

        # Logger para as tabelas iniciais processadas
        processed_initial_list = [ForeignKeyManager._remove_schema_prefix(t) for t in initial_table_list]
        logger.info(f"Iniciando extração de tabelas referenciadas por FKs. Tabelas iniciais (processadas): {processed_initial_list}")

        for table_name_of_chunk_with_schema, chunk_content in retrieved_context_parts.items():
            processed_table_name_of_chunk = ForeignKeyManager._remove_schema_prefix(table_name_of_chunk_with_schema)
            all_identified_tables_set.add(processed_table_name_of_chunk) # Adiciona a tabela do chunk

            # Os chunks são strings no formato: schema;tabela;desc;col1;col2;PK:col;FK:def1;FK:def2;IDX:idx
            # Vamos dividir o chunk por ';' para analisar cada parte.
            parts = chunk_content.strip().split(';')

            for part in parts:
                part = part.strip()
                if not part.startswith("FK:"):
                    continue

                # 'part' é agora uma definição individual de FK, ex: "FK:id_tipo>el_cpe_base.ct_documento_tipo(id)[DIR:OUTGOING]"
                # ou "FK:id<el_cpe_ex.ct_liquidacao(id_documento)[DIR:INCOMING]"

                # Remove o prefixo "FK:"
                fk_definition_str = part[len("FK:"):]

                # Usamos o regex para encontrar a tabela referenciada/referenciadora
                match = fk_table_pattern.search(fk_definition_str)
                if match:
                    # O grupo 1 do regex captura o nome da tabela (com schema)
                    # ex: 'el_cpe_base.ct_documento_tipo' ou 'el_cpe_ex.ct_liquidacao'
                    related_table_with_schema = match.group(1)
                    processed_related_table_name = ForeignKeyManager._remove_schema_prefix(related_table_with_schema)

                    if processed_related_table_name not in all_identified_tables_set:
                        logger.info(
                            f"Nova tabela relacionada por FK descoberta: '{processed_related_table_name}' "
                            f"(original: '{related_table_with_schema}', a partir da FK '{fk_definition_str}' "
                            f"no chunk de '{processed_table_name_of_chunk}')"
                        )
                        all_identified_tables_set.add(processed_related_table_name)
                else:
                    logger.warning(
                        f"Não foi possível parsear a definição de FK: '{part}' "
                        f"no chunk de '{processed_table_name_of_chunk}' "
                        f"(original: {table_name_of_chunk_with_schema})"
                    )
            # Fim do loop de partes do chunk
        # Fim do loop de chunks

        final_table_list = sorted(list(all_identified_tables_set))
        logger.info(f"Extração de tabelas FK concluída. Lista final de tabelas identificadas ({len(final_table_list)}): {final_table_list}")

        return {
            "sucesso": True,
            "all_identified_tables": final_table_list
        }