from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import date
from .database import get_db
from . import models

router = APIRouter(prefix="/api/v1", tags=["Data Synchronization"])

@router.post("/sync")
def sync_fasih_data(payload: List[Dict[str, Any]], db: Session = Depends(get_db)):
    records_processed = 0
    today = date.today() # Ambil tanggal hari ini

    for item in payload:
        try:
            # 1. Ekstrak Data dari Bot
            email_petugas = item.get("email")
            region_code = item.get("regionCode", "") # KODE SLS UTUH
            iddesa_str = region_code.replace("-", "")[:10]
            
            target_usaha = item.get("regionTotal", 0)
            status_open = item.get("OPEN", 0)
            status_submitted = item.get("SUBMITTED BY Pencacah", 0)
            status_draft = item.get("DRAFT", 0)

            # Cek Master Data (Strict Mode)
            petugas = db.query(models.MasterPetugas).filter(models.MasterPetugas.email == email_petugas).first()
            wilayah = db.query(models.MasterWilayah).filter(models.MasterWilayah.iddesa == iddesa_str).first()

            if not petugas or not wilayah:
                continue

            # ==========================================
            # 2. UPSERT Master Assignment (Berdasarkan KODE SLS)
            # ==========================================
            assignment = db.query(models.MasterAssignment).filter(
                models.MasterAssignment.region_code == region_code,
                models.MasterAssignment.email_petugas == email_petugas
            ).first()
            
            if not assignment:
                assignment = models.MasterAssignment(
                    region_code=region_code, # Simpan SLS
                    id_desa=iddesa_str, 
                    email_petugas=email_petugas, 
                    target_usaha=target_usaha
                )
                db.add(assignment)
                db.commit()
                db.refresh(assignment)
            else:
                # Update jika target usaha berubah
                if assignment.target_usaha != target_usaha:
                    assignment.target_usaha = target_usaha
                    db.commit()

            # ==========================================
            # 3. UPSERT Transaction (1 Baris Per Hari Per SLS)
            # ==========================================
            transaksi = db.query(models.Transaction).filter(
                models.Transaction.id_assignment == assignment.id_assignment,
                func.date(models.Transaction.tanggal_data) == today
            ).first()

            if not transaksi:
                # Jika belum ada tarikan di hari ini, buat baru!
                transaksi = models.Transaction(
                    id_assignment=assignment.id_assignment,
                    status_open=status_open,
                    status_submitted=status_submitted,
                    status_draft=status_draft
                )
                db.add(transaksi)
            else:
                # Jika bot berjalan ke-2 atau ke-3 kalinya hari ini, UPDATE angkanya!
                transaksi.status_open = status_open
                transaksi.status_submitted = status_submitted
                transaksi.status_draft = status_draft
            
            db.commit()
            records_processed += 1

        except Exception as e:
            db.rollback()
            print(f"Error memproses baris {item.get('regionCode')}: {e}")
            continue

    return {
        "status": "success", 
        "message": f"Berhasil mensinkronisasi {records_processed} baris data SLS dari FASIH!"
    }

@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Endpoint ini akan menarik data untuk Frontend Next.js.
    Melakukan JOIN 3 Tabel (Wilayah, Assignment, Transaction) secara real-time.
    """
    today = date.today()
    
    # Query Data Agregasi per Desa/Kelurahan
    data_agregat = db.query(
        models.MasterWilayah.nmkec,
        models.MasterWilayah.nmdesa,
        func.sum(models.MasterAssignment.target_usaha).label('total_target'),
        func.sum(models.Transaction.status_submitted).label('total_selesai'),
        func.sum(models.Transaction.status_open).label('total_sisa')
    ).join(
        models.MasterAssignment, models.MasterWilayah.iddesa == models.MasterAssignment.id_desa
    ).join(
        models.Transaction, models.MasterAssignment.id_assignment == models.Transaction.id_assignment
    ).filter(
        func.date(models.Transaction.tanggal_data) == today
    ).group_by(
        models.MasterWilayah.nmkec,
        models.MasterWilayah.nmdesa
    ).all()

    # Rapihkan menjadi JSON yang mudah dibaca Next.js
    hasil = []
    for baris in data_agregat:
        target = int(baris.total_target or 0)
        selesai = int(baris.total_selesai or 0)
        sisa = int(baris.total_sisa or 0)
        
        # Hindari error pembagian dengan nol
        progres = round((selesai / target * 100), 2) if target > 0 else 0
        
        hasil.append({
            "kecamatan": baris.nmkec,
            "desa": baris.nmdesa,
            "target": target,
            "selesai": selesai,
            "sisa": sisa,
            "progres_persen": progres
        })
        
    return {"status": "success", "tanggal": today, "data": hasil}


@router.get("/dashboard/petugas")
def get_dashboard_summary_petugas(db: Session = Depends(get_db)):
    today = date.today()
    
    # Kueri diperbarui untuk menarik spesifik Region Code (Assignment)
    data_petugas = db.query(
        models.MasterPetugas.nama,
        models.MasterPetugas.email,
        models.MasterPetugas.role,
        models.MasterWilayah.nmkec.label('kecamatan'),
        models.MasterWilayah.nmdesa.label('desa'),
        models.MasterAssignment.region_code.label('assignment_code'), # 🌟 TARIK KODE ASSIGNMENT
        func.sum(models.MasterAssignment.target_usaha).label('total_target'),
        func.sum(models.Transaction.status_submitted).label('total_selesai'),
        func.sum(models.Transaction.status_open).label('total_sisa')
    ).join(
        models.MasterAssignment, models.MasterPetugas.email == models.MasterAssignment.email_petugas
    ).join(
        models.MasterWilayah, models.MasterAssignment.id_desa == models.MasterWilayah.iddesa
    ).join(
        models.Transaction, models.MasterAssignment.id_assignment == models.Transaction.id_assignment
    ).filter(
        func.date(models.Transaction.tanggal_data) == today
    ).group_by(
        models.MasterPetugas.nama, models.MasterPetugas.email, models.MasterPetugas.role,
        models.MasterWilayah.nmkec, models.MasterWilayah.nmdesa, 
        models.MasterAssignment.region_code # 🌟 GROUPING BERDASARKAN ASSIGNMENT
    ).all()

    hasil = []
    for baris in data_petugas:
        hasil.append({
            "nama": baris.nama,
            "email": baris.email,
            "role": baris.role,
            "kecamatan": baris.kecamatan,
            "desa": baris.desa,
            "assignment_code": baris.assignment_code, # 🌟 MASUKKAN KE JSON
            "target": int(baris.total_target or 0),
            "selesai": int(baris.total_selesai or 0),
            "sisa": int(baris.total_sisa or 0)
        })
        
    return {"status": "success", "tanggal": today, "data": hasil}

@router.get("/dashboard/timeline")
def get_dashboard_timeline(db: Session = Depends(get_db)):
    # Menarik seluruh sejarah transaksi
    data_historis = db.query(
        func.date(models.Transaction.tanggal_data).label('tanggal'),
        models.MasterWilayah.nmkec.label('kecamatan'),
        models.MasterWilayah.nmdesa.label('desa'),
        models.MasterAssignment.email_petugas.label('email_petugas'), # 🌟 SUNTIKAN BARU
        func.sum(models.MasterAssignment.target_usaha).label('total_target'),
        func.sum(models.Transaction.status_submitted).label('total_selesai'),
        func.sum(models.Transaction.status_open).label('total_sisa')
    ).join(
        models.MasterAssignment, models.MasterWilayah.iddesa == models.MasterAssignment.id_desa
    ).join(
        models.Transaction, models.MasterAssignment.id_assignment == models.Transaction.id_assignment
    ).group_by(
        func.date(models.Transaction.tanggal_data),
        models.MasterWilayah.nmkec,
        models.MasterWilayah.nmdesa,
        models.MasterAssignment.email_petugas # 🌟 GROUPING DIPERLUAS
    ).order_by(
        func.date(models.Transaction.tanggal_data).asc()
    ).all()

    hasil = []
    for baris in data_historis:
        hasil.append({
            "tanggal": str(baris.tanggal),
            "kecamatan": baris.kecamatan,
            "desa": baris.desa,
            "email_petugas": baris.email_petugas, # 🌟 MASUKKAN KE JSON
            "target": int(baris.total_target or 0),
            "selesai": int(baris.total_selesai or 0),
            "sisa": int(baris.total_sisa or 0)
        })
        
    return {"status": "success", "data": hasil}