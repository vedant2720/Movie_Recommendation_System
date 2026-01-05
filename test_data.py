import pandas as pd
import sqlite3

conn = sqlite3.connect('../recommender_system.db')
cursor = conn.cursor()

df_old = pd.read_csv("zee-users.dat",sep="::",engine="python",encoding="latin-1")

# 2. Define the occupation mapping (from your previous step)
occupation_map = {
    0: "other", 1: "academic_educator", 2: "artist", 3: "clerical_admin",
    4: "college_grad_student", 5: "customer_service", 6: "doctor",
    7: "engineer", 8: "farmer", 9: "homemaker", 10: "K12_student",
    11: "lawyer", 12: "programmer", 13: "retired", 14: "sales_marketing",
    15: "scientist", 16: "self_employed", 17: "technician",
    18: "tradesman", 19: "unemployed", 20: "writer"
}

# 3. Transform the data to match the NEW schema
df_new = pd.DataFrame()

# Map existing columns
df_new['user_id'] = df_old['UserID']
df_new['gender'] = df_old['Gender'].map({'F': 0, 'M': 1}) # Convert to Integer
df_new['age'] = df_old['Age']
df_new['occupation'] = df_old['Occupation'].map(occupation_map) # Convert Code to Text

# Generate REQUIRED placeholder columns for the new schema
df_new['username'] = "user_" + df_old['UserID'].astype(str)
df_new['email'] = df_new['username'] + "@example.com"
df_new['password'] = "default_password_123" # In production, use hashed passwords

# 4. Insert into SQLite
conn = sqlite3.connect('recommender_system.db')

# Ensure the table is created first
conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        gender INTEGER NOT NULL,
        age INTEGER NOT NULL,
        occupation TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
''')

# Insert the transformed DataFrame
# We use 'append' because the table already exists. 
# 'index=False' prevents Pandas from adding its own index column.
df_new.to_sql('users', conn, if_exists='append', index=False)

conn.close()

