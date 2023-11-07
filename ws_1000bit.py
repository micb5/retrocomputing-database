from bs4 import BeautifulSoup 
import requests
import re
from sql_database import connetti
from sql_database import crea_database


def get_manufacturer(manufacturer):
    """Ricava brand, nome alternativo e origine da manufacturer, e li inserisce nel database"""
    cursor = conn.cursor()
    #crea lista di tutti i termini di manufacturer che si trovano tra parentesi 
    terms_in_parentheses=re.findall(r'\((.*?)\)', manufacturer)
    # ricava il nome principale, eliminando tutti i termini tra parentesi
    # Apple caso a parte
    if "Apple" in manufacturer:
        for term in terms_in_parentheses:
            manufacturer = manufacturer.replace("("+term+")","")
    else:
        for term in terms_in_parentheses:
            manufacturer = manufacturer.replace(term,"")
    # rimuove le parole in elenco dal nome principale
    removal_list = ["Corp.", "Inc.", "Ltd.", "Ltda.","Limited", "s.p.a.", "Co.", "Inc", "s.r.l.", "ltd", "Ltda", "Lmtd.", "SpA", "snc", "srl", "S.p.A.", "GmbH", "LLC", "S.A.", "Ltd", ")", "(", ","]
    for word in removal_list:
        manufacturer = manufacturer.replace(word, "")
    #ricava origin dall'ultimo termine della lista di termini tra parentesi e lo elimina 
    if len(terms_in_parentheses) > 0:
        origin = terms_in_parentheses[-1].strip()
        del terms_in_parentheses[-1]
        if "(" in origin and ")" not in origin:
            origin+=")"
        if origin.isspace() or origin=="":
            origin=None
    else:
        origin = None      
    # ricava brand 
    # e nome alternativo dalla restante lista di termini tra parentesi
    brand = manufacturer.strip()
    alt_name=""
    if " - " in brand:
        alt_name = brand.split("-")[1].strip()
        brand = brand.split("-")[0].strip()
    if len(terms_in_parentheses)>=1:
        if alt_name:
            alt_name+="\n"+("\n".join(terms_in_parentheses))
        else:
            alt_name=("\n".join(terms_in_parentheses))
    elif not alt_name:
        alt_name = None

    # inserisce le istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Manufacturer (Brand, Alternative_name, Origin) VALUES (%s,%s,%s) ON CONFLICT (Brand) DO NOTHING ", (brand, alt_name, origin)))
    #restituisce brand
    return brand


def get_img(soup, name, brand):
    """Recupera le immagini e le inserisce nel database"""
    cursor = conn.cursor()
    # cerca tab immagini
    photo_container=soup.find(id='tabFoto')
    # cerca tutte le immagini nel tab
    photo_elements=photo_container.findAll('img',attrs={'class':'w3-image'})
    #ricava url di ciascun'immagine  
    base="https://www.1000bit.it"
    caption= None
    if len(photo_elements)>0:
        for photo in photo_elements:
            img=base + photo['src']
            #inserisce le istanze nel database
            cursor.execute(cursor.mogrify("INSERT INTO Image (URL, Model, Manufacturer, Caption) VALUES (%s,%s,%s,%s) ON CONFLICT (URL) DO NOTHING ", (img, name, brand, caption))) 


def get_doc(soup, name, brand):
    """Recupera la documentazione e la inserisce nel database"""
    cursor = conn.cursor()
    # cerca tab manuali
    doc_container=soup.find(id='tabManuali')   
    # cerca tutti i link nel tab
    doc_elements=doc_container.findAll('a', href=True)
    # ricava url e descrizione di ciascun documento
    base="https://www.1000bit.it"
    if len(doc_elements)>0:
        for doc in doc_elements:
            if "support/manuali/" in doc['href']:
                doc_url= base + doc['href']
                doc_text=doc.text
            else:
                doc_url=doc['href']
                doc_text=None
            #inserisce le istanze nel database
            cursor.execute(cursor.mogrify("INSERT INTO Documentation (URL, Model, Manufacturer, Description) VALUES (%s,%s,%s,%s) ON CONFLICT (URL) DO NOTHING ", (doc_url, name, brand, doc_text))) 
                
def get_value_from_table(soup, parameter):
    """Cerca il parametro negli elementi della tabella, restituisce il testo dell'elemento immediatamente successivo"""
    try:
        value = soup.find('td', attrs={'class':'w3-indigo'}, string=re.compile(parameter)).findNext('td').get_text(strip=True)
        if value.isspace() or value=="":
            value=None
    except:
        value = None
    return value


def get_data(soup):
    """Recupera i dati tecnici del modello e li inserisce nel database, 
    invoca le funzioni che ricavano produttore, immagini e documentazione"""
    cursor = conn.cursor()
    name = get_value_from_table(soup,'Name')
    #ricava manufacturer
    manufacturer = get_value_from_table(soup,'Manufacturer')
    brand = get_manufacturer(manufacturer)
    #dati tecnici
    year = get_value_from_table(soup,'Production start')
    ram = get_value_from_table(soup,'RAM')
    rom = get_value_from_table(soup,'ROM')
    cpu = get_value_from_table(soup,'CPU')
    os = get_value_from_table(soup,'Operating')
    text = get_value_from_table(soup,'Text')
    graphics = get_value_from_table(soup,'Graphics')
    sound = get_value_from_table(soup,'Sound')
    storage = get_value_from_table(soup,'Storage')
    price = get_value_from_table(soup,'Price')
    #per l'attributo ports, unisce il contenuto di tutti gli elementi che fanno riferimento a port
    # "Serial port", "Parallel port", 
    all_ports = soup.findAll('td', attrs={'class':'w3-indigo'}, string=re.compile('port'))
    x=[]
    for port in all_ports:
        try:
            port_content = port.findNext('td').get_text(strip=True)
            if port_content:
                x.append(port.text +": "+ port_content)
        except:
            port_content = None
    if len(x) > 0:
        port = "\n".join(x)
    else: 
        port = None
    #per l'attributo notes unisce gli elementi note e configuration 
    note = get_value_from_table(soup,'Note')
    configuration = get_value_from_table(soup,'Configurations')   
    if note:
        if configuration:
            notes= note + "\n" + configuration
        else:
            notes=note
    else:
        notes=None
    # inserisce le istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO NOTHING", (name, brand, year, ram, rom, cpu, os, graphics, text, sound, storage, port, price, notes)))
    # ricava immagini
    get_img(soup, name, brand)       
    # ricava documentazione
    get_doc(soup, name, brand)
    conn.commit()
        

            

        


def main():

    print("Inizio scraping di 1000bit")

    # richiede la versione in inglese del sito
    url_lang = "https://www.1000bit.it/wrapper.asp?l=eng"
    session = requests.Session()
    a = session.get(url_lang)
    # conserva i cookies relativi alla lingua
    cookies=session.cookies.get_dict()

    count=0
    # per ogni pagina nel range
    for i in range(1,2854):
        # richiede la pagina
        url="https://www.1000bit.it/scheda.asp?id={0}".format(str(i))
        page = requests.get(url, cookies=cookies)
        
        # se la pagina reindirizza alla home, si salta
        if page.url == "https://www.1000bit.it/default.asp":
            continue
        else:
            # contenuto della pagina
            soup = BeautifulSoup(page.content, "html.parser")
    
            # ricava i dati
            get_data(soup)
            count+=1
        
        print( "{0} su 2636".format(count))
    print("Fine scraping di 1000bit.it")


"""Esecuzione dello script"""
#creazione del database se non esiste già
crea_database()
#connessione al database PostgreSQL 
conn = connetti()
#esegue main
main()
#chiusura connessione database 
conn.close()