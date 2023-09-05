import sqlite3

def create_players_table():
    # Create a connection to the database and a cursor inside the function
    conn = sqlite3.connect('tournament.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT UNIQUE,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            matches_played INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0  -- New field for points
        )
    ''')
    conn.commit()
    
    # Close the connection after the operation
    conn.close()




def insert_player(user_id, username):
    try:
        # Crear una conexión a la base de datos y un cursor dentro de la función
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO players (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        
        # Cerrar la conexión después de la operación
        conn.close()
        
        return True
    except sqlite3.IntegrityError:
        # El usuario ya existe en la base de datos
        return False

def delete_player(user_id):
    try:
        # Crear una conexión a la base de datos y un cursor dentro de la función
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM players WHERE user_id = ?', (user_id,))
        conn.commit()

        # Cerrar la conexión después de la operación
        conn.close()
    except sqlite3.IntegrityError:
        # Manejar el error de integridad si es necesario
        pass

def get_user_id(username):
    try:
        # Crear una conexión a la base de datos y un cursor dentro de la función
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute('SELECT user_id FROM players WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
        else:
            user_id = None

        # Cerrar la conexión después de la operación
        conn.close()

        return user_id
    except sqlite3.IntegrityError:
        # Manejar el error de integridad si es necesario
        pass

def increment_wins(user_id):
    try:
        # Crear una conexión a la base de datos y un cursor dentro de la función
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE players
            SET wins = wins + 1,
                points = points + 1  -- Incrementa los puntos por una victoria
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

        # Cerrar la conexión después de la operación
        conn.close()
    except sqlite3.IntegrityError:
        # Manejar el error de integridad si es necesario
        pass

def increment_matches_played(user_id):
    try:
        # Crear una conexión a la base de datos y un cursor dentro de la función
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE players
            SET matches_played = matches_played + 1,
                points = points + 1  -- Incrementa los puntos por una partida jugada
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

        # Cerrar la conexión después de la operación
        conn.close()
    except sqlite3.IntegrityError:
        # Manejar el error de integridad si es necesario
        pass

def increment_losses(user_id):
    try:
        # Crear una conexión a la base de datos y un cursor dentro de la función
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE players
            SET losses = losses + 1
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

        # Cerrar la conexión después de la operación
        conn.close()
    except sqlite3.IntegrityError:
        # Manejar el error de integridad si es necesario
        pass
    

    
    
def get_leaderboard(cursor, limit=5):
    cursor.execute('''
        SELECT username, wins, losses, 
            CASE
                WHEN matches_played = 0 THEN 0.0
                ELSE CAST(wins AS REAL) / matches_played
            END AS win_percentage
        FROM players
        ORDER BY points DESC
        LIMIT ?
    ''', (limit,))
    leaderboard = cursor.fetchall()
    return leaderboard


