import streamlit as st
import pandas as pd
import subprocess
import sys
import os
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import MasterWilayah, MasterPetugas, UserAdmin, MasterAssignment, Transaction

# ==========================================
# INITIALIZATION & AUTHENTICATION CHECK
# ==========================================
st.set_page_config(page_title="SE2026 Admin Portal", page_icon="🔒", layout="wide")

db = SessionLocal()

# Inisiasi user superadmin bawaan jika database kosong
default_admin = db.query(UserAdmin).filter(UserAdmin.username == "superadmin").first()
if not default_admin:
    try:
        admin_baru = UserAdmin(username="superadmin")
        admin_baru.set_password("malang2026") # Password default superadmin
        db.add(admin_baru)
        db.commit()
    except IntegrityError:
        db.rollback()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==========================================
# SCREEN: LAYAR LOGIN UTAMA
# ==========================================
if not st.session_state.logged_in:
    st.markdown("""
        <style>
        .login-box { padding: 2rem; background-color: #1e293b; border-radius: 15px; border: 1px solid #334155; }
        </style>
    """, unsafe_allow_html=True)
    
    st.container()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")
        st.write("")
        st.title("🔒 Login Command Center SE2026")
        st.caption("Pintu Masuk Terisolasi Khusus Superadmin BPS")
        
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk Ke Sistem", type="primary")
            
            if submit_login:
                user = db.query(UserAdmin).filter(UserAdmin.username == user_input).first()
                if user and user.check_password(pass_input):
                    st.session_state.logged_in = True
                    st.session_state.username = user_input
                    st.rerun()
                else:
                    st.error("🚨 Kredensial Salah! Akses ditolak oleh server database.")
    st.stop()

# ==========================================
# NAVIGATION: SIDEBAR MENU UTAMA
# ==========================================
with st.sidebar:
    st.image("https://bps.go.id/assets/images/logo-bps.png", width=70)
    st.title("🛡️ Portal Utama")
    st.write(f"Login sebagai: **{st.session_state.username}**")
    st.markdown("---")
    
    # Navigasi Menu Sidebar Ditambah 1 Menu Baru
    menu = st.radio(
        "PILIH SEKTOR OPERASI:",
        [
            "📂 Upload Master Wilayah", 
            "📂 Upload Master Petugas", 
            "🕰️ Upload Data Historis (Mundur)", 
            "🚀 Trigger Bot FASIH"
        ],
        index=0
    )
    
    st.markdown("---")
    if st.button("🚪 Keluar (Logout)", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# MAIN CONTENT AREA
# ==========================================

# --- SEKTOR 1: UPLOAD MASTER WILAYAH ---
if menu == "📂 Upload Master Wilayah":
    st.header("📂 Upload Data Wilayah Sensus (Excel)")
    st.info("Format Kolom Excel Wajib: **kdkec**, **nmkec**, **kddesa**, **nmdesa**, **iddesa**")
    file_wilayah = st.file_uploader("Pilih file Master Wilayah (.xlsx)", type=["xlsx"])
    
    if file_wilayah is not None:
        df_wilayah = pd.read_excel(file_wilayah, dtype=str)
        df_wilayah.columns = df_wilayah.columns.str.strip()
        st.dataframe(df_wilayah.head())
        
        kolom_wajib = ['iddesa', 'kdkec', 'nmkec', 'kddesa', 'nmdesa']
        if not all(kolom in df_wilayah.columns for kolom in kolom_wajib):
            st.error(f"❌ Struktur kolom tidak valid! Wajib ada: {', '.join(kolom_wajib)}")
        else:
            if st.button("Suntikkan Data ke Database", type="primary"):
                with st.spinner("Mengintegrasikan data wilayah..."):
                    sukses = 0
                    for _, row in df_wilayah.iterrows():
                        cek = db.query(MasterWilayah).filter(MasterWilayah.iddesa == row['iddesa']).first()
                        if not cek:
                            db.add(MasterWilayah(
                                iddesa=row['iddesa'], kdkec=row['kdkec'],
                                nmkec=row['nmkec'], kddesa=row['kddesa'], nmdesa=row['nmdesa']
                            ))
                            sukses += 1
                    db.commit()
                    st.success(f"✅ Sistem Berhasil Mengamankan {sukses} Wilayah Baru!")

# --- SEKTOR 2: UPLOAD MASTER PETUGAS ---
elif menu == "📂 Upload Master Petugas":
    st.header("📂 Upload Registrasi Master Petugas (Excel)")
    st.info("Format Kolom Excel Wajib: **nama**, **email**, **role**")
    file_petugas = st.file_uploader("Pilih file Ketenagakerjaan Petugas (.xlsx)", type=["xlsx"])
    
    if file_petugas is not None:
        df_petugas = pd.read_excel(file_petugas, dtype=str)
        df_petugas.columns = df_petugas.columns.str.strip()
        st.dataframe(df_petugas.head())
        
        kolom_wajib = ['nama', 'email', 'role']
        if not all(kolom in df_petugas.columns for kolom in kolom_wajib):
            st.error(f"❌ Struktur kolom tidak valid! Wajib ada: {', '.join(kolom_wajib)}")
        else:
            if st.button("Suntikkan Data ke Database", type="primary"):
                with st.spinner("Mengintegrasikan data petugas..."):
                    sukses = 0
                    for _, row in df_petugas.iterrows():
                        cek = db.query(MasterPetugas).filter(MasterPetugas.email == row['email']).first()
                        if not cek:
                            db.add(MasterPetugas(nama=row['nama'], email=row['email'], role=row['role']))
                            sukses += 1
                    db.commit()
                    st.success(f"✅ Sistem Berhasil Mendaftarkan {sukses} Petugas Baru!")

# --- SEKTOR 3: UPLOAD DATA HISTORIS (NEW) ---
elif menu == "🕰️ Upload Data Historis (Mundur)":
    st.header("🕰️ Injeksi Data Historis Manual")
    st.write("Gunakan fitur ini jika bot gagal berjalan di masa lalu dan Anda ingin menyuntikkan file Excel *Backup* laporan bot ke tanggal tertentu.")
    
    # 1. Komponen Date Picker
    selected_date = st.date_input("Pilih Tanggal Eksekusi (Tanggal ini akan masuk ke tabel Transaction)", datetime.now())
    
    st.info("Upload file Excel Backup Bot FASIH. Pastikan menggunakan Sheet **Region_Status** yang berisi kolom: `email`, `regionCode`, `regionTotal`, `OPEN`, `SUBMITTED BY Pencacah`.")
    file_historis = st.file_uploader("Pilih file Backup Bot (.xlsx)", type=["xlsx"])
    
    if file_historis is not None:
        # Baca sheet Region_Status (atau sheet pertama jika tidak ada nama tersebut)
        try:
            df_historis = pd.read_excel(file_historis, sheet_name="Region_Status")
        except:
            df_historis = pd.read_excel(file_historis)
            
        st.write("Preview Data:")
        st.dataframe(df_historis.head())
        
        if st.button("Injeksi Historis ke Database", type="primary"):
            with st.spinner(f"Menyuntikkan data untuk tanggal {selected_date}..."):
                records_processed = 0
                
                for index, row in df_historis.iterrows():
                    email_petugas = str(row.get("email", ""))
                    region_code = str(row.get("regionCode", ""))
                    iddesa_str = region_code.replace("-", "")[:10]
                    
                    target_usaha = int(row.get("regionTotal", 0))
                    status_open = int(row.get("OPEN", 0))
                    status_submitted = int(row.get("SUBMITTED BY Pencacah", 0))
                    status_draft = int(row.get("DRAFT", 0))

                    # STRICT MODE: Hanya masukkan jika Master ada
                    petugas = db.query(MasterPetugas).filter(MasterPetugas.email == email_petugas).first()
                    wilayah = db.query(MasterWilayah).filter(MasterWilayah.iddesa == iddesa_str).first()

                    if not petugas or not wilayah:
                        continue

                    # 1. Cek atau Buat Assignment
                    assignment = db.query(MasterAssignment).filter(
                        MasterAssignment.region_code == region_code,
                        MasterAssignment.email_petugas == email_petugas
                    ).first()
                    
                    if not assignment:
                        assignment = MasterAssignment(
                            region_code=region_code, 
                            id_desa=iddesa_str, 
                            email_petugas=email_petugas, 
                            target_usaha=target_usaha
                        )
                        db.add(assignment)
                        db.commit()
                        db.refresh(assignment)
                    else:
                        if assignment.target_usaha != target_usaha:
                            assignment.target_usaha = target_usaha
                            db.commit()

                    # 2. Cek atau Buat Transaction DI TANGGAL TERPILIH
                    transaksi = db.query(Transaction).filter(
                        Transaction.id_assignment == assignment.id_assignment,
                        func.date(Transaction.tanggal_data) == selected_date
                    ).first()

                    if not transaksi:
                        transaksi = Transaction(
                            id_assignment=assignment.id_assignment,
                            tanggal_data=selected_date,  # <-- TANGGAL KUSTOM DARI ADMIN
                            status_open=status_open,
                            status_submitted=status_submitted,
                            status_draft=status_draft
                        )
                        db.add(transaksi)
                    else:
                        # Timpa / Update jika sudah ada data di tanggal yang sama
                        transaksi.status_open = status_open
                        transaksi.status_submitted = status_submitted
                        transaksi.status_draft = status_draft
                    
                    db.commit()
                    records_processed += 1
                
                st.success(f"✅ Injeksi Selesai! Berhasil mensinkronisasi {records_processed} baris data SLS untuk tanggal {selected_date}.")

# --- SEKTOR 4: TRIGGER BOT FASIH & LIVE CONSOLE LOG VIEW ---
elif menu == "🚀 Trigger Bot FASIH":
    st.header("🚀 Eksekusi Bot Crawler FASIH (On-Demand Ingestion)")
    st.write("Tekan tombol di bawah untuk memicu jalannya `bot_fasih.py` tanpa lewat CLI terminal.")
    
    st.subheader("🖥️ Real-time Ingestion Stream Log")
    log_area = st.empty()
    
    log_area.markdown("""
        <div style='background-color: #0f172a; color: #10b981; font-family: monospace; 
                    padding: 15px; border-radius: 10px; height: 350px; overflow-y: auto; 
                    border: 1px solid #334155;'>
            Menunggu instruksi eksekusi...
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💥 JALANKAN MESIN PENARIK DATA", type="primary"):
        st.warning("Mesin dijalankan! Mengaktifkan Playwright, mohon pantau pergerakan log di bawah ini...")
        
        if not os.path.exists("bot_fasih.py"):
            st.error("🚨 Kegagalan Fatal: File script `bot_fasih.py` tidak ditemukan di root project!")
        else:
            proses = subprocess.Popen(
                [sys.executable, "bot_fasih.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            log_akumulasi = ""
            while True:
                baris_log = proses.stdout.readline()
                if not baris_log and proses.poll() is not None:
                    break
                if baris_log:
                    log_akumulasi += baris_log
                    
                    html_log = f"""
                    <div style='background-color: #0f172a; color: #10b981; font-family: monospace; 
                                padding: 15px; border-radius: 10px; height: 350px; overflow-y: auto; 
                                border: 1px solid #334155; white-space: pre-wrap; display: flex; flex-direction: column-reverse;'>
                        <div>{log_akumulasi}</div>
                    </div>
                    """
                    log_area.markdown(html_log, unsafe_allow_html=True)
                    
            st.success("🏁 Siklus Operasi Bot FASIH Selesai Dieksekusi!")

db.close()