from configparser import ConfigParser
import os

def config(filename='database.ini', section='postgresql'):
    #percorso di filename
    thisfolder = os.path.dirname(os.path.abspath(__file__))
    inifile = os.path.join(thisfolder, filename)
    # crea un parser
    parser = ConfigParser()
    # legge il file di configurazione
    parser.read(inifile)
    # ottiene sezione, postgresql di default
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Sezione {0} non trovata nel file {1}'.format(section, filename))
    return db

