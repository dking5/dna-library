from app.schemas import Gene
from datetime import datetime

def test_gene_response_computed_fields():
    raw_data = {
        "id": 101,
        "label": "Test_Gene_01",
        "sequence": "ATGC",
        "gc_content": 50.0,
        "description": "Sample gene",
        "created_at": datetime.now()
    }
    response = Gene(**raw_data)

    response_json = response.model_dump()

    assert "reverse_complement" in response_json
    assert response_json["reverse_complement"] == "TACG"
    assert response.id == 101