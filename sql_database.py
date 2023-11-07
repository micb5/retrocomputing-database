import psycopg2
from config import config

def connetti():
    """ Si connette al server del database di PostgreSQL """
    conn = None
    try:
        # legge i parametri di connessione
        params = config()

        # si connette al server di PostgreSQL
        print('Connessione al database di PostgreSQL in corso...')
        conn = psycopg2.connect(**params)
    
    except:
        print('Errore di connessione')

    # restituisce la connessione
    return conn


def crea_database(): 
    """ Crea le tabelle 'Manufacturer', 'Model', 'Image' e 'Documentation' nel database, se non sono già presenti"""

    # ottiene la connessione al database
    conn=connetti()
    # crea un cursore
    cursor = conn.cursor()

    # crea tabella Manufacturer
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS Manufacturer (
                       Brand VARCHAR(70) NOT NULL, 
                       Alternative_name VARCHAR(200), 
                       Origin VARCHAR(100), 
                       PRIMARY KEY(Brand));""") 
        conn.commit()
        print("Tabella Manufacturer creata")

    except:
        print('Errore creazione Manufacturer')

    # crea tabella Model
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS Model (
                       Name VARCHAR(70) NOT NULL,
                       Manufacturer VARCHAR(70) NOT NULL,
                       Year VARCHAR(100),
                       Ram VARCHAR(350),
                       Rom VARCHAR(300),
                       CPU VARCHAR(250),
                       Operative_System VARCHAR(270),
                       Display_or_Graphics VARCHAR(400),
                       Text VARCHAR(200),
                       Sound VARCHAR(200),
                       Storage VARCHAR(300),
                       Ports VARCHAR(400),
                       Price VARCHAR(20),
                       Notes TEXT,
                       PRIMARY KEY(Name, Manufacturer),
                       FOREIGN KEY(Manufacturer) REFERENCES Manufacturer(Brand));""") 
        conn.commit()
        print("Tabella Model creata")

    except:
        print('Errore creazione Model')

    # crea tabella Image
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS Image(
                       URL VARCHAR(200) NOT NULL,
                       Model VARCHAR(70) NOT NULL,
                       Manufacturer VARCHAR(70) NOT NULL,
                       Caption VARCHAR(400),
                       PRIMARY KEY (URL),
                       FOREIGN KEY (Model, Manufacturer) REFERENCES Model(Name, Manufacturer));""") 
        conn.commit()
        print("Tabella Image creata")

    except:
        print('Errore creazione Image')

    # crea tabella Documentation
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS Documentation(
                       URL VARCHAR(200) NOT NULL,
                       Model VARCHAR(70) NOT NULL,
                       Manufacturer VARCHAR(70) NOT NULL,
                       Description VARCHAR(400),
                       PRIMARY KEY (URL),
                       FOREIGN KEY (Model, Manufacturer) REFERENCES Model(Name, Manufacturer));""") 
        conn.commit()
        print("Tabella Documentation creata")

    except:
        print('Errore creazione Documentation')
    conn.close()



"""Esecuzione del file"""
if __name__ == "__main__":
    crea_database()