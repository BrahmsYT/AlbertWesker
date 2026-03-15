import sqlite3
conn = sqlite3.connect('scanner.db')
conn.row_factory = sqlite3.Row
users = conn.execute('SELECT * FROM users').fetchall()
print(f'Users in database: {len(users)}')
for u in users:
    print(f'  Username: {u["username"]}, Role: {u["role"]}')
conn.close()
