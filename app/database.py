import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "universitas_lks"),
        port=int(os.getenv("DB_PORT", 3306))
    )

def execute_query(sql_query: str):
    """
    Eksekusi query SQL (khusus read-only SELECT) dan kembalikan list of dict.
    """
    clean_sql = sql_query.strip().strip(";").strip()
    # Keamanan dasar: pastikan hanya query SELECT yang dieksekusi
    if not clean_sql.upper().startswith("SELECT") and not clean_sql.upper().startswith("SHOW") and not clean_sql.upper().startswith("DESCRIBE"):
        raise ValueError("Hanya query SELECT/read-only yang diizinkan untuk keamanan data.")

    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(clean_sql)
        rows = cursor.fetchall()
        # Konversi Decimal/Date/Time jadi tipe native serializable
        formatted_rows = []
        for row in rows:
            formatted_row = {}
            for k, v in row.items():
                if hasattr(v, "__float__"):
                    formatted_row[k] = float(v)
                else:
                    formatted_row[k] = v
            formatted_rows.append(formatted_row)
        return formatted_rows
    finally:
        conn.close()

def get_database_schema_summary() -> str:
    """Mengembalikan ringkasan skema tabel database untuk prompt context."""
    return """
Tabel-tabel dalam database `universitas_lks`:

1. `fakultas`:
   - id: INT (Primary Key)
   - nama: VARCHAR (Contoh: 'Ilmu Komputer', 'Ekonomi')
   - dekan: VARCHAR (Nama Dekan, Contoh: 'Dr. Budi Santoso')

2. `jabatan_fungsional`:
   - id: INT (Primary Key)
   - nama: VARCHAR (Contoh: 'Asisten Ahli', 'Lektor', 'Lektor Kepala', 'Guru Besar')
   - tunjangan_dasar: DECIMAL

3. `dosen`:
   - id: INT (Primary Key)
   - nidn: VARCHAR (Nomor Induk Dosen)
   - nama: VARCHAR (Nama lengkap dosen dengan gelar)
   - foto: VARCHAR
   - pendidikan_terakhir: VARCHAR ('S1', 'S2', 'S3')
   - status_kepegawaian: VARCHAR ('Tetap', 'Kontrak')
   - fakultas_id: INT (Foreign Key ke fakultas.id)
   - jabatan_id: INT (Foreign Key ke jabatan_fungsional.id)

4. `remunerasi`:
   - id: INT (Primary Key)
   - dosen_id: INT (Foreign Key ke dosen.id)
   - tahun: INT (Contoh: 2026)
   - bulan: INT (Contoh: 1 sampai 12)
   - gaji_pokok: DECIMAL
   - tunjangan_jabatan: DECIMAL
   - tunjangan_fungsional: DECIMAL
   - tunjangan_kinerja: DECIMAL
   - total_remunerasi: DECIMAL
"""
