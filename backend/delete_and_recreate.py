# delete_and_recreate.py
import os
from qdrant_client import QdrantClient
from recipe_rag_pipeline import reset_qdrant, COL

QDRANT_URL  = os.getenv("QDRANT_URL",  "http://localhost:6201")
qc = QdrantClient(url=QDRANT_URL)

# 1) 기존 컬렉션 삭제
if COL in [c.name for c in qc.get_collections().collections]:
    qc.delete_collection(collection_name=COL)
    print(f"✅ {COL} 컬렉션 삭제 완료")

# 2) 새 컬렉션 생성
reset_qdrant()
print(f"✅ {COL} 컬렉션 생성 완료")
