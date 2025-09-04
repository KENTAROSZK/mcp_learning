# 入力されたマークダウンテキストをインデックス化するためのMCPサーバ
import glob
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# from mcp.server import Server
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
# server = Server("rag-index-server")
mcp = FastMCP("rag-index-server")


@mcp.tool()
def index_files():
    """マークダウンファイルをインデックス化する"""
    files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    conn = get_conn()
    cur = conn.cursor()

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            emb = model.encode(text)
            cur.execute(
                "INSERT INTO rag_docs (content, embedding) VALUES (%s, %s)",
                (text, emb.tolist()),
            )
    conn.commit()
    cur.close()
    conn.close()
    return {"indexed_files": len(files)}


if __name__ == "__main__":
    mcp.run()
