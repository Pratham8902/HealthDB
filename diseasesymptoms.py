import pandas as pd
import mysql.connector

# === CONFIG ===
CSV_PATH = "datasets\disease.csv"
DB_CONFIG = {
    'user': 'root',
    'password': 'Pratham8902',
    'host': 'localhost',
    'database': 'HealthDB'
}

# === LOAD CSV ===
df = pd.read_csv(CSV_PATH)

# === CONNECT TO MYSQL ===
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# === INSERT UNIQUE SYMPTOMS & DISEASES ===
for _, row in df.iterrows():
    disease = row["Disease"].strip()
    
    # Insert disease if not exists
    cursor.execute("INSERT IGNORE INTO Diseases (name) VALUES (%s)", (disease,))
    conn.commit()
    
    # Get disease_id
    cursor.execute("SELECT disease_id FROM Diseases WHERE name = %s", (disease,))
    disease_id = cursor.fetchone()[0]
    
    for col in df.columns:
        if col.startswith("Symptom") and pd.notna(row[col]):
            symptom = row[col].strip()
            
            # Insert symptom if not exists
            cursor.execute("INSERT IGNORE INTO Symptoms (symptom) VALUES (%s)", (symptom,))
            conn.commit()
            
            # Get symptom_id
            cursor.execute("SELECT symptom_id FROM Symptoms WHERE symptom = %s", (symptom,))
            symptom_id = cursor.fetchone()[0]
            
            # Insert into mapping table
            cursor.execute("""
                INSERT IGNORE INTO DiseaseSymptoms (disease_id, symptom_id)
                VALUES (%s, %s)
            """, (disease_id, symptom_id))
            conn.commit()

# === CLEANUP ===
cursor.close()
conn.close()

print("✅ Disease-symptom relationships imported!")
