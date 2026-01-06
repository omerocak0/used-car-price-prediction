import os
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Veritabanı importları
from database import SessionLocal, Marka, Seri, Model

app = FastAPI()
templates = Jinja2Templates(directory="templates")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- MODEL SÜTUN YAPISI ----------------
model_columns = [
    "yil", "kilometre", "degisen_sayisi", "boyali_sayisi", 
    "motor_hacmi_num", "motor_gucu_num", "marka_num", "seri_num", "model_num",
    "vites_tipi_Düz", "vites_tipi_Otomatik", "vites_tipi_Yarı Otomatik",
    "yakit_tipi_Benzin", "yakit_tipi_Dizel", "yakit_tipi_Elektrik", "yakit_tipi_Hibrit", "yakit_tipi_LPG & Benzin",
    "kasa_tipi_Cabrio", "kasa_tipi_Coupe", "kasa_tipi_Hatchback/3", "kasa_tipi_Hatchback/5", 
    "kasa_tipi_MPV", "kasa_tipi_Pick-up", "kasa_tipi_Roadster", "kasa_tipi_SUV", "kasa_tipi_Sedan", "kasa_tipi_Station wagon"
]

# ---------------- MODELLERİN YÜKLENMESİ ----------------
MODEL_PATHS = {
    "Random Forest": r"C:\Users\omer\Desktop\fiyat_tahmin_modeli\modeller\random_forest.joblib",
    "KNN": r"C:\Users\omer\Desktop\fiyat_tahmin_modeli\modeller\knn.joblib",
    "Decision Tree": r"C:\Users\omer\Desktop\fiyat_tahmin_modeli\modeller\decision_tree.joblib",
    "Linear Regression": r"C:\Users\omer\Desktop\fiyat_tahmin_modeli\modeller\linear_model.joblib",
    "ANN": r"C:\Users\omer\Desktop\fiyat_tahmin_modeli\modeller\ann.joblib"
}

loaded_models = {}

print("🔄 Modeller yükleniyor...")

for name, path in MODEL_PATHS.items():
    if os.path.exists(path):
        try:
            loaded = joblib.load(path)
            
            # DURUM 1: Sözlük (XGBoost genellikle burada olur)
            if isinstance(loaded, dict):
                # Scaler ayıklama
                if 'scaler' in loaded:
                    loaded_models[f"{name}_scaler"] = loaded['scaler']
                
                # Model ayıklama (predict özelliği olan nesneyi bul)
                actual_model = loaded.get('model') or loaded.get('estimator') or loaded.get('algo')
                if not actual_model:
                    for val in loaded.values():
                        if hasattr(val, "predict") and "scaler" not in str(type(val)).lower():
                            actual_model = val
                            break
                loaded_models[name] = actual_model

            # DURUM 2: Liste veya Tuple
            elif isinstance(loaded, (tuple, list)):
                loaded_models[name] = loaded[0]
                if len(loaded) >= 3:
                    loaded_models[f"{name}_scaler"] = loaded[2]
            
            # DURUM 3: Doğrudan Nesne
            else:
                loaded_models[name] = loaded
                
            if loaded_models.get(name):
                print(f"✅ {name} başarıyla yüklendi.")
            else:
                print(f"⚠️ {name} yüklendi ama model nesnesi ayırt edilemedi.")
        except Exception as e:
            print(f"❌ {name} yüklenirken hata: {e}")
    else:
        print(f"⚠️ Dosya bulunamadı: {path}")

# ---------------- SEÇENEKLER ----------------
vites_tipi_options = ["Düz", "Otomatik", "Yarı Otomatik"]
yakit_tipi_options = ["Benzin", "Dizel", "Elektrik", "Hibrit", "LPG & Benzin"]
kasa_tipi_options = ["Cabrio", "Coupe", "Hatchback/3", "Hatchback/5", "MPV", "Pick-up", "Roadster", "SUV", "Sedan", "Station wagon"]
yil_options = list(range(1970, 2026))
algorithm_options = [name for name in MODEL_PATHS.keys() if name in loaded_models]

# ---------------- ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    db = SessionLocal()
    try:
        markalar_db = db.query(Marka).all()
        seriler_db = db.query(Seri).all()
        modeller_db = db.query(Model).all()

        seriler = {}
        for s in seriler_db:
            seriler.setdefault(s.marka_id, []).append({"id": s.id, "ad": s.ad})

        modeller = {}
        for m in modeller_db:
            modeller.setdefault(m.seri_id, []).append({"id": m.id, "ad": m.ad})

        markalar = {m.id: m.ad for m in markalar_db}
        
        form_data = {
            "yil": 2025, "kilometre": 0, "degisen_sayisi": 0, "boyali_sayisi": 0, 
            "motor_hacmi_num": 1600, "motor_gucu_num": 100, "vites_tipi": "Düz",
            "yakit_tipi": "Benzin", "kasa_tipi": "Sedan"
        }
        
        return templates.TemplateResponse("index.html", {
            "request": request, "markalar": markalar, "seriler": seriler, "modeller": modeller,
            "vites_tipi_options": vites_tipi_options, "yakit_tipi_options": yakit_tipi_options,
            "kasa_tipi_options": kasa_tipi_options, "yil_options": yil_options,
            "algorithm_options": algorithm_options, "tahmin": None, "form_data": form_data
        })
    finally:
        db.close()

@app.get("/get_options/{marka_id}", response_class=JSONResponse)
def get_options(marka_id: int):
    db = SessionLocal()
    try:
        seriler_db = db.query(Seri).filter(Seri.marka_id == marka_id).all()
        seriler = [{"id": s.id, "ad": s.ad} for s in seriler_db]
        modeller = {}
        for s in seriler_db:
            modeller_db = db.query(Model).filter(Model.seri_id == s.id).all()
            modeller[s.id] = [{"id": m.id, "ad": m.ad} for m in modeller_db]
        return {"seriler": seriler, "modeller": modeller}
    finally:
        db.close()

@app.post("/tahmin", response_class=HTMLResponse)
async def tahmin(
    request: Request,
    secilen_model: str = Form(...),
    marka: int = Form(...),
    seri: int = Form(...),
    model_id: int = Form(...),
    yil: int = Form(...),
    kilometre: int = Form(...),
    degisen_sayisi: int = Form(...),
    boyali_sayisi: int = Form(...),
    motor_hacmi_num: float = Form(...),
    motor_gucu_num: float = Form(...),
    vites_tipi: str = Form(...),
    yakit_tipi: str = Form(...),
    kasa_tipi: str = Form(...)
):
    model_obj = loaded_models.get(secilen_model)
    if not model_obj:
        return HTMLResponse(content=f"<h3>Hata: {secilen_model} yüklenemedi.</h3>")

    # DataFrame Hazırlama
    df = pd.DataFrame(0, index=[0], columns=model_columns)
    df.at[0, "yil"] = int(yil)
    df.at[0, "kilometre"] = int(kilometre)
    df.at[0, "degisen_sayisi"] = int(degisen_sayisi)
    df.at[0, "boyali_sayisi"] = int(boyali_sayisi)
    df.at[0, "motor_hacmi_num"] = float(motor_hacmi_num) 
    df.at[0, "motor_gucu_num"] = float(motor_gucu_num)
    df.at[0, "marka_num"] = int(marka)
    df.at[0, "seri_num"] = int(seri)
    df.at[0, "model_num"] = int(model_id)

    # One-Hot Encoding
    for col in [f"vites_tipi_{vites_tipi}", f"yakit_tipi_{yakit_tipi}", f"kasa_tipi_{kasa_tipi}"]:
        if col in df.columns:
            df.at[0, col] = 1

    # Scaler Uygulama
    scaler = loaded_models.get(f"{secilen_model}_scaler")
    df_final = pd.DataFrame(scaler.transform(df), columns=model_columns) if scaler else df

    # Tahmin
    try:
        prediction = model_obj.predict(df_final)
        fiyat_tahmin = float(prediction[0])
    except Exception as e:
        return HTMLResponse(content=f"<h3>Tahmin Hatası: {e}</h3>")

    # Sayfayı Yenileme
    db = SessionLocal()
    try:
        markalar_db = db.query(Marka).all()
        markalar = {m.id: m.ad for m in markalar_db}
        # Formun sıfırlanmaması için form_data'yı geri gönderiyoruz
        form_data = {
            "marka": marka, "seri": seri, "model_id": model_id, "yil": yil, 
            "kilometre": kilometre, "degisen_sayisi": degisen_sayisi, "boyali_sayisi": boyali_sayisi, 
            "motor_hacmi_num": motor_hacmi_num, "motor_gucu_num": motor_gucu_num, 
            "vites_tipi": vites_tipi, "yakit_tipi": yakit_tipi, "kasa_tipi": kasa_tipi
        }
        return templates.TemplateResponse("index.html", {
            "request": request, "tahmin": f"{fiyat_tahmin:,.0f} TL", "secilen_algoritma": secilen_model,
            "markalar": markalar, "vites_tipi_options": vites_tipi_options, "yakit_tipi_options": yakit_tipi_options,
            "kasa_tipi_options": kasa_tipi_options, "yil_options": yil_options,
            "algorithm_options": algorithm_options, "form_data": form_data
        })
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)