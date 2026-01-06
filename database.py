from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Temel Base
Base = declarative_base()

# SQLite bağlantısı
engine = create_engine("sqlite:///arac_fiyat.db", echo=True)
SessionLocal = sessionmaker(bind=engine)

# Marka tablosu
class Marka(Base):
    __tablename__ = "marka"
    id = Column(Integer, primary_key=True)
    ad = Column(String, unique=True, nullable=False)
    seriler = relationship("Seri", back_populates="marka")

# Seri tablosu
class Seri(Base):
    __tablename__ = "seri"
    id = Column(Integer, primary_key=True)
    ad = Column(String, nullable=False)
    marka_id = Column(Integer, ForeignKey("marka.id"))
    marka = relationship("Marka", back_populates="seriler")
    modeller = relationship("Model", back_populates="seri")

# Model tablosu
class Model(Base):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True)
    ad = Column(String, nullable=False)
    seri_id = Column(Integer, ForeignKey("seri.id"))
    seri = relationship("Seri", back_populates="modeller")

# Tahmin edilen araçlar
class AracTahmin(Base):
    __tablename__ = "arac_tahmin"
    id = Column(Integer, primary_key=True)
    fiyat = Column(Float)
    yil = Column(Integer)
    kilometre = Column(Float)
    degisen_sayisi = Column(Integer)
    boyali_sayisi = Column(Integer)
    motor_hacmi_num = Column(Float)
    motor_gucu_num = Column(Float)
    marka_id = Column(Integer)
    seri_id = Column(Integer)
    model_id = Column(Integer)
    vites_tipi = Column(String)
    yakit_tipi = Column(String)
    kasa_tipi = Column(String)

# Tabloları oluştur
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("✅ Veritabanı ve tablolar oluşturuldu")
