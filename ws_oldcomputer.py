import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
from sql_database import connetti


def get_gallery(table, name, brand):
    """Ricava l'url e la didascalia delle immagini presenti nella gallery, inserendoli poi nel database"""
    cursor = conn.cursor()
    base= "http://oldcomputer.info/"
    suffix= "&spgmPic=0#spgmPicture"
    # cerca la pagina della gallery
    if name=="520STm":
        gallery_url = table.findAll('a', href=re.compile('gallery'))[1]['href']
    elif name=="1040STf":
        gallery_url=table.findAll('a', href=re.compile('gallery'))[0]['href']
    else:
        try:
            gallery_url = table.find('a', href=re.compile('gallery'))['href']
        except:
            # se non è presente, esce
            return
    #ricava url relativo alla prima pagina della gallery
    next_image= urljoin(base, gallery_url.replace("p=","spgmGal=")) + suffix
    #per ogni pagina della gallery:
    while next_image:
        #richiede il contenuto della pagina
        res = requests.get(next_image)
        page = BeautifulSoup(res.content, 'html.parser')
        #cerca l'url dell'immagine
        image_table=page.find('table', attrs={'class':'table-picture'})
        image_url = base + image_table.find('img',attrs={'id':'picture'}).get('src')
        #cerca la didascalia dell'immagine
        try:
            caption = image_table.find('td',attrs={'id':'picture-caption'}).text
            caption=caption.replace("\n","").replace("\t"," ")
            if caption.isspace() or caption=="":
                caption=None
        except:
            caption = None
        # inserisce le istanze nel database
        cursor.execute(cursor.mogrify("INSERT INTO Image (URL, Model, Manufacturer, Caption) VALUES (%s,%s,%s,%s) ON CONFLICT (URL) DO NOTHING ", (image_url, name, brand, caption))) 
        #cerca pagina successiva della gallery
        try:
            next_image= base + page.find('img', attrs={'class':'img-picture-next'}).parent.get('href')
        except AttributeError:
            next_image=""


def get_documents(url, name, brand):
    """Ricava l'url e la descrizione della documentazione presente nella pagina data in ingresso, 
    inserisce le istanze nel database"""
    cursor = conn.cursor()
    #richiede il contenuto della pagina
    page = requests.get(url, timeout =10 ,verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    #cerca tutti i file di estensione .pdf .djv  .djvu
    all_docs = soup.findAll('a', href=re.compile('.pdf', re.IGNORECASE))  
    all_docs += soup.findAll('a', href=re.compile('.djv'))
    #per ogni elemento trovato, ricava link e descrizione
    if len(all_docs)>0:
        for doc in all_docs:
            if doc['href'] not in [url]:
                doc_url=urljoin(url,doc['href'])
            else:
                doc_url=doc['href']
            description= doc.text.replace(doc_url,"").replace(doc_url.replace("http://",""),"").replace("\n","").replace("\t","").strip()
            #per gli elementi non in elenco cerca la descrizione nell'elemento nextSibling
            exclude=["EC-7915", "Scenic D6 333", "PowerEdge SC1425", "Presario CDS510", "Power Macintosh 7220/200", "Power Macintosh G4 450", "PC-8201A", "VPU200"]
            if name not in exclude:
                if doc.parent.name=="p" or doc.parent.name=="font":
                    if doc.nextSibling:
                        description += " " + doc.nextSibling.text.replace("\n","").replace("\t"," ").strip()
            #oppure cerca la descrizione nell'elemento parent   
            if description=="" or description==" " or name=="BBC Micro Model B":
                description = doc.parent.text.replace(doc_url,"").replace("\n","").replace("\t"," ").strip()
            #inserisce le istanze nel database
            cursor.execute(cursor.mogrify("INSERT INTO Documentation (URL, Model, Manufacturer, Description) VALUES (%s,%s,%s,%s) ON CONFLICT (URL) DO NOTHING ", (doc_url, name, brand, description))) 
            
    

def get_value_from_table(soup, parameter):
    """Cerca il parametro nella scheda tecnica, ricava il testo contenuto nell'elemento immediatamente successivo"""
    try:
        value = soup.find("td", string=re.compile(parameter)).find_next_sibling("td").text.replace("\t","")
        if "??" in value:
            value = None
        if "None" in value:
            value = None
        if "Unknown" in value:
            value = None
        if value=="?":
            value = None
    except:
        value = None
    #restituisce il valore
    return value

def get_manufacturer(table, origin):
    """Ricava il nome del produttore, lo corregge, lo inserisce nel database insieme all'origine e al nome alternativo (sempre nullo)"""
    cursor = conn.cursor()
    # cerca manufacturer nella scheda tecnica
    try:
        manufacturer = table.find('td', string=re.compile('Manufacturer')).find_next_sibling('td').text.replace('\t','')
    except:
        #cerca il primo elemento nella scheda
        first_td = table.find('td').find_next_sibling('td').text
        if first_td =="1995":
            manufacturer="Adax"
            origin="Poland"
        else:
            manufacturer="Unknown"
    # corregge il nome  del produttore affinchè sia conforme ai nomi presenti nel database
    if "Mattel" in manufacturer:
        word="Mattel Electronics"
    elif "Robotron" in manufacturer or "Robotron," in manufacturer:
        word="Robotron"
    elif "Apple" in manufacturer:
        word="Apple Computer"
    elif "Jumptec (mainboard)" in manufacturer:
        word="Jumptec / Cecomm"
    elif "Basis" in manufacturer:
        word="Basis Microcomputer"
    elif "Commodore"  in manufacturer:
        word = "Commodore Business Machines"
    elif "Timex " in manufacturer:
        word = "Timex Computer"
    elif "Elwro" in manufacturer:
        word="Elwro Electronic"
    elif "Philips" in manufacturer:
        word="Philips Electronics"
    elif "Alcatel" in manufacturer:
        word="Alcatel"
    elif "Amstrad" in manufacturer and "Schneider"in manufacturer:
        word="Schneider / Amstrad"
    elif "Elektronska" in manufacturer:
        word="Ei NIS"
    elif "Wyse" in manufacturer:
        word="Wyse Technology"
    elif "Sanyo" in manufacturer:
        word="Sanyo Business Systems"
    elif "ALR" in manufacturer:
        word="Advanced Logic Research"
    elif "Elektronska" in manufacturer:
        word="Ei NIS"
    elif "Mera-Elzab" in manufacturer:
        word="Mera-Elzab"
    elif "Advanced Logic" in manufacturer:
        word="Advanced Logic Research"
    else:
        word=manufacturer
    # elimina le parole in elenco dal nome del produttore
    x=["Ltd.", "Corp", "Skalica", "Research", "?", "-", "??"]
    if "Hewlett" not in word and "Mera-Elzab" not in word and "Advanced Logic" not in word:
        for item in x:
            if item in word:
                word=word.replace(item, " ").strip()
    #attributi brand, nome alternativo e origine
    brand=word.strip()
    alt_name = None
    if origin:
        origin=origin.replace("?","")
    #inserimento delle istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Manufacturer (Brand, Alternative_name, Origin) VALUES (%s,%s,%s) ON CONFLICT (Brand) DO UPDATE SET Origin=COALESCE(Manufacturer.Origin, %s) ", (brand, alt_name, origin, origin)))
    return brand


def correct_name_OC(manufacturer, name):
    """Corregge il nome del modello per renderlo uniforme ai dati presenti nel database"""

    if "Atari" in manufacturer:
        name=name.replace("Portfolio","PortFolio").replace("65XE","65 XE").replace("800XE","800 XE").replace("Atari ","")
    if "IBM" in manufacturer:
        name=name.replace("IBM ","").replace("PS","Personal System")
    if "Elwro" in manufacturer and "Elwro" not in name:
        name="Elwro "+name
    if "Epson" in manufacturer:
        name=name.replace("-","")
    if "Tandy" in manufacturer:
        name=name.replace("1000EX","1000 EX")
    if "Amstrad" in manufacturer:
        name=name.replace("CPC-","CPC ").replace("PCW","PCW-")
    if "Basis" in manufacturer:
        name=name.replace("BASIS","Basis")
    if "Commodore" in manufacturer:
        name=name.replace("Commodore ","").replace("VIC-20","VIC 20")
    if "Ei NIS" in manufacturer:
        name=name.replace("PECOM","Pecom")
    if "Philips" in manufacturer:
        name=name.replace("VG","VG-")
    if "Robotron" in manufacturer:
        name=name.replace("Robotron ","").replace("KC", "KC ")
    if "Sharp" in manufacturer:
        name=name.replace("MZ-","MZ")
    if "Spectravideo" in manufacturer:
        name=name.replace("Spectravideo XPress","SVI 738 X'Press")
    if "Texas" in manufacturer:
        name=name.replace("TI-","TI ")
    if "Timex" in manufacturer:
        name=name.replace("Timex Sinclair ", "TS-").replace("Timex TC ", "TC-")
    if "Apple" in manufacturer:
        name=name.replace("PowerBcook 165c","Power Book 165C")
    # restituisce il nome corretto
    return name.strip()


def get_data_8bit(link, name):
    """Ricava i dati tecnici dalla scheda di tipo "8bit", li inserisce nel database, 
    invoca le funzioni che ricavano produttore, immagini e documentazione"""
    cursor = conn.cursor()
    #richiede il contenuto della pagina
    page = requests.get(link, timeout=50)
    soup = BeautifulSoup(page.content, "html.parser")
    # cerca la scheda tecnica 
    table8=["CPC-6128", "Amiga 600", "65XE", "130XE", "800XE", "16 / PLUS 4", "ZX Spectrum +", "PCW9512", "Didaktik M"]
    if name=="BBC Master Compact":
        table = soup.find("table", attrs={"id": "table26"})
    elif name in table8:
        table = soup.find("table", attrs={"id": "table8"})
    elif name=="Timex Sinclair 1000":
        table = soup.find("table", attrs={"id": "table14"})
    elif name=="128D":
        table = soup.find("table", attrs={"id": "table10"})
    elif name=="KC85/4":
        table = soup.find("table", attrs={"id": "table2"})
    else:
        table = soup.find("table", attrs={"id": "table1"})
    #ricava origine e produttore
    origin = get_value_from_table(table, 'Origin')
    brand = get_manufacturer(table, origin)
    #corregge il nome del modello
    corrected_name = correct_name_OC(brand, name)
    #dati tecnici
    year = get_value_from_table(table, 'introduction')
    cpu = get_value_from_table(table, 'CPU')
    speed = get_value_from_table(table, 'Speed')
    if speed:
        cpu += " - " + speed
    ram = get_value_from_table(table,'RAM')
    rom = get_value_from_table(table,'ROM')
    os = get_value_from_table(table,'OS:')
    sound = get_value_from_table('Sound', table)
    storage = get_value_from_table('Media', table)
    ports = get_value_from_table('I/O', table)
    #attributi nulli
    notes=None
    price=None
    # ricava "display"
    # separa le infromazioni relative a "testo" e "grafica" dal contenuto di "display"
    # gestendo tutti i casi possibili 
    display = get_value_from_table(table,'Display')
    grafica=''
    if display:
        if "Graphics: " in display:
            testo=display.split("Graphics: ")[0].replace("Text: ", "").replace("\n", "")
            grafica=display.split("Graphics: ")[1]
        elif "Graphic: " in display:
            testo=display.split("Graphic: ")[0].replace("Text: ", "").replace("\n", "")
            grafica=display.split("Graphic: ")[1]
        elif "graphics, " in display:
            grafica=display.split("graphics, ")[0]
            testo=display.split("graphics, ")[1].replace("text", "").replace("\n", "")
        elif "graphics mode, " in display:
            grafica=display.split("graphics mode, ")[0]
            testo=display.split("graphics mode, ")[1]
        elif "Generated" in display:
            testo=display.split("Text: ")[1]
            grafica=display.split("Text: ")[0]
        else:
            if "Text: " in display:
                temp=display.split(". ", 1)
                if len(temp)>1:
                    testo=temp[0].replace("Text: ", "")
                    grafica=temp[1]
                else:
                    testo=display.replace("Text: ", "")
            elif "text/graphics" in display:
                testo=display.split(". ")[0]
                grafica=display
            elif "Text mode" in display:
                testo=display.split("graphics", 2)[2]
                grafica= display.replace(testo, "")
                testo=testo.replace("Text ","")
            else:
                if "Text" in display or "mode" in display:
                    testo= display
                else: 
                    grafica= display
                    testo= None           
    else:
        testo = None
    # ricava "colors" e aggiunge il suo contenuto a "grafica"
    colors = get_value_from_table(table,'Colors')
    if colors:
        if grafica:
            grafica += "\n" + "Colors: " + colors
        else:
            grafica = "Colors: " + colors
    if not grafica:
        grafica = None
    #inserimento istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO UPDATE SET (Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports) = (COALESCE(Model.Year, %s), COALESCE(Model.Ram, %s), COALESCE(Model.Rom, %s), COALESCE(Model.CPU, %s), COALESCE(Model.Operative_System, %s), COALESCE(Model.Display_or_Graphics, %s), COALESCE(Model.Text, %s), COALESCE(Model.Sound, %s), COALESCE(Model.Storage, %s), COALESCE(Model.Ports, %s))", (corrected_name, brand, year, ram, rom, cpu, os, grafica, testo, sound, storage, ports, price, notes, year, ram, rom, cpu, os, grafica, testo, sound, storage, ports )))
    # ricava immagini
    get_gallery(table, corrected_name, brand)
    # ricava documentazione dalla pagina corrente
    get_documents(link, corrected_name, brand)
    #cerca pagina dell'archivio 
    try:
        archive_page = table.find('a', href=re.compile('keep')).get('href')
    except:
        archive_page = None
    if archive_page:
        archive_page=urljoin(link,archive_page)
        #ricava documentazione dall'archivio
        get_documents(archive_page, corrected_name, brand)
    conn.commit()

def get_data_apple(link, name):
    """Ricava i dati tecnici dalla scheda di tipo "apple", li inserisce nel database, 
    invoca le funzioni che ricavano produttore, immagini e documentazione"""
    cursor = conn.cursor()
    #richiede contenuto della pagina
    page = requests.get(link, timeout=50)
    soup = BeautifulSoup(page.content, "html.parser")
    #cerca la scheda tecnica
    table = soup.find("table", attrs={"id": "table1"})
    brand = "Apple Computer"
    #corregge il nome del modello
    corrected_name=correct_name_OC(brand, name)
    #dati tecnici
    year = get_value_from_table(table,'Year')
    cpu = get_value_from_table(table,'CPU')
    sound = get_value_from_table(table,'Sound')
    ports = get_value_from_table(table,'Connectors')
    os = get_value_from_table(table,'OS:')
    #attributi nulli
    rom =  None
    text = None
    price = None
    notes = None
    #per l'attributo ram unisce il contenuto degli elementi "RAM", "Max Ram" e "Ram Type"
    ram = get_value_from_table(table, 'RAM')
    ram_max = get_value_from_table(table,'Max')
    ram_type = get_value_from_table(table,'RAM Type')
    if ram:
        if ram_max:
            ram += "\nMax. RAM: " + ram_max
        if ram_type:
            ram += "\nRAM Type: " + ram_type
    # per l'attributo grafica unisce il contenuto di display e graphics
    display = get_value_from_table(table,'Display')
    graphics = get_value_from_table(table,'Graphics')
    grafica=""
    if display:
        grafica += "Dispaly: " + display
    if graphics:
        grafica += "\nGraphics: " + graphics
    # per l'attributo storage unisce il contenuto di hd, floppy e other_drives
    hd = get_value_from_table(table,'Hard disk')
    floppy = get_value_from_table(table,'Floppy')
    other_drives = get_value_from_table(table,'Other drives')
    storage= ""
    if hd:
        storage += "Hard disk: " + hd + "\n"
    if floppy:
        storage += "Floppy drives: " + floppy +"\n"
    if other_drives:
        storage += "Other drives: " + other_drives
    if storage=="":
        storage = None
    # inserimento istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO UPDATE SET (Year, Ram, CPU, Operative_System, Display_or_Graphics, Sound, Storage, Ports) = (COALESCE(Model.Year, %s), COALESCE(Model.Ram, %s), COALESCE(Model.CPU, %s), COALESCE(Model.Operative_System, %s), COALESCE(Model.Display_or_Graphics, %s), COALESCE(Model.Sound, %s), COALESCE(Model.Storage, %s), COALESCE(Model.Ports, %s))", (corrected_name, brand, year, ram, rom, cpu, os, grafica, text, sound, storage, ports, price, notes, year, ram, cpu, os, grafica, sound, storage, ports )))  
    # ricava immagini
    get_gallery(table, corrected_name, brand)  
    # ricava documentazione dalla pagina corrente
    get_documents(link, corrected_name, brand)
    # cerca pagina dell'archivio
    try:
        archive_page = table.find('a', href=re.compile('keep')).get('href')
    except:
        archive_page = None
    if archive_page:
        #ricava documentazione dall'archivio
        get_documents(archive_page, corrected_name, brand)
    conn.commit()

def get_data_pc(link, name):
    """Ricava i dati tecnici dalla scheda del modello di tipo "pc", li inserisce nel database, 
    invoca le funzioni che ricavano produttore, immagini e documentazione"""
    cursor = conn.cursor()
    
    # richiede contenuto della pagina
    page = requests.get(link, timeout=50)
    soup = BeautifulSoup(page.content, "html.parser")

    # cerca la scheda
    table = soup.find("table", attrs={"id": "table1"})
    
    # ricava produttore
    origin = get_value_from_table(table, 'Origin')
    brand = get_manufacturer(table, origin)
    
    # corregge il nome del modello
    corrected_name = correct_name_OC(brand, name)

    # dati tecnici
    year = get_value_from_table(table,'introduction')
    cpu = get_value_from_table(table,'CPU')
    speed = get_value_from_table(table,'Speed')
    if speed:
        cpu += " - " + speed

    ram = get_value_from_table(table,'RAM')
    rom = get_value_from_table(table,'ROM')
    os = get_value_from_table(table,'Operating')

    display = get_value_from_table(table,'Graphics')
    sound = get_value_from_table(table,'Sound')
    
    # attributi nulli
    text = None
    ports = None
    price = None
    notes = None
  
    # ricava l'attributo storage unendo il contenuto di hd, floppy e other_cards
    hd = get_value_from_table(table,'Hard disk')
    floppy = get_value_from_table(table,'Floppy')
    other_cards = get_value_from_table(table,'Other cards')
    storage= ""
    if hd:
        storage +="Hard disk: " + hd + "\n"
    if floppy:
        storage+="Floppy/removable drives: " + floppy + "\n"
    if other_cards:
        storage += "Other cards: " + other_cards
    if storage=="":
        storage = None

    #inserimento istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO UPDATE SET (Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Sound, Storage) = (COALESCE(Model.Year, %s), COALESCE(Model.Ram, %s), COALESCE(Model.Rom, %s), COALESCE(Model.CPU, %s), COALESCE(Model.Operative_System, %s), COALESCE(Model.Display_or_Graphics, %s), COALESCE(Model.Sound, %s), COALESCE(Model.Storage, %s))", (corrected_name, brand, year, ram, rom, cpu, os, display, text, sound, storage, ports, price, notes, year, ram, rom, cpu, os, display, sound, storage )))    
    
    # ricava immagini
    get_gallery(table, corrected_name, brand)

    # ricava documentazione dalla pagina corrente
    get_documents(link, corrected_name, brand)
    
    #cerca pagina dell'archivio 
    try:
        archive_page = table.find('a', href=re.compile('keep')).get('href')
    except:
        archive_page = None
    if archive_page:
        #ricava documentazione dalla pagina dell'archivio
        get_documents(archive_page, corrected_name, brand)
    conn.commit()

def get_data_portables(link, name):
    """Ricava i dati dalla scheda del modello di tipo "portables", li inserisce nel database, 
    invoca le funzioni che ricavano produttore, immagini e documentazione"""

    cursor = conn.cursor()

    # richiede la pagina del modello
    page = requests.get(link, timeout=50)
    soup = BeautifulSoup(page.content, "html.parser")
    # cerca la scheda tecnica
    table = soup.find("table", attrs={"id": "table1"})
    
    # ricava produttore
    origin = get_value_from_table(soup,'Origin')
    brand = get_manufacturer(table, origin)

    # corregge il nome del modello
    corrected_name = correct_name_OC(brand, name)

    # dati tecnici
    year = get_value_from_table(table,'introduction')
    cpu = get_value_from_table(table,'CPU')

    ram = get_value_from_table(table,'RAM')
    os = get_value_from_table(table,'OS:')
    if os and os[0]=="\n":
        os=os.replace("\n","",1)

    display = get_value_from_table(table,'Graphics')
    ports = get_value_from_table(table,'I/O')
    sound = get_value_from_table(table,'Sound')
    
    # attributi nulli
    text = None
    rom = None
    price = None
    notes = None
    

    # ricava l'attributo storage unendo il contenuto di hd, floppy e other_media
    hd = get_value_from_table(table,'Hard disk')
    floppy = get_value_from_table(table,'Floppy')
    other_media = get_value_from_table(table,'Other media')
    storage= ""
    if hd:
        storage +="Hard Disk: " + hd + "\n"
    if floppy:
        storage+="Floppy Disk: " + floppy + "\n"
    if other_media:
        storage += "Other media: " + other_media
    if storage.isspace():
        storage = None

      
    # inserisce le istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO UPDATE SET (Year, Ram, CPU, Operative_System, Display_or_Graphics, Sound, Storage) = (COALESCE(Model.Year, %s), COALESCE(Model.Ram, %s), COALESCE(Model.CPU, %s), COALESCE(Model.Operative_System, %s), COALESCE(Model.Display_or_Graphics, %s), COALESCE(Model.Sound, %s), COALESCE(Model.Storage, %s))", (corrected_name, brand, year, ram, rom, cpu, os, display, text, sound, storage, ports, price, notes, year, ram, cpu, os, display, sound, storage )))
    
    # ricava immagini
    get_gallery(table, corrected_name, brand)

    # ricava documentazione dalla pagina corrente
    get_documents(link, corrected_name, brand)
    
    #cerca pagina dell'archivio
    try:
        archive_page = table.find('a', href=re.compile('keep')).get('href')
    except:
        archive_page = None
    if archive_page:
        # ricava documentazione dalla pagina archivio
        get_documents(archive_page, corrected_name, brand)
    conn.commit()

def get_data_terminal(link, name, origin):
    """Ricava i dati dalla scheda del modello di tipo "terminal", li inserisce nel database, 
    invoca le funzioni che ricavano produttore, immagini e documentazione"""

    cursor = conn.cursor()
    # richiede la pagina del modello
    page = requests.get(link, timeout=50)
    soup = BeautifulSoup(page.content, "html.parser")

    # cerca la scheda tecnica
    table = soup.find("table", attrs={"id": "table1"})
    
    # ricava produttore
    brand = get_manufacturer(table, origin)

    # corregge il nome del modello
    corrected_name = correct_name_OC(brand, name)

    # dati tecnici
    year = get_value_from_table(table, 'introduction')
    cpu = get_value_from_table(table,'CPU')
    display = get_value_from_table(table,'Display')
    storage = get_value_from_table(table, 'Memory')

    #attributi nulli
    ram = None
    rom = None
    os = None
    sound = None
    text = None
    notes = None
    price = None

    # per l'attributo ports unisce il contenuto di main_port e additional_ports
    main_port = get_value_from_table(table,'Main')
    additional_ports = get_value_from_table(table,'Additional')
    ports = ""
    if main_port:
        ports += main_port + "\n"
    elif additional_ports:
        ports += additional_ports + "\n"
    else:
        ports = None
    
    # inserisce le istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO UPDATE SET (Year, CPU, Display_or_Graphics, Storage, Ports) = (COALESCE(Model.Year, %s), COALESCE(Model.CPU, %s), COALESCE(Model.Display_or_Graphics, %s), COALESCE(Model.Storage, %s), COALESCE(Model.Ports, %s))", (corrected_name, brand, year, ram, rom, cpu, os, display, text, sound, storage, ports, price, notes, year, cpu, display, storage, ports)))
    
    # ricava immagini
    get_gallery(table, corrected_name, brand)

    # ricava documentazione dalla pagina corrente
    get_documents(link, corrected_name, brand)
    
    # cerca pagina dell'archivio 
    try:
        archive_page = table.find('a', href=re.compile('keep')).get('href')
    except:
        archive_page = None
    # ricava documentazione dalla pagina archivio
    if archive_page:
        get_documents(archive_page, corrected_name, brand)
    conn.commit()



def get_column_from_table(url, n):
    """Dalla tabella presente nella pagina data, ricava gli elementi dalla colonna numero n indicata in ingresso"""
    # richiede contenuto della pagina
    response = requests.get(url, timeout =50 ,verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    # cerca tabella
    table = soup.find('table', attrs={'id': 'table3'})
    the_list=[]
    #per ogni elemento della colonna ennesima, ricava i valori link e testo associato
    for i in table.select('td:nth-of-type({0}) a'.format(n)):
        # aggiunge alla lista la coppia di valori: (link, testo)
        the_list.append([url + i['href'], i.text])
    # restituisce la lista
    return the_list
        



def main():
    print("Inizio scraping di oldcomputer.info")
    url_sections = ["http://oldcomputer.info/8bit/", "http://oldcomputer.info/apple/", "http://oldcomputer.info/pc/", "http://oldcomputer.info/portables/", "http://oldcomputer.info/terminal/"]
    #per ogni pagina in url_sections ricava l'elenco dei modelli e i relativi link, tramite la funzione get_column_from_table
    #per la pagina terminal ricava anche l'elenco dei luoghi di provenienza
    for url in url_sections:
        if "terminal" in url:
            models = get_column_from_table(url, 2)
            location = get_column_from_table(url,3)
            print("Recupero elenco modelli Terminal...")
        elif "apple" in url:
            models = get_column_from_table(url, 1)
            print("Recupero elenco modelli Apple...")
        else:
            models = get_column_from_table(url, 2)
            if "portables" in url:
                print("Recupero elenco modelli Portables...")
            elif "pc" in url:
                print("Recupero elenco modelli PCs...")
            else:
                print("Recupero elenco modelli 8bit...")
        #visita ciascun modello nell'elenco models
        count = 0
        total = len(models)
        while models:
            #per ogni modello
            for i in models:
                #salta casi in cui il nome contiene "?" o "replica"
                if  "?" in i[1] or "replica" in i[1]:
                    models.remove(i)
                    continue
                #ottiene il nome dai valori di i, elimina il contenuto tra parentesi
                exact_name = i[1].split(" (")[0].strip()
                #invoca la corrispondente funzione per il recupero dati
                try:
                    if exact_name=="ANG-3001":
                        get_data_8bit(link = i[0], name = exact_name)
                    if "terminal" in url:
                        index=models.index(i)
                        loc=location[index]
                        get_data_terminal(link = i[0], name = exact_name, origin = loc[1])
                    elif "portables" in url:
                        get_data_portables(link = i[0], name = exact_name)
                    elif "apple" in url:
                        get_data_apple(link = i[0], name = exact_name)
                    elif "pc" in url:
                        get_data_pc(link = i[0], name = exact_name)
                    elif "8bit" in url:
                        get_data_8bit(link = i[0], name = exact_name)    
                    # rimuove il modello dall'elenco una volta visitato
                    models.remove(i)
                    count += 1
                except requests.exceptions.ConnectTimeout as e:
                    print(e)
                print("Fatto {0} su {1}".format(count,total) )
                time.sleep(2)
    print("Fine scraping di oldcomputer.info")
    
    


"""Esecuzione dello script"""
#connessione al database PostgreSQL 
conn = connetti()
#esegue main
main()
#chiusura connessione database 
conn.close()
print("All done!")

