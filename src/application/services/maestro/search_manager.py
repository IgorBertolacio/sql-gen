from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from typing import Dict, Any, List, Optional


class SearchManager:
    @staticmethod
    def find_table_by_name(table_name: str) -> Dict[str, Any]:
        client = QdrantClient(
            url="https://01ed3958-ad74-4fae-980d-a437657dd61e.us-west-1-0.aws.cloud.qdrant.io",
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.XP5xOdP_WF65RzTaVkcc-cFjq1drD7oX1yi30Q8gzUk"
        )

        filtro = Filter(
            must=[
                FieldCondition(
                    key="name",
                    match=MatchValue(value=table_name)
                )
            ]
        )

        resposta, _ = client.scroll(
            collection_name="sql_metadados",
            scroll_filter=filtro,
            limit=5,
            with_payload=True
        )

        resultados = []
        for ponto in resposta:
            resultados.append({
                "id": ponto.id,
                "payload": ponto.payload
            })

        return {
            "sucesso": True,
            "resultados": resultados
        }
