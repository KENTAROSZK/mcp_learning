# indexingと検索DBの両方を1つのMCPサーバで担わせるためのpython
import glob
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

# ==============================
# 設定
# ==============================
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

DATA_DIR = "data/source"


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
# テーブル作成
# ==============================
def create_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rag_docs (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embedding VECTOR(1024)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


create_table()


# ==============================
# MCPサーバ
# ==============================
mcp = FastMCP("rag-mcp-server")


# ------------------------------
# インデックス化ツール
# ------------------------------
@mcp.tool()
def index_files():
    """
    MarkdownファイルをDBにインデックス化する
    """
    files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    conn = get_conn()
    cur = conn.cursor()
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            emb = model.encode(text)
            cur.execute(
                "INSERT INTO rag_docs (content, embedding) VALUES (%s, %s::vector)",
                (text, emb.tolist()),
            )
    conn.commit()
    cur.close()
    conn.close()
    return {"indexed_files": len(files)}


# ------------------------------
# 検索ツール
# ------------------------------
@mcp.tool()
def search(query: str):
    """
    ベクトル検索ツール
    """
    emb = model.encode(query)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT content, embedding <-> %s::vector AS score
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


# ==============================
# エントリーポイント
# ==============================
if __name__ == "__main__":
    mcp.run()
