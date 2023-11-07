
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from sql_database import connetti




def get_img(driver, url, name, brand):
    """Recupera le immagini dalla pagina data in ingresso, e le inserisce nel database"""
    cursor = conn.cursor()
    val=driver.current_url
    # se url in ingresso non è della pagina principale
    if not url==val:
        # apre la pagina della collezione 
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.url_to_be(url))
        # cerca le immagini nella pagina della collezione, l'attributo caption è sempre null
        caption=None
        img_elements = driver.find_elements(By.XPATH, "//p/img[contains(@src, 'photos')]")
        if len(img_elements) > 0:
            for img in img_elements:
                image = img.get_attribute("src")
                # inserisce le istanze nel database
                cursor.execute(cursor.mogrify("INSERT INTO Image (URL, Model, Manufacturer, Caption) VALUES (%s,%s,%s,%s) ON CONFLICT (URL) DO NOTHING ", (image, name, brand, caption))) 
        else:
            # ritorna alla pagina principale
            driver.back()
            WebDriverWait(driver, 10).until(EC.url_to_be(val))
    # se url in ingresso è della pagina principale:
    if driver.current_url == val:
        # cerca immagini nella pagina, mentre l'attributo caption è sempre null
        caption=None
        img_elements = driver.find_elements(By.XPATH, "//p/img[contains(@src, 'photosbd')]")
        if len(img_elements) > 0:
            for img in img_elements:
                image= img.get_attribute("src")
                # insersce le istanze nel database
                cursor.execute(cursor.mogrify("INSERT INTO Image (URL, Model, Manufacturer, Caption) VALUES (%s,%s,%s,%s) ON CONFLICT (URL) DO NOTHING ", (image, name, brand, caption))) 


def correct_manufacturer(driver, word):
    """Corregge il nome del produttore, dato in ingresso come "word", per renderlo uniforme ai dati presenti nel database """

    # rimuove le parole della lista dal nome del produttore
    removal_list = ["Corp.", "Consumer Electronics plc.", "Computers Co. Ltd.", "Industries Inc.", "& Hachette", "Incorporated", "Microcomputers Ltd.", "International Corporation", "Corporation"]
    removal_list += ["SA", "Electronic Co. Ltd.", "Compagny", "Computing," , "Enterprises Ltd.", "Rundfunkwerke AG", " Research"]
    removal_list += ["Inc.","Ltda.", "Ltd.", "International LTD", "Limited", "s.p.a.", "plc", "Plc" , "Pty", "LTD.", "Co.", "Inc", "s.r.l.", "ltd","Ltd", "Ltda", "Lmtd.", "SpA", "Spa", "snc", "srl", "S.p.A.", "GmbH", "LLC", "S.A.", ",", "."]
    for item in removal_list:
        word = word.replace(item, "").strip()
    # per i produttori in elenco recupera il nome da un altro elemento della pagina
    elenco=["Acorn Computers", "International Telephone and Telegraph", "Micro Instrumentation and Telemetry Systems", "Compaq Computer", "VEB Kombinat Robotron", "ITMC", "International Business Machines", "Matsushita Electric Industrial", "Nippon Electric", "Victor Company of Japan", "Data Application International", "Non-Linear Systems", "Microinformatics and Telecom Company" ]
    if word in elenco:
        word=driver.find_element(By.XPATH, '//td[@class="menu_rapide"]/a[contains(@href,"resultatrechercheconst.php?id=")]//font').text
        if not word:
            word=driver.find_element(By.XPATH, '//td[@class="menu_rapide"]/font/a[contains(@href,"resultatrechercheconst.php?id=")]//font').text       
    # ulteriori correzioni del nome 
    if "Bit" in word or "Kyocera" in word:
        word+= " Corporation"
    elif "Apple" in word:
        word="Apple Computer"
    elif "Compaq" in word:
        word=word.replace("Home ","")
    elif "Exidy" in word:
        word+=" Systems"
    elif "Heath" in word:
        word=word.replace("Company","")
    elif "Goldstar" in word:
        word+= " Technology"
    elif "Otrona" in word:
        word+= " Advanced Systems"
    elif "Jupiter" in word:
        word+= " Ace"
    elif "Victor Technologies" in word:
        word=word.replace("Victor", "Sirius Systems")
    elif "Logabax" in word:
        word=word.replace("Logabax","LogAbax")
    elif "Grid" in word:
        word=word.replace("Grid", "GRiD")
    elif "Hewlett" in word:
        word=word.replace(" ", "-")
    elif "SMT"in word:
        word=word.replace("SMT", "GOUPIL")
    elif "JVC"in word:
        word=word.replace(" - ", "/")
    elif "Zenith" in word:
        word=word.replace("Data System","")
    elif "Tangerine" in word:
        word="Oric Products International"
    elif "Luxor" in word:
        word=word.replace(" AB","")
    elif "Eaca" in word:
        word=word.replace("Eaca","EACA")
    elif "Campers" in word:
        word="Camputers"
    elif "Basic Microcomputer" in word:
        word=word.replace("Basic", "Basis")
    elif "Electronic Design and Studies" in word:
        word="Réalisation et Etudes Electroniques"
    elif "Video Technology" in word:
        word=word.replace("Computers", "")
    elif "Multitech" in word:
        word=word.replace("Industrial","Electronics")
    elif "Indata" in word:
        word="DAI"
    elif "Sord" in word:
        word=word.replace("Systems", "")
    elif "Sanyo" in word:
        word="Sanyo Business Systems"
    elif "IMS Associates" in word:
        word=word.replace("IMS","Ims")

    word=word.strip()
    # restituisce il nome corretto
    return word


def correct_name(name, manufacturer): 
    """Corregge il nome del modello per renderlo uniforme ai dati presenti nel database"""
    if "Acorn" in manufacturer:
        name=name.replace("B+","B Plus")
    if "Amstrad" in manufacturer:
        name=name.replace("PCW ","PCW-").replace("PCW-1","PCW 1").replace("+", " Plus")
    if "Applied Computer Techniques" in manufacturer:
        name=name.replace("Xen", "XEN")
    if "LogAbax" in manufacturer:
        name=name.replace("-"," ")
    if "Luxor" in manufacturer:
        name=name.replace("ABC","ABC ")
    if "Miles Gordon" in manufacturer:
        name=name.replace("SAM ","sam")
    if "Multitech" in manufacturer or "Spectravideo" in manufacturer:
        name=name.replace("-"," ")
    if "Nascom" in manufacturer:
        name=name.replace("1","I").replace("2","II").replace("3","III")
    if "NeXT" in manufacturer:
        name=name.replace("cube", " Cube")
    if "Nec" in manufacturer:
        name=name.replace("TK","Tk").replace("PC-8001 mkII", " PC-8001 MK2")
    if "Olivetti" in manufacturer:
        name=name.replace("-"," ")
    if "Otrona" in manufacturer:
        name=name.replace("Attached","Attache")
    if "Philips" in manufacturer or "Schneider" in manufacturer:
        name=name.replace("VG ","VG-")
    if "Psion"in manufacturer and "Series" in name:
        name="Psion "+name
    if "Radiola" in manufacturer:
        name=name.replace("MK","MK-").replace("VG ","VG-")
    if "Robotron" in manufacturer:
        name=name.replace("- ","(")
        if "(" in name and ")" not in name:
            name +=")"
    if "Rockwell" in manufacturer:
        name=name.replace(" ","")
    if "GOUPIL" in manufacturer:
        name=name.split("/")[0].strip()
        if "86" in name or "40" in name:
            name=name.replace("Goupil", "System")
        if "Club" in name:
            name=name.replace("Goupil ", "")
    if "Sanyo" in manufacturer:
        name=name.replace("MBC ","MBC-").split("/")[0].strip()
        name=name.replace("Wavy", "(Wavy ")
        if "(" in name and ")" not in name:
            name +=")"
    if "Scelbi" in manufacturer:
        name= "Scelbi-"+name
    if "Southwest" in manufacturer:
        name="SWTPC "+name
    if "Schneider" in manufacturer:
        name=name.replace("MC","MC-").replace("Euro","Euro ")
    if "Sega" in manufacturer:
        name=name.replace("SC","SC-")
    if "Sharp" in manufacturer:
        name=name.replace("PC-"," PC ").replace("MZ-","MZ").replace("X1-G","X1g").replace("X1-F","X1f").replace("X1 Turbo Z","X1 TurboZ").strip()
    if "Sinclair" in manufacturer:
        name=name.replace("ZX80","ZX 80 (ZX80)").replace("ZX81","ZX 81 (ZX81)").replace("PC","PC ")
        if name=="Spectrum +":
            name.replace(" +","+")
    if "Sony" in manufacturer:
        name=name.replace("Hit Bit ","").replace("F1XD","F1 XD").replace("F1XDJ","F1 XDJ").replace("F1XV","F1 XDV")
    if "Sord" in manufacturer:
        name=name.replace("M23 P","M23P").replace("IS 11","IS-11")
    if "Sun" in manufacturer:
        name=name.replace("SPARCs","SparcS").replace("SPARCc","SparcC").replace("SPARC","Sparc")
    if "Tandy" in manufacturer:
        name=name.replace("TRS-80","TRS80").replace("1000 TL","1000TL")
    if "Texas Instruments" in manufacturer:
        name=name.replace("Computer 40","Computer 40 (CC40)")
    if "Thomson" in manufacturer:
        name=name.replace("Platini", "Michele Platini").replace(" N","N")
    if "Timex" in manufacturer:
        name=name.replace("TS ","TS-")
    if "Toshiba" in manufacturer:
        name=name.replace("00 S","00S")
    if "Sirius" in manufacturer:
        name=name.replace("Vicky","Vicki")
    if "Xerox" in manufacturer:
        name=name.replace(" Star"," - Star").replace("8/16","16/8")
    if "Yamaha" in manufacturer:
        name=name.replace("CX11","CX-11")
    if "Zenith" in manufacturer:
        name=name.replace("Z-","Z").replace("Supersport","Super Sport").replace("-"," ")
    if "Applied Technology" in manufacturer:
        name=name.replace("k","")
    if "Apple" in manufacturer:
        name=name.replace(" II+"," II Plus").replace("II J-plus","Apple II J Plus").replace(" IIc+"," IIc Plus").replace("Mac Powerbook 190","Powerbook 190").replace("Mac Powerbook 150","PowerBook 150").replace("Mac Powerbook 100","PowerBook 100")
    if "Atari" in manufacturer:
        if name=="65":
            name+=" XE"
        elif name=="130":
            name+=" XE"
        else:
            name=name.replace(" XL","XL").replace("1040 STfm","1040STFM").replace("1040 STf","1040STf").replace("520 ST","520ST").replace("Stacy 4","Stacy4").replace("Mega STE","Mega STe").replace("Portfolio", "PortFolio")
    if "Basis" in manufacturer:
        name= "Basis "+name
    if "Cambridge" in manufacturer:
        name=name.replace("Z 88","Z88")
    if "Canon" in manufacturer:
        name=name.replace("cat","CAT").replace("CX-1","CX 1")
    if "Casio" in manufacturer:
        elenco=["FX-770P", "FX-790P", "FX-850","FX-750", "PB-2000C", "PB-770", "PB-100", "PB-700", "FX-700P", "FP-200"]
        if name in elenco:
            name=name.replace("-", " ")
        name=name.replace("MX","MX-").replace("790P","790 P").replace("850P","850 P").replace("FX-730P","Fx 730P").replace("FX-720P","Fx 720P")
    if "Commodore" in manufacturer:
        name=name.replace("VC 20","VC20").replace("C ","").replace("500+","500Plus").replace("Aldi", "ALDI")
    if "Compaq" in manufacturer:
        name=name.replace("LTE ","LTE").replace("Deskpro","DeskPro")
    if "Epson" in manufacturer:
        name=name.replace("-","").replace("PX","PX ")    
    if "Franklin" in manufacturer:
        name=name.replace("Ace 100","ACE 100").replace("ACE 1000","Ace 1000")
    if "Fujitsu" in manufacturer:
        name=name.replace("FM8","FM 8").replace("FM11","FM 11").replace("FM77","FM 77").replace("16 beta","16 Beta")
    if "GRiD" in manufacturer:
        name=name.replace("Grid","GRiD")
    if "Hewlett" in manufacturer and name[0].isdigit():
        name= "HP "+name
    if "IBM" in manufacturer:
        name=name.replace("PS/2 mod", "Personal System/2 Model").replace("PS/1 mod", "Personal System/1 Model").replace("PC-jr", "PCjr").replace("PC-XT","PC/XT").replace("PC-AT","PC/AT").replace("SX", "SX ").replace("(", "- ").replace(")","").strip()
    if "Leanord" in manufacturer:
        name=name.replace("Sil'z", "Sil'Z")

    # restituisce il nome corretto  
    return name.strip()

def get_value_from_table(driver, parameter):
    """Cerca il parametro negli elementi della tabella, restituisce il testo dell'elemento immediatamente successivo"""
    try:
        value = driver.find_element(By.XPATH, '//tr[contains(.,"{0}")]/td[@class="tab_right"]'.format(parameter)).text
    except:
        value=None
    return value

def get_data(driver):
    """Recupera i dati tecnici del modello e li inserisce nel database"""
    cursor = conn.cursor()
    #ricava brand, origine e nome alternativo del produttore
    try:
        #attende che gli elementi siano visibili
        WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//tr[contains(.,"Manufacturer")]/td[@class="tab_right"]')))
        manufacturer=get_value_from_table(driver,"Manufacturer")
        origin=manufacturer.split("(")[1].replace(")","").replace("?"," ").replace(" ,","").strip()
        if origin[0]==",":
            origin=origin.replace(",","")
        # corregge il nome del produttore
        brand=correct_manufacturer(driver, manufacturer.split("(")[0])
    except:
        brand= "Unknown"
        origin= None
    #l'attributo nome alternativo del produttore è sempre null, non essendo presente
    alt_name= None
    # ricava il nome del modello
    try:
        name = driver.find_element(By.XPATH, '//tr[contains(.,"Reference")]/td[@class="tab_right"]').text
    except:
        # se non trova il nome del modello, esce
        print("Nome non trovato")
        return
    # corregge il nome del modello   
    name = correct_name(name, brand)
    # dati tecnici
    year = get_value_from_table(driver,"Release" )
    cpu = get_value_from_table(driver, "Processor")
    if "?" in cpu:
        cpu= None
    storage = get_value_from_table(driver, "Storage")
    ports = get_value_from_table(driver, "Interfaces")
    os = get_value_from_table(driver, "Software") 
    notes = get_value_from_table(driver, "Special")
    if notes and "#" in notes:
        notes = None  
    sound = None
    price = None
    # recupa "memory" dalla scheda tecnica
    # separa le informazioni relative a ram e rom dal contenuto di memory
    # gestendo tutti i possibili casi in cui si presentano
    try:
        memory = driver.find_element(By.XPATH, '//tr[contains(.,"Memory")]/td[2]').text
    except:
        ram=None
        rom=None   
    try:
        ram=""
        #recupera tutte le linee di testo che non contengono la parola "ROM", le elimina da memory e le aggiunge a ram
        ram_lines = driver.find_elements(By.XPATH, '//tr[contains(.,"Memory")]/td[2]/font[not(contains(., "ROM"))]')
        if len(ram_lines)>0:
            for line in ram_lines:
                r=line.text
                if r:
                    memory=memory.replace(r,"")
                    ram+=r+" "
            if ram:
                rom=memory.replace("\n"," ").strip()
                if "?" in rom:
                    rom=None
            else:
                ram=memory
                rom=None
        else:
            rom=memory
            ram=None
        if rom and "?" in rom:
            rom=None
        if ram and "?" in ram:
            ram=None  
    except:
        ram=memory
        rom=None
    # ricava "display" dalla scheda tecnica
    # separa "text" dal contenuto di display
    # gestendo tutti i possibili casi in cui si presenta
    display = get_value_from_table(driver, "Display")
    try:
        text = driver.find_element(By.XPATH, '//tr[contains(.,"Display")]/td[2]/font[contains(., "Text:")]').text
        if "Graphics" in text:
            text=text.split("Graphics")[0]
        if "Graphic" in text:
            text=text.split("Graphic")[0]
        display=display.replace(text+"\n","").replace(text,"").strip()
        text=text.replace("Text: ","").strip()
        if display=="":
            display=None
    except:
        text=None
    if display and "?" in display:
        display=None
    if text and "?" in text:
        text=None
    #inserisce le istanze nel database
    cursor.execute(cursor.mogrify("INSERT INTO Manufacturer (Brand, Alternative_name, Origin) VALUES (%s,%s,%s) ON CONFLICT (Brand) DO UPDATE SET Origin=COALESCE(Manufacturer.Origin, %s)", (brand, alt_name, origin, origin)))  
    cursor.execute(cursor.mogrify("INSERT INTO Model (Name, Manufacturer, Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Sound, Storage, Ports, Price, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(Name, Manufacturer) DO UPDATE SET (Year, Ram, Rom, CPU, Operative_System, Display_or_Graphics, Text, Storage, Ports, Notes) = (COALESCE(Model.Year, %s), COALESCE(Model.Ram, %s), COALESCE(Model.Rom, %s), COALESCE(Model.CPU, %s), COALESCE(Model.Operative_System, %s), COALESCE(Model.Display_or_Graphics, %s), COALESCE(Model.Text, %s), COALESCE(Model.Storage, %s), COALESCE(Model.Ports, %s), COALESCE(Model.Notes, %s))", (name, brand, year, ram, rom, cpu, os, display, text, sound, storage, ports, price, notes, year, ram, rom, cpu, os, display, text, storage, ports, notes)))
    # cerca la pagina della collezione, se presente
    # altrimenti assegna a collection_page l'url della pagina corrente
    try:
        collection_page = driver.find_element(By.XPATH, '//tr[contains(.,"Collection")]//a[contains(@href, "detailcollection.php?ident=")]').get_attribute("href")
    except:
        collection_page= driver.current_url
    # recupera le immagini da collection_page
    get_img(driver, collection_page, name, brand)
    conn.commit()

    

    
    
def main():
    #installa WebDriver 
    print("Inizio scraping di system-cfg.com")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    print("Caricamento WebDriver...")
    # visita ogni pagina nel range:
    for i in range(1,1136): #1136
        # ottiene url con richiesta di traduzione all'api di google translate
        val = "https://www-system--cfg-com.translate.goog/detail.php?ident={0}&_x_tr_sl=fr&_x_tr_tl=en&_x_tr_hl=en&_x_tr_pto=wapp".format(i)
        #richiede al driver di aprire la pagina
        driver.get(val)
        current_url = driver.current_url
        WebDriverWait(driver, 10).until(EC.url_to_be(val))
        #se la pagina è stata caricata correttamente
        if current_url == val:
            #recupera i dati 
            get_data(driver)
            print("Fatto {0} su 1136".format(i))
    # chiusura driver
    driver.close()
    print("Fine scraping di system-cfg.com")


        
"""Esecuzione dello script"""
#connessione al database PostgreSQL 
conn = connetti()
#esegue main
main()
#chiusura connessione database 
conn.close()