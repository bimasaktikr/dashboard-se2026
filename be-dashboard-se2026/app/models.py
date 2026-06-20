import hashlib
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class UserAdmin(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_superadmin = Column(Boolean, default=True)

    def set_password(self, password: str):
        # Menggunakan SHA-256 untuk hashing sederhana pada level dev
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
class MasterPetugas(Base):
    __tablename__ = "master_petugas"
    
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    # Email dijadikan UNIQUE index agar bisa di-reference oleh Master_Assignment
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(50))

class MasterWilayah(Base):
    __tablename__ = "master_wilayah"
    
    # Menggunakan iddesa dari Excel sebagai Primary Key
    iddesa = Column(String(20), primary_key=True, index=True)
    kdkec = Column(String(10))
    nmkec = Column(String(100))
    kddesa = Column(String(10))
    nmdesa = Column(String(100))

class MasterAssignment(Base):
    __tablename__ = "master_assignment"
    
    id_assignment = Column(Integer, primary_key=True, index=True)
    
    # KUNCI UTAMA: Menyimpan kode SLS utuh dari Bot (Misal: 35730100010001)
    region_code = Column(String(50), index=True) 
    
    id_desa = Column(String(20), ForeignKey("master_wilayah.iddesa"))
    email_petugas = Column(String(100), ForeignKey("master_petugas.email"))
    target_usaha = Column(Integer, default=0)

    wilayah = relationship("MasterWilayah")
    petugas = relationship("MasterPetugas")

class Transaction(Base):
    __tablename__ = "transaction"
    
    id_transaksi = Column(Integer, primary_key=True, index=True)
    id_assignment = Column(Integer, ForeignKey("master_assignment.id_assignment"))
    
    # Auto-timestamp yang dibuat otomatis oleh server database
    tanggal_data = Column(DateTime(timezone=True), server_default=func.now())
    
    status_open = Column(Integer, default=0)
    status_submitted = Column(Integer, default=0)
    status_draft = Column(Integer, default=0)

    assignment = relationship("MasterAssignment")