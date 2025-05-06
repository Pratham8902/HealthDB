import mysql.connector
import csv

# Connect to the MySQL database
db = mysql.connector.connect(
    host="localhost",        # e.g., "localhost" or "127.0.0.1"
    user="root",             # your MySQL username
    password="Pratham8902",  # your MySQL password
    database="HealthDB"      # your database name
)

cursor = db.cursor()

# Read the CSV file and load the data into the MedicalProcedures table
def load_medical_procedures_from_csv(csv_file):
    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)  # Assumes the first row contains the header (procedure_name)
        
        for row in csv_reader:
            procedure_name = row['procedure_name']  # Assumes the column name in the CSV is 'procedure_name'
            
            # Insert into MedicalProcedures table
            cursor.execute("""
                INSERT INTO MedicalProcedures (procedure_name) 
                VALUES (%s)
                ON DUPLICATE KEY UPDATE procedure_name = VALUES(procedure_name)
            """, (procedure_name,))
        
        db.commit()
        print("Medical procedures loaded successfully from CSV!")

# Load the data from the CSV
csv_file = r'datasets\tests.csv'  # Path to your CSV file
load_medical_procedures_from_csv(csv_file)

# Close the connection
cursor.close()
db.close()

