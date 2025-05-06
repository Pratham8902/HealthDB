import google.generativeai as genai
import mysql.connector

genai.configure(api_key="Insert Gemini 2.0 Key here")

def generate_sql_from_prompt(prompt):
    instruction = (
        "You are a SQL expert assistant. Generate executable MySQL code based on the user's request.\n"
        "The database has these tables:\n"
        "Patients(patient_id, name, age, gender),\n"
        "Diseases(disease_id, name),\n"
        "Symptoms(symptom_id, symptom),\n"
        "MedicalProcedures(procedure_id, name),\n"
        "PatientDetails(patient_id, disease_id, symptom_id, procedure_id, vacccine_name)\n\n"
        "For any disease/symptom/procedure mentioned, get their ID using SELECT.\n"
        "Use those IDs to populate PatientDetails.\n"
        "Retrieve data using IDs when asked.\n"
        "Use LAST_INSERT_ID() after inserting into Patients.\n"
        "Do NOT use markdown. Do NOT explain anything. Just return executable SQL code only.\n\n"
        f"User: {prompt}"
    )

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content(instruction)
    return response.text.strip()


import json

def extract_patient_data(prompt):
    instruction = (
        "You are an assistant that extracts structured patient data from clinical text.\n"
        "Respond with JSON like this:\n"
        "{\n"
        '  "name": "Raj",\n'
        '  "age": 21,\n'
        '  "gender": "Male",\n'
        '  "symptoms": ["headache", "nausea", "fatigue"],\n'
        '  "diseases": ["typhoid"],\n'
        '  "procedures": ["Covid test", "Sonography"],\n'
        '  "medicines": ["Ibuprofen"]\n'
        "}\n"
        "Return ONLY the raw JSON. No markdown. No 'json' label. No ``` block."
    )

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content([instruction, prompt])
    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1].strip()
    if raw_text.lower().startswith("json"):
        raw_text = raw_text[len("json"):].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON:", e)
        print("Gemini Output:\n", raw_text)
        return None



def get_id(cursor, table, column_value_name, value):
    id_columns = {
        "Patients": "patient_id",
        "Diseases": "disease_id",
        "Symptoms": "symptom_id",
        "MedicalProcedures": "procedure_id",
        "Immunizations": "vaccine_name"
    }

    lookup_columns = {
        "MedicalProcedures": "procedure_name",
        "Symptoms": "symptom", 
    }

    id_col = id_columns.get(table)
    col = lookup_columns.get(table, column_value_name) 

    if not id_col:
        raise ValueError(f"No ID column mapping defined for table: {table}")

    cursor.execute(f"SELECT {id_col} FROM {table} WHERE {col} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        print(f"⚠️ '{value}' not found in {table} (looked via `{col}`)")
        return None

def insert_patient_with_details(data):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Pratham8902',
        database='HealthDB'
    )
    cursor = conn.cursor()

    # 1. Insert patient
    cursor.execute("INSERT INTO Patients (name, age, gender) VALUES (%s, %s, %s)", 
                   (data["name"], data["age"], data["gender"]))
    conn.commit()
    patient_id = cursor.lastrowid

    # 2. Insert disease links
    for disease in data.get("diseases", []):
        disease_id = get_id(cursor, "Diseases", "name", disease)
        if disease_id:
            cursor.execute("INSERT INTO PatientDetails (patient_id, disease_id) VALUES (%s, %s)", 
                           (patient_id, disease_id))

    # 3. Insert symptom links
    for symptom in data.get("symptoms", []):
        symptom_id = get_id(cursor, "Symptoms", "symptom", symptom)
        if symptom_id:
            cursor.execute("INSERT INTO PatientDetails (patient_id, symptom_id) VALUES (%s, %s)", 
                           (patient_id, symptom_id))

    # 4. Insert procedure links
    for proc in data.get("procedures", []):
        procedure_id = get_id(cursor, "MedicalProcedures", "name", proc)
        if procedure_id:
            cursor.execute("INSERT INTO PatientDetails (patient_id, procedure_id) VALUES (%s, %s)", 
                           (patient_id, procedure_id))

    # (Optional) You could handle medicines separately
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Patient {data['name']} and details inserted successfully.")

def insert_patient_details(cursor, conn, name, age, gender, disease, symptoms, procedure, vaccine):
    cursor.execute("SELECT patient_id FROM Patients WHERE name = %s", (name,))
    patient_row = cursor.fetchone()
    if patient_row:
        print(f"ℹ️ Patient {name} already exists. Skipping insert.")
        return

    cursor.execute("INSERT INTO Patients (name, age, gender) VALUES (%s, %s, %s)", (name, age, gender))
    conn.commit()
    patient_id = cursor.lastrowid

    # Disease
    cursor.execute("SELECT disease_id FROM Diseases WHERE name = %s", (disease,))
    disease_row = cursor.fetchone()
    if not disease_row:
        print(f"⚠️ '{disease}' not found in Diseases")
        return
    disease_id = disease_row[0]

    # Procedure
    procedure_id = None
    if procedure:
        cursor.execute("SELECT procedure_id FROM MedicalProcedures WHERE procedure_name = %s", (procedure,))
        proc_row = cursor.fetchone()
        if not proc_row:
            print(f"⚠️ '{procedure}' not found in MedicalProcedures")
        else:
            procedure_id = proc_row[0]

    for symptom in symptoms:
        cursor.execute("SELECT symptom_id FROM Symptoms WHERE symptom = %s", (symptom,))
        symptom_row = cursor.fetchone()
        if not symptom_row:
            print(f"⚠️ '{symptom}' not found in Symptoms")
            continue
        symptom_id = symptom_row[0]

        cursor.execute("""
            INSERT INTO PatientDetails (patient_id, disease_id, symptom_id, procedure_id, vacccine_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, disease_id, symptom_id, procedure_id, vaccine))

    conn.commit()
    print(f"✅ Patient {name} and details inserted successfully.")

def get_or_insert_id(cursor, table, id_col, lookup_col, value):
    cursor.execute(f"SELECT {id_col} FROM {table} WHERE {lookup_col} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(f"INSERT INTO {table} ({lookup_col}) VALUES (%s)", (value,))
        cursor.execute(f"SELECT {id_col} FROM {table} WHERE {lookup_col} = %s", (value,))
        return cursor.fetchone()[0]

def clean_sql_output(sql_code):
    sql_code = sql_code.replace("```sql", "").replace("```", "")
    return sql_code.strip()

prompt = "Insert into database a patient who is 21 year old, Male, named Raj, who has headache, nausea, fatigue and had a history of typhoid, So Doctor recommended him X ray and Acidity testing, and some Ibuprofien."
#prompt = "Insert a 22-year-old female named Priya, who has chest pain and breathlessness, previously diagnosed with asthma. Doctor ordered a Spirometry test and prescribed Albuterol."

patient_data = extract_patient_data(prompt)
if patient_data:
    insert_patient_with_details(patient_data)
else:
    print("❌ Failed to extract patient data.")

sql_block = generate_sql_from_prompt(prompt)
sql_block = clean_sql_output(sql_block)

print("Generated SQL:\n", sql_block)

def run_sql_block(conn, sql_block):
    cursor = conn.cursor()
    result = None
    for stmt in sql_block.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cursor.execute(stmt)
            if stmt.lower().startswith("select"):
                result = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"❌ SQL Error: {err}")
    cursor.close()
    return result



def summarize_sql_result(prompt, rows, columns, gemini_model):
    if not rows:
        return "No matching data found."

    header = ", ".join(columns)
    data = "\n".join([", ".join(str(v) for v in row) for row in rows])

    context = f"""User question: {prompt}
SQL result:
{header}
{data}

Summarize or answer the user's question using the result."""
    
    try:
        gemini_response = gemini_model.generate_content(context)
        return gemini_response.text.strip()
    except Exception as e:
        return f"❌ Gemini Error: {e}"


conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Pratham8902',
    database='HealthDB'
)

while True:
    user_query = input("🧠 > ").strip()
    if user_query.lower() == "exit":
        break

    sql_query = generate_sql_from_prompt(user_query) 
    print("📝 Generated SQL:\n", sql_query)

    result = run_sql_block(conn, sql_query)
    if result:
        print("📋 Query Result:", result)
    else:
        print("⚠️ No results returned.")


def get_or_insert_id(cursor, table, id_col, lookup_col, value):
    cursor.execute(f"SELECT {id_col} FROM {table} WHERE {lookup_col} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(f"INSERT INTO {table} ({lookup_col}) VALUES (%s)", (value,))
        cursor.execute(f"SELECT {id_col} FROM {table} WHERE {lookup_col} = %s", (value,))
        return cursor.fetchone()[0]

def main():
    print("💬 Welcome to ChatDB (powered by Gemini)!")
    print("Type your natural language query. Type 'exit' to quit.\n")

    while True:
        prompt = input("🧠 > ").strip()

        if prompt.lower() in {"exit", "quit"}:
            print("👋 Exiting ChatDB. Bye!")
            break

        patient_data = extract_patient_data(prompt)
        if patient_data:
            insert_patient_with_details(patient_data)
        
        try:
            sql_block = generate_sql_from_prompt(prompt)
            sql_block = clean_sql_output(sql_block)
            print("\n📝 Generated SQL:\n", sql_block)
            run_sql_block(sql_block)
        except Exception as e:
            print("❌ Gemini/SQL Error:", e)

if __name__ == "__main__":
    main()
