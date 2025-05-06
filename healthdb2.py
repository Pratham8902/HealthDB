import google.generativeai as genai
import mysql.connector

# === CONFIG ===
genai.configure(api_key="Insert Gemini 2.0 Key here")

# === Gemini to SQL ===
def generate_sql_from_prompt(prompt):
    instruction = (
    "You are a helpful assistant that converts natural language to MySQL queries.\n"
    "Only return valid MySQL SQL queries wrapped in ```sql. No explanation.\n\n"
    "✅ Requirements:\n"
    "- Do NOT use IF/ELSE or procedural blocks — only use plain SQL.\n"
    "- Do NOT use 'name' as a column unless it exists. Use correct column names like 'name', 'procedure_name', etc.\n"
    "- Always check if a patient exists using SELECT. If not found, INSERT the patient.\n"
    "- Use `SELECT patient_id INTO @patient_id` instead of LAST_INSERT_ID() after SELECT.\n"
    "- Use DISTINCT while retrieving patient details"
    "- For ALL queries about a patient's attributes (diseases, symptoms, procedures), ALWAYS use DISTINCT.\n"
    "- When joining through PatientDetails, always use DISTINCT to avoid duplicate values.\n"
    "- When querying for a patient's disease or symptoms, always use DISTINCT to avoid duplicates."
    "- Use correct column names based on tables:\n"
    "  • Patients(name, age, gender)\n"
    "  • Diseases(disease_id, name)\n"
    "  • Symptoms(symptom_id, symptom)\n"
    "  • MedicalProcedures(procedure_id, procedure_name)\n"
    "  • PatientDetails(patient_id, disease_id, symptom_id, procedure_id, vaccine_name)\n"
    "- When inserting into PatientDetails, make sure the foreign keys exist first.\n"
    "- Use INSERT IGNORE for all inserts to avoid duplication errors.\n"
    "- Use COMMIT at the end of the transaction.\n"
    "- Use LIMIT 1 with SELECT INTO to avoid multi-row errors.\n\n"
    "📌 IMPORTANT: When querying for: \n"
    "- Diseases: Use DISTINCT and join through PatientDetails \n"
    "- Symptoms: Use DISTINCT and join through PatientDetails \n"
    "- Procedures: Use DISTINCT and join through PatientDetails \n"
    "Example Correct Pattern: \n"
    "```sql \n"
    "SELECT DISTINCT D.name FROM Diseases D \n" 
    "JOIN PatientDetails PD ON D.disease_id = PD.disease_id \n"
    "JOIN Patients P ON PD.patient_id = P.patient_id \n"
    "WHERE P.name = 'PatientName'; \n"
    "``` \n"
    "- For vaccine queries, first try searching Immunizations.virus column directly\n"
    "- Use pattern matching with LIKE '%disease%' for broader matches\n"
    "- Example direct vaccine query:\n"
    "```sql\n"
    "SELECT vaccine_name, virus\n"
    "FROM Immunizations\n"
    "WHERE virus LIKE '%DiseaseName%' OR vaccine_name LIKE '%DiseaseName%';\n"
    "```\n"
    "📌 Example:\n"
    "User: Insert a 30-year-old female named Maya, diagnosed with dengue, showing symptoms of fever and rash, and was prescribed Paracetamol and advised a Blood test.\n"
    "Generated SQL:\n"
    "```sql\n"
    "START TRANSACTION;\n"
    "SELECT patient_id INTO @patient_id FROM Patients WHERE name = 'Maya' AND age = 30 AND gender = 'Female' LIMIT 1;\n"
    "INSERT IGNORE INTO Patients (name, age, gender) VALUES ('Maya', 30, 'Female');\n"
    "SELECT patient_id INTO @patient_id FROM Patients WHERE name = 'Maya' AND age = 30 AND gender = 'Female' LIMIT 1;\n"
    "INSERT IGNORE INTO Diseases (name) VALUES ('dengue');\n"
    "SELECT disease_id INTO @disease_id FROM Diseases WHERE name = 'dengue' LIMIT 1;\n"
    "INSERT IGNORE INTO Symptoms (symptom) VALUES ('fever'), ('rash');\n"
    "SELECT symptom_id INTO @fever_id FROM Symptoms WHERE symptom = 'fever' LIMIT 1;\n"
    "SELECT symptom_id INTO @rash_id FROM Symptoms WHERE symptom = 'rash' LIMIT 1;\n"
    "INSERT IGNORE INTO MedicalProcedures (procedure_name) VALUES ('Blood test');\n"
    "SELECT procedure_id INTO @procedure_id FROM MedicalProcedures WHERE procedure_name = 'Blood test' LIMIT 1;\n"
    "INSERT IGNORE INTO PatientDetails (patient_id, disease_id, symptom_id, procedure_id, vaccine_name) VALUES\n"
    "(@patient_id, @disease_id, @fever_id, @procedure_id, 'Paracetamol'),\n"
    "(@patient_id, @disease_id, @rash_id, @procedure_id, 'Paracetamol');\n"
    "COMMIT;\n"
    "```\n\n"
    f"User: {prompt}"
)

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content([instruction])
    return response.text.strip()

# === Clean Gemini Output ===
def clean_sql_output(sql_code):
    return sql_code.replace("```sql", "").replace("```", "").strip()

# === Run SQL Queries ===
def run_sql_block(conn, sql_code):
    cursor = conn.cursor()
    result = []
    
    for stmt in sql_code.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cursor.execute(stmt)

            if stmt.lower().startswith("select") or "show" in stmt.lower():
                rows = cursor.fetchall()
                if rows:
                    result.extend(rows)

            while cursor.nextset():
                pass

        except mysql.connector.Error as err:
            print(f"❌ SQL Error: {err}")

    cursor.close()
    return result if result else None

def start_chat():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Pratham8902',
        database='HealthDB'
    )

    print("💬 Welcome to ChatDB (powered by Gemini + MySQL)!")
    print("Type your natural language query. Type 'exit' to quit.\n")

    while True:
        user_query = input("🧠 > ").strip()
        if user_query.lower() == "exit":
            break

        sql_query = generate_sql_from_prompt(user_query)
        print("📝 Generated SQL:\n", sql_query)

        sql_query = clean_sql_output(sql_query)
        results = run_sql_block(conn, sql_query)

        if results:
            print("📋 Query Result:")
            for row in results:
                print("  →", row)
        else:
            print("⚠️ No results returned or query had no output.")

    conn.close()

def clean_sql_output(sql_code):
    sql = sql_code.replace("```sql", "").replace("```", "").strip()
    # Auto-add DISTINCT to attribute queries
    if any(keyword in sql.lower() for keyword in ["disease", "symptom", "procedure"]):
        if "select" in sql.lower() and "distinct" not in sql.lower():
            sql = sql.replace("SELECT", "SELECT DISTINCT", 1)
    return sql

# === Run It ===
if __name__ == "__main__":
    start_chat()

# Insert into database a patient who is 21 year old, Male, named Raj, who has headache, nausea, fatigue and had a history of typhoid, So Doctor recommended him X ray and testing for Acidity.
# Insert a 22-year-old female named Priya, who has headache and dizziness, previously diagnosed with Migraine. Doctor ordered a depression screening for her.

# Queries #
# What is the age of Raj?
# What is the disease of Raj?
# What are the symptoms of Raj?

# What is the age of Priya?
# What is the disease of Priya?
# What are the symptoms of Priya?

# Name all the patients
# What are the common symptoms between Raj and Priya?

# Give me the oldest patient
# Update Raj's age to 31
# What is the age of Raj?

# What are the tables in this database?
# What procedures did Raj undergo?

# What is the vaccine for Typhoid?
# What are the types of Hepatitis?

# How many patients have each disease?