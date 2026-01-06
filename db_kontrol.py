import sqlite3

# ### ÖNCE BUNU DENE
conn = sqlite3.connect("arac_fiyat.db")
# conn = sqlite3.connect("arac.db")   # bunu kapattık

cursor = conn.cursor()

print("\n--- MARKALAR ---")
cursor.execute("SELECT * FROM marka")
print(cursor.fetchall())

print("\n--- SERİLER ---")
cursor.execute("SELECT * FROM seri")
print(cursor.fetchall())

print("\n--- MODELLER ---")
cursor.execute("SELECT * FROM model")
print(cursor.fetchall()[:20])  # ilk 20 model

conn.close()
