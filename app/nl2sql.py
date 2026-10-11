import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.llm import get_llm
from app.database import get_schema, run_query

SQL_CHART_PROMPT = """Kamu adalah AI pakar MySQL untuk Universitas LKS. Tugasmu mengubah pertanyaan pengguna menjadi JSON.

Schema Database:
{schema}

Aturan:
1. Hanya gunakan tabel yang sah: jabatan_fungsional, fakultas, dosen, remunerasi.
2. HANYA boleh query SELECT. Dilarang INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.
3. Jika pertanyaan meminta visualisasi, grafik, tren, atau perbandingan data, set "chart": true, pilih "chartType" ("bar", "line", atau "pie"), dan berikan "chartTitle".
4. Jika tidak butuh grafik, set "chart": false, "chartType": null, "chartTitle": null.
5. Balas HANYA berupa JSON valid murni tanpa markdown (tanpa ```json):
{{
  "sql": "SELECT ...",
  "chart": true,
  "chartType": "bar",
  "chartTitle": "Perbandingan Total Remunerasi Dosen"
}}"""

def clean_json(text: str) -> dict:
    text_str = str(text).strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_str, flags=re.DOTALL).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback jika model menyertakan teks sebelum/sesudah blok JSON
        match = re.search(r"\{[\s\S]*\}", text_str)
        if match:
            return json.loads(match.group(0))
        raise

def validate_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")
    
    # 1. Wajib SELECT
    if not re.match(r"^(select|with)\b", cleaned, flags=re.IGNORECASE):
        raise ValueError("Hanya query SELECT yang diizinkan.")
        
    # 2. Blokir DDL / DML berbahaya
    forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
    for w in forbidden:
        if re.search(rf"\b{w}\b", cleaned, flags=re.IGNORECASE):
            raise ValueError(f"Perintah '{w}' dilarang demi keamanan skema.")
            
    # 3. Kriteria 4.c: Wajib HANYA mengakses tabel yang didefinisikan
    allowed_tables = {"jabatan_fungsional", "fakultas", "dosen", "remunerasi"}
    # Deteksi tabel setelah kata kunci FROM atau JOIN
    tables_used = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z0-9_]+)", cleaned, flags=re.IGNORECASE))
    
    # Pastikan setiap tabel yang dipanggil ada di daftar resmi
    invalid_tables = tables_used - allowed_tables
    if invalid_tables:
        raise ValueError(f"Tabel dilarang atau tidak sah: {', '.join(invalid_tables)}")
        
    return cleaned

def ask(question: str) -> dict:
    schema = get_schema()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SQL_CHART_PROMPT),
        ("human", "{question}")
    ])
    chain = prompt | get_llm() | StrOutputParser()
    raw = chain.invoke({"schema": schema, "question": question})
    plan = clean_json(raw)

    safe_sql = validate_sql(plan["sql"])
    columns, rows = run_query(safe_sql)

    return {
        "sql": safe_sql,
        "chart": plan.get("chart", False),
        "chartType": plan.get("chartType"),
        "chartTitle": plan.get("chartTitle"),
        "columns": columns,
        "data": rows
    }

# Alias untuk kompatibilitas
process_nl2sql = ask
