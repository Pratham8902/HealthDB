import google.generativeai as genai

genai.configure(api_key="Insert Gemini 2.0 Key here")

model = genai.GenerativeModel("models/gemini-2.0-flash")
response = model.generate_content("Write a SQL query to show all patients from a table named Patients.")
print(response.text.strip())
