import pandas as pd
from database import SessionLocal, Marka, Seri, Model

db = SessionLocal()

# --------------------------
# 1️⃣ Markaları ekle
# --------------------------
df_marka = pd.read_excel("marka.xlsx")

for _, row in df_marka.iterrows():
    marka_id = int(row['marka_id'])
    marka_adi = str(row['marka_adı']).strip()

    if not db.query(Marka).filter_by(id=marka_id).first():
        db.add(Marka(id=marka_id, ad=marka_adi))

db.commit()

# --------------------------
# 2️⃣ Serileri ekle
# --------------------------
df_seri = pd.read_excel("seri.xlsx")

for _, row in df_seri.iterrows():
    seri_id = int(row['seri_id'])
    marka_id = int(row['marka_id'])
    seri_adi = str(row['seri_adı']).strip()

    if not db.query(Seri).filter_by(id=seri_id).first():
        marka = db.query(Marka).filter_by(id=marka_id).first()
        if marka:
            db.add(Seri(id=seri_id, ad=seri_adi, marka_id=marka_id))

db.commit()

# --------------------------
# 3️⃣ Modelleri ekle
# --------------------------
df_model = pd.read_excel("model.xlsx")

for _, row in df_model.iterrows():
    model_id = int(row['model_id'])
    seri_id = int(row['seri_id'])
    model_adi = str(row['model_adı']).strip()

    if not db.query(Model).filter_by(id=model_id).first():

        seri = db.query(Seri).filter_by(id=seri_id).first()
        if seri:
            db.add(Model(id=model_id, ad=model_adi, seri_id=seri_id))

db.commit()
db.close()

print("✅ Tüm marka-seri-model ilişkileri başarıyla eklendi")
