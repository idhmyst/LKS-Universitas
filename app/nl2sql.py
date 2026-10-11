import re
import json
from app.llm import get_llm
from app.database import execute_query, get_database_schema_summary

def clean_sql_output(raw_text: str) -> str:
    """Membersihkan raw response LLM agar hanya menyisakan query SQL murni."""
    # Ambil teks di dalam blok ```sql ... ``` jika ada
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
    else:
        sql = raw_text.strip()
    
    # Hapus semicolon di akhir jika ada
    sql = sql.rstrip(";").strip()
    return sql

def generate_sql(question: str) -> str:
    """Mengubah pertanyaan bahasa alami menjadi query SQL MySQL."""
    llm = get_llm()
    schema_info = get_database_schema_summary()
    
    prompt = f"""Kamu adalah data analyst & SQL expert untuk database MySQL universitas.
Tugasmu adalah menghasilkan query SQL murni (MySQL syntax) berdasarkan pertanyaan user dan skema tabel berikut.

{schema_info}

ATURAN PENTING:
1. HANYA hasilkan 1 query SQL murni (SELECT).
2. JANGAN sertakan penjelasan apa pun selain query SQL itu sendiri.
3. Gunakan JOIN yang tepat jika data menghubungkan antar tabel (misalnya: dosen JOIN fakultas ON dosen.fakultas_id = fakultas.id).
4. Pencarian teks sebaiknya gunakan LIKE %...% atau nama yang relevan jika sesuai.
5. Format mata uang ada di tunjangan dan gaji, gunakan agregasi (SUM, AVG, COUNT, MAX, MIN) sesuai kebutuhan.
6. Jangan gunakan perintah berbahaya (INSERT, UPDATE, DELETE, DROP, ALTER).

Pertanyaan User: {question}

Query SQL:"""

    response = llm.invoke(prompt)
    
    # Handle response langchain (bisa string atau list of content dicts)
    content = response.content
    if isinstance(content, list):
        # Ambil text jika formatnya [{'type': 'text', 'text': '...'}]
        raw_text = "".join([part.get("text", "") for part in content if isinstance(part, dict)])
    else:
        raw_text = str(content)
        
    return clean_sql_output(raw_text)

def generate_answer(question: str, sql: str, data: list) -> str:
    """Merangkum data hasil eksekusi query ke dalam kalimat bahasa Indonesia yang ramah dan informatif."""
    llm = get_llm()
    
    # Batasi data jika terlalu banyak agar tidak melebihi konteks
    sample_data = data[:25]
    total_rows = len(data)
    
    prompt = f"""Kamu adalah asisten AI Universitas LKS yang ramah, profesional, dan membantu.
User mengajukan pertanyaan, lalu sistem menjalankan SQL berikut dan memperoleh hasil data dari database:

Pertanyaan User: {question}
Query SQL: {sql}
Hasil Data ({total_rows} baris ditemukan): {json.dumps(sample_data, default=str, ensure_ascii=False)}

Tugasmu:
Berikan jawaban akhir dalam bahasa Indonesia yang ringkas, jelas, akurat, dan mudah dipahami berdasarkan data di atas.
Jika ada angka nominal uang (rupiah), formatlah dengan rapi (misal: Rp 15.000.000).
Jika data kosong, beri tahu dengan sopan bahwa data yang dicari tidak ditemukan."""

    response = llm.invoke(prompt)
    content = response.content
    if isinstance(content, list):
        return "".join([part.get("text", "") for part in content if isinstance(part, dict)]).strip()
    return str(content).strip()

def process_nl2sql(question: str) -> dict:
    """Pipeline lengkap: Natural Language -> SQL -> Database Execution -> Natural Language Answer."""
    try:
        sql = generate_sql(question)
    except Exception as e:
        return {
            "question": question,
            "sql": "",
            "result": [],
            "answer": f"Gagal menghasilkan SQL: {str(e)}",
            "error": str(e)
        }
        
    try:
        result = execute_query(sql)
    except Exception as e:
        return {
            "question": question,
            "sql": sql,
            "result": [],
            "answer": f"Terjadi kesalahan saat mengeksekusi query database: {str(e)}",
            "error": str(e)
        }
        
    try:
        answer = generate_answer(question, sql, result)
    except Exception as e:
        answer = f"Berhasil mendapatkan {len(result)} data, tetapi gagal merangkum jawaban: {str(e)}"

    return {
        "question": question,
        "sql": sql,
        "result": result,
        "answer": answer,
        "error": None
    }
