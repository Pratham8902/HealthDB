import google.generativeai as genai
import mysql.connector
import streamlit as st

# API Key
genai.configure(api_key="Insert Gemini 2.0 Key here")

# Gemini Prompt
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

# Gemini uses single quotes which stops the query from executing, this prevents that.
def clean_sql_output(sql_code):
    return sql_code.replace("```sql", "").replace("```", "").strip()

# Running the SQL Queries
def run_sql_block(conn, sql_code):
    cursor = conn.cursor()
    result = []
    
    for stmt in sql_code.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cursor.execute(stmt)

            # The SELECT queries are stored in a variable, and then used as input as well
            if cursor.with_rows:
                rows = cursor.fetchall()
                if rows:
                    result.extend(rows)

            while cursor.nextset():
                pass

        except mysql.connector.Error as err:
            print(f"SQL Error: {err}")

    cursor.close()
    return result if result else None


# Main Gemini chat function to chat in the terminal (Now Streamlit)
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
        user_query = input("🧠 > ").strip() # Emoji's added for website mode
        if user_query.lower() == "exit": # Break function
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
            print("⚠️ No results returned or query had no output.") # Incase, the data requested DNE

    conn.close()

def clean_sql_output(sql_code): 
    sql = sql_code.replace("```sql", "").replace("```", "").strip()

    # Auto-add DISTINCT to attribute queries as the output was getting duplicate due to multiplication in the patientdetails table
    if any(keyword in sql.lower() for keyword in ["disease", "symptom", "procedure"]): 
        if "select" in sql.lower() and "distinct" not in sql.lower():
            sql = sql.replace("SELECT", "SELECT DISTINCT", 1)
    return sql

# Main function with Streamlit
def main():
    st.set_page_config(page_title="HealthDB AI Assistant", page_icon="🏥")
    
    st.title("🏥 HealthDB AI Assistant")
    st.caption("Convert natural language queries to SQL and get results from your healthcare database")
    
    # Initialize session state
    if "history" not in st.session_state:
        st.session_state.history = []
    
    # Sidebar with database info
    with st.sidebar:
        st.header("Database Connection")
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Pratham8902',
                database='HealthDB'
            )

            st.success("✅ Connected to database")
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
            conn = None
        
        st.header("Query History")
        for i, item in enumerate(st.session_state.history[:20]):  # Limit to last 10 queries
            with st.expander(f"Query {i+1}: {item['query'][:50]}..."):
                st.text_area("User Query", 
                           value=item['query'], 
                           height=max(68, len(item['query'])//3),  # Dynamic height
                           disabled=True,
                           key=f"text_area_{i}" 
                )
                
                if st.button("Show Results", key=f"btn_{i}"):
                    st.session_state.current_result = item['result']
    
    # Main chat interface
    if conn:  
        query = st.chat_input("Ask about patients, diseases, or vaccines...")
        
        if query:
            with st.spinner("Generating SQL..."):
                try:
                    # Calling all the SQL functions and cleaning it
                    sql_query = generate_sql_from_prompt(query)
                    cleaned_sql = clean_sql_output(sql_query)
                    
                    with st.chat_message("user"):
                        st.write(query)
                    
                    with st.chat_message("assistant"):
                        st.subheader("Generated SQL")
                        st.code(cleaned_sql)
                        
                        try:
                            results = run_sql_block(conn, cleaned_sql)
                            
                            # Add to history
                            st.session_state.history.insert(0, {
                                "query": query,
                                "sql": cleaned_sql,
                                "result": results
                            })
                            
                            st.subheader("Results")
                            if results:
                                st.dataframe(results)  # Better display for tabular data 
                            else:                      # as the output was with commas, brackets
                                st.info("No results returned")
                                
                        except Exception as e:
                            st.error(f"Database error: {str(e)}")
                            
                except Exception as e:
                    st.error(f"Error generating SQL: {str(e)}")

if __name__ == "__main__":
    main()
