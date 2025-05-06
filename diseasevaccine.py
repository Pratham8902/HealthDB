import mysql.connector
import pandas as pd

# Connect to the MySQL database
db = mysql.connector.connect(
    host="localhost",        # e.g., "localhost" or "127.0.0.1"
    user="root",             # your MySQL username
    password="Pratham8902",  # your MySQL password
    database="HealthDB"      # your database name
)

cursor = db.cursor()

# Function to load Immunizations data from CSV and insert into the database
def load_immunizations_from_csv(file_path):
    # Read CSV file into pandas DataFrame
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        vaccine_name = row['Vaccine']
        virus = row['Virus']
        
        cursor.execute("""
            INSERT INTO Immunizations (vaccine_name, virus)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            vaccine_name = VALUES(vaccine_name), virus = VALUES(virus)
        """, (vaccine_name, virus))
    
    db.commit()
    print("Immunizations data loaded successfully!")

# Function to connect immunizations with diseases
def link_immunizations_with_diseases():
    cursor.execute("""
        SELECT vaccine_name, disease_id 
        FROM Immunizations
        JOIN Diseases ON Immunizations.virus = Diseases.name
    """)
    rows = cursor.fetchall()
    
    # Link Immunizations to Diseases
    for vaccine_name, disease_id in rows:
        cursor.execute("""
            INSERT INTO DiseaseVaccines (disease_id, vaccine_name)
            VALUES (%s, %s)
        """, (disease_id, vaccine_name))
    
    db.commit()
    print("Immunizations linked to diseases successfully!")

# File path to the CSV file
file_path = 'datasets\Immunization.csv'

# Load the immunizations data from CSV
load_immunizations_from_csv(file_path)

# Link immunizations to diseases
link_immunizations_with_diseases()

# Close the connection
cursor.close()
db.close()
