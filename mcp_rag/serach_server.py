# RAGの検索用のMCPサーバサーバ
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

current_path = Path(__file__).resolve()
dotenv_path = current_path.parent.parent / ".env"

load_dotenv(dotenv_path=dotenv_path)

MODEL_NAME = "embaas/sentence-transformers-multilingual-e5-large"
model = SentenceTransformer(MODEL_NAME)

PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "ragdb")
PG_USER = os.environ.get("POSTGRES_USER", "raguser")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "ragpass")


# ==============================
# DB接続
# ==============================
def get_conn():
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )
    register_vector(conn)
    return conn


# ==============================
# MCPサーバ
# ==============================
# server = Server("rag-search-server")
mcp = FastMCP("rag-search-server")


@mcp.tool()
def search(query: str):
    """ベクトル検索を行う"""
    emb = model.encode(query)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT content, embedding <-> %s AS score
        FROM rag_docs
        ORDER BY score ASC
        LIMIT 5;
        """,
        (emb.tolist(),),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"content": r[0], "score": r[1]} for r in rows]


if __name__ == "__main__":
    mcp.run()
