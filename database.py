import mysql.connector 
conn = mysql.connector.connect( 
    host="localhost", 
    user="root", 
    password="Team3@123", 
    database="bank_db" 
) 
cursor = conn.cursor() 