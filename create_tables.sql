USE HealthDB;

CREATE TABLE IF NOT EXISTS Patients (
  patient_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  age INT,
  gender VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS Symptoms (
  symptom_id INT AUTO_INCREMENT PRIMARY KEY,
  symptom VARCHAR(100) UNIQUE
);

CREATE TABLE IF NOT EXISTS Diseases (
  disease_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) UNIQUE
);

#Bridge table
CREATE TABLE IF NOT EXISTS DiseaseSymptoms (
  disease_id INT,
  symptom_id INT,
  FOREIGN KEY (disease_id) REFERENCES Diseases(disease_id),
  FOREIGN KEY (symptom_id) REFERENCES Symptoms(symptom_id)
);

CREATE TABLE IF NOT EXISTS Immunizations (
  vaccine_name VARCHAR(100) PRIMARY KEY,
  virus VARCHAR(100)
) ENGINE = InnoDB;

#Bridge table
CREATE TABLE IF NOT EXISTS DiseaseVaccines (
  disease_id INT,
  vaccine_name VARCHAR(100),
  FOREIGN KEY (disease_id) REFERENCES Diseases(disease_id)
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS MedicalProcedures (
  procedure_id INT AUTO_INCREMENT PRIMARY KEY,
  procedure_name VARCHAR(255) UNIQUE
);


CREATE TABLE IF NOT EXISTS PatientDetails (
  patient_id INT,
  disease_id INT,
  symptom_id INT,
  procedure_id INT,
  vacccine_name VARCHAR(100),
  FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
  FOREIGN KEY (disease_id) REFERENCES Diseases(disease_id),
  FOREIGN KEY (symptom_id) REFERENCES Symptoms(symptom_id),
  FOREIGN KEY (procedure_id) REFERENCES MedicalProcedures(procedure_id)
)

ALTER TABLE Patients ADD UNIQUE(name, age, gender);
--ALTER TABLE PatientDetails ADD UNIQUE(patient_id, disease_id, symptom_id, procedure_id, vacccine_name);

CREATE TABLE PatientDiseases (
    patient_id INT,
    disease_id INT,
    PRIMARY KEY (patient_id, disease_id),
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (disease_id) REFERENCES Diseases(disease_id)
);

ALTER TABLE PatientDetails 
ADD COLUMN symptoms JSON,  -- Store symptom IDs as array
ADD COLUMN procedures JSON;