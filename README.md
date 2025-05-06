This guide provides steps to run and execute the HealthDB project

## Prerequisites

- Python environment (venv)
- Gemini 2.0 moddel API key
- MySQL connection

## Setup Instructions

1) If the code is running from scratch, meaning tables do not exist, Execute the SQL queries in the create_tables.sql file. This would create all the tables necessary for the code.

2) Once the tables are created, we need to add data into the static tables. For that, make sure first that the environment is setup by running venv\Scripts\activate command.

3) Once the venv is activated, run the python files diseasesymptoms.py, diseasevaccine.py, medicalprocedures.py. This would load the datasets into the tables created in Step 1

4) After that, insert your Gemini 2.0 API key in gemini_test.py if you want to test whether the model is running. If sure, skip to Step 5

5) The files setup.py, healthdb.py, healthdb2.py are earlier versions of code which work but are not efficient. Run healthdb3.py using the command streamlit run healthdb3.py (After inserting the Gemini key ofc)

# There are a set of queries at the end of healthdb2.py which can be copied or used as reference while executing the program. 

### Thank you ###