import mysql.connector 
conn = mysql.connector.connect( 
    host="localhost", 
    user="root", 
    password="Team3@123", 
    database="bank_db" 
) 
cursor = conn.cursor() 

# Existing databases may have a short PIN column from the original schema.
# Password hashes need more room than a numeric PIN.
cursor.execute(
    "ALTER TABLE accounts MODIFY COLUMN pin VARCHAR(255) NOT NULL"
)
conn.commit()