import time
from grove.grove_i2c_color_sensor_v2 import GroveI2cColorSensorV2

def lecture_donnees() -> tuple :
    """
        fonction qui recupère les données captées par le capteur connectées sur le raspberry
        retourn un tuple correspondant au code rgb de la couleur
    """
    color_sensor = GroveI2cColorSensorV2()
    color_sensor.sleep()
    color_sensor.wakeup()
    
    if color_sensor.is_awake() == 1:
        print("le capteur est prêt!")
        print("l'id du port du capteur est : ",color_sensor.id)
    else:
        print("le capteur n'est pas branché :(")

    return color_sensor.rgb


def melange(rgb1 : tuple, rgb2: tuple) -> tuple:
    """
        fonction qui prend en paramètre les codes rgb de deux couleurs et renvoie
        le code rgb de la couleur obtenue en mélangeant les deux couleurs.
    """
    
    #vérifier que les codes soient valides
    if len(rgb1) != 3 or len(rgb2) != 3 :
        return "le code rgb n'est pas valide, vérifier qu'il s'agit d'un tuple de 3 valeurs"
    
    #calcul des moyennes des composantes RGB
    r_mel = (rgb1[0]+rgb2[0]) // 2
    g_mel = (rgb1[1]+rgb2[1]) // 2
    b_mel = (rgb1[2]+rgb2[2]) // 2
    
    return (r_mel,g_mel,b_mel)


import requests
def get_color_name(rgb:tuple)-> str:
    """
        prend en paramètre un code rgb d'une couleur et renvoie son nom
        en envoyant une requête au site thecolorapi.
    """
    #utilisation de l'API The Color Api
    url = f'http://www.thecolorapi.com/id?rgb={rgb[0]},{rgb[1]},{rgb[2]}'
    reponse = requests.get(url)
    
    if reponse.status_code == 200 :
        data = reponse.json()
        #print(data)
        return data['name']['value']


def get_color_image(rgb):
    """
        fonction qui prend en paramètre un code rgb et renvoie le lien de 
        l'image de la couleur.
    """
    
    url = f'http://www.thecolorapi.com/id?rgb={rgb[0]},{rgb[1]},{rgb[2]}'
    reponse = requests.get(url)
    
    if reponse.status_code == 200 :
        data = reponse.json()
        #print(data)
        image = data['image']['bare']
        return image


#importation des modules nécessaire
import os
import uvicorn
from fastapi import FastAPI,Request, HTTPException,Form 
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


# Création de l'application
app = FastAPI() 
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

#on définit des variables globales utiles pour plus tard
uti = None
couleur1 = None
couleur2 = None


#première page du site web
@app.get("/", response_class=HTMLResponse) #Traitement de la requête get http
def index(request:Request) -> str : #Valeur de retour pour la réponse http
    return templates.TemplateResponse("index.html", {"request":request})


#deuxième page du site
@app.get("/html_connexion.html", response_class=HTMLResponse) 
def html(request: Request) -> str: 
    return templates.TemplateResponse("html_connexion.html", {"request":request})


#dans le cas d'une connexion (on clique sur "se connecter")
@app.post("/connexion",response_class = HTMLResponse)
def traitement(request:Request, pseudo_uti : str = Form(...), mdp_uti = Form(...)):
    
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on regarde si le pseudo est dans la table utilisateur
    verif_pseudo = cur.execute("SELECT * FROM utilisateur WHERE pseudo = ?;", (pseudo_uti,))
    
    if verif_pseudo.fetchone() is None: #si le pseudo n'est pas dedans
        #on ferme la bd
        con.close()
        #on affiche un message
        raise HTTPException(status_code=400, detail="Le pseudo est incorrect.") 
        
        
    else: #si le pseudo est dans la table
        #on va regarder si le mdp est bon
        verif_mdp = cur.execute("SELECT mdp FROM utilisateur WHERE pseudo = ?;", (pseudo_uti,))
        
        #si le mdp est faux 
        if verif_mdp.fetchone()[0] != mdp_uti :
            #on ferme la base de donnée
            con.close() 
            #on affiche un message
            raise HTTPException(status_code=400, detail="Le mot de passe est incorrect.")
        
        else: #si le mdp est bon
            #on met à jour l'utilisateur
            global uti
            uti = pseudo_uti
            
            #on ferme la BD
            con.commit()
            con.close()
            
            #et on peux aller sur le site
            return templates.TemplateResponse("page_menu.html", {"request":request, "pseudo_uti":pseudo_uti}) 


#quand on va sur "inscription"
@app.get("/page_ins.html",response_class=HTMLResponse)
def page_ins(request:Request):
    return templates.TemplateResponse("page_ins.html", {"request":request})

#dans le cas d'une inscription (on clique sur "valider l'inscription")
@app.post("/inscription",response_class = HTMLResponse)
def traitement(request:Request, pseudo_uti : str = Form(...), mdp_uti = Form(...)):
    
    #connexion à la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on regarde si pseudo n'est pas déjà dans la table utilisateur
    verif = cur.execute("SELECT * FROM utilisateur WHERE pseudo = ?;", (pseudo_uti,))
    
    if verif.fetchone() is None: #si le pseudo n'est pas dedans
        #on ajoute le pseudo et le mdp à la table utilisateur
        cur.execute("INSERT INTO utilisateur (pseudo,mdp) VALUES (?,?)", (pseudo_uti,mdp_uti,)) 
        #on met à jour l'utilisateur
        global uti
        uti = pseudo_uti
        #on ferme la BD
        con.commit()
        con.close()
        
        #et on peux aller sur le site
        return templates.TemplateResponse("page_menu.html", {"request":request,"pseudo_uti":pseudo_uti})

    else: #si le pseudo est déjà dans la table utilisateur
        con.close() #on ferme la base de donnée
        #on affiche un message
        raise HTTPException(status_code=400, detail="Le pseudo est déjà pris.")
    

#maintenant on est sur la page du menu car on s'est isncrit ou connecter 
    
#quand on accede à la page pour capter
@app.get("/page_capteur.html", response_class=HTMLResponse)
def page_capteur(request: Request) -> str: 
    return templates.TemplateResponse("page_capteur.html", {"request":request})

#quand on capte une couleur
@app.get("/capter",response_class=HTMLResponse)
def capte(request:Request):
    
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on recupere la couleur captée, son nom et son image
    couleur = lecture_donnees()
    nom = get_color_name(couleur)
    img_url = get_color_image(couleur)
    
    #on va ajouter cette couleur à la table de l'utilisateur, pour l'avoir dans son historique
    #vérifions d'abord si sa table existe
    existe = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (uti,))
    
    if existe.fetchone() is None: #si elle n'existe pas
        #on crée la table de l'utilisateur
        cur.execute(f"CREATE TABLE {uti} (id_coul INTEGER PRIMARY KEY AUTOINCREMENT, rgb VARCHAR(255), nom VARCHAR(255), img TEXT)") 
    
    #on peut maintenant ajouter la couleur captée à la table de l'utilisateur
    #mais d'abord on convertit le rgb en chaine de caractère pour l'insertion dans la table
    couleur_txt = ', '.join(map(str, couleur))
    
    #on ajoute maintenant la couleur
    cur.execute(f"INSERT INTO {uti} (rgb,nom,img) VALUES (?,?,?)", (couleur_txt,nom,img_url))
    #on ferme la BD
    con.commit()
    con.close()
    
    #on peut afficher les données récuperer sur la page 
    return templates.TemplateResponse("page_capteur.html",{"request":request,"message":"le code rgb de la couleur captee est : ","couleur":couleur_txt,"mess_nom":"Le nom de cette couleur est : ","nom":nom,"img_url":img_url})


#dans le cas où on veut mélanger deux couleurs
#quand on capte la première couleur 
@app.get("/capter1",response_class=HTMLResponse)
def capte1(request:Request):
    
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on recupere la couleur captée, son nom et son image
    global couleur1
    couleur1 = lecture_donnees()
    nom1 = get_color_name(couleur1)
    img_url1 = get_color_image(couleur1)
    
    
    #on va ajouter cette couleur à la table de l'utilisateur, pour l'avoir dans son historique
    #vérifions d'abord si sa table existe
    existe = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (uti,))
    
    if existe.fetchone() is None: #si elle n'existe pas
        #on crée la table de l'utilisateur
        cur.execute(f"CREATE TABLE {uti} (id_coul INTEGER PRIMARY KEY AUTOINCREMENT, rgb VARCHAR(255), nom VARCHAR(255), img TEXT)") 
    
    #on peut maintenant ajouter la couleur captée à la table de l'utilisateur
    #mais d'abord on convertit le rgb en chaine de caractère pour l'insertion dans la table
    couleur1_txt =  ', '.join(map(str, couleur1))
    #on ajoute la couleur
    cur.execute(f"INSERT INTO {uti} (rgb,nom,img) VALUES (?,?,?)", (couleur1_txt,nom1,img_url1))
    #on ferme la BD
    con.commit()
    con.close()
    
    #on peut afficher les données récuperer sur la page
    return templates.TemplateResponse("page_capteur.html", {"request":request, "message1":"le code de la premiere couleur est : ","couleur1":couleur1_txt,"mess_nom1":"Le nom de cette couleur est : ","nom1":nom1,"img_url1":img_url1})

#quand on capte la deuxième couleur
@app.get("/capter2",response_class=HTMLResponse)
def capte2(request:Request):
    
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on recupere la couleur captée, son nom et son image
    global couleur2
    couleur2 = lecture_donnees()
    nom2 = get_color_name(couleur2)
    img_url2 = get_color_image(couleur2)
    
    #on va ajouter cette couleur à la table de l'utilisateur, pour l'avoir dans son historique
    #vérifions d'abord si sa table existe
    existe = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (uti,))
    
    if existe.fetchone() is None: #si elle n'existe pas
        #on crée la table de l'utilisateur
        cur.execute(f"CREATE TABLE {uti} (id_coul INTEGER PRIMARY KEY AUTOINCREMENT, rgb VARCHAR(255), nom VARCHAR(255) img TEXT)") 
    
    #on peut maintenant ajouter la couleur captée à la table de l'utilisateur
    couleur2_txt =  ', '.join(map(str, couleur2))
    #on ajoute la couleur
    cur.execute(f"INSERT INTO {uti} (rgb,nom,img) VALUES (?,?,?)", (couleur2_txt,nom2,img_url2))
    #on ferme la BD
    con.commit()
    con.close()
    
    #on peut afficher les données récuperer sur la page
    return templates.TemplateResponse("page_capteur.html", {"request":request,"message2":"le code de la deuxieme couleur est : ", "couleur2":couleur2_txt,"mess_nom2":"Le nom de cette couleur est : ","nom2":nom2,"img_url2":img_url2})

#quand on clique sur le bouton pour mélanger
@app.get("/melanger",response_class=HTMLResponse)
def melanger(request:Request):
    
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on recupere le mélange, son nom et son image
    mel = melange(couleur1,couleur2)
    nom3 = get_color_name(mel)
    img_url3 = get_color_image(mel)
    
    #on va ajouter cette couleur à la table de l'utilisateur, pour l'avoir dans son historique
    #vérifions d'abord si sa table existe
    existe = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (uti,))
    
    if existe.fetchone() is None: #si elle n'existe pas
        #on crée la table de l'utilisateur
        cur.execute(f"CREATE TABLE {uti} (id_coul INTEGER PRIMARY KEY AUTOINCREMENT, rgb VARCHAR(255), nom VARCHAR(255), img TEXT)") 
    
    #on peut maintenant ajouter la couleur captée à la table de l'utilisateur
    mel_txt = ', '.join(map(str, mel))
    #on ajoute la couleur
    cur.execute(f"INSERT INTO {uti} (rgb,nom,img) VALUES (?,?,?)", (mel_txt,nom3,img_url3))
    
    #on ferme la BD
    con.commit()
    con.close()
    
    #on peut afficher les données récuperer sur la page
    return templates.TemplateResponse("page_capteur.html", {"request":request,"message3":"le code de la couleur obtenue est : ", "mel":mel_txt,"mess_nom3":"Le nom de cette couleur est : ","nom3":nom3,"img_url3":img_url3})


#quand on veut retourner au menu
@app.get("/page_menu.html", response_class=HTMLResponse)
def page_menu(request:Request):
    return templates.TemplateResponse("page_menu.html", {"request":request, "pseudo_uti":uti})


#quand on accède à la page de l'historique
@app.get("/page_hist.html", response_class=HTMLResponse)
def page_hist(request:Request):
    
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on recupère toutes les couleurs captées de l'utilisateur dans sa table
    historique = cur.execute(f"SELECT rgb, nom, img FROM {uti}").fetchall()

    #on ferme la BD
    con.commit()
    con.close()
    
    #et on peux afficher sur la page
    return templates.TemplateResponse("page_hist.html",{"request":request, "historique" : historique})


#quand on accede à la page pour voir ses palettes
@app.get("/page_palettes.html", response_class=HTMLResponse)
def page_palettes(request:Request):
    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()

    #on veut recuperer les palettes de l'utilisateur
    palette_uti = []

    #on va chercher parmis les tables de la bd celles qui sont les palettes de l'utilisateur
    #pour cela, on regarde chaque table
    res = cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    toute_table = res.fetchall()

    for table in toute_table:
        t = table[0]
        #si cette table à une colonne utilisateur et que celui çi est le nom de l'utilisateur, alors il s'agit d'une de ses palettes
        #Vérifier si la colonne "utilisateur" existe dans la table
        cur.execute(f"PRAGMA table_info({t});")
        columns_info = cur.fetchall()
        column_names = [column[1] for column in columns_info]

        if 'utilisateur' in column_names:
            # La colonne "utilisateur" existe dans cette table
            test = cur.execute(f"SELECT utilisateur FROM {t};")
            if test.fetchall()[0][0] == uti:
                palette_uti.append(t)
    
    #maintenant qu'on a les palettes de l'utilisateur, on peut les afficher sur notre page
    return templates.TemplateResponse("page_palettes.html",{"request":request,"palette_uti":palette_uti})


#quand on clique sur le bouton pour créer une nouvelle palette, ce popup s'ouvre
@app.get("/popup.html", response_class=HTMLResponse)
def nouvelle_palette(request:Request):

    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()
    
    #on recupère toutes les couleurs captées de l'utilisateur dans sa table
    historique = cur.execute(f"SELECT rgb, nom, img FROM {uti}").fetchall()

    #on ferme la BD
    con.close()

    return templates.TemplateResponse("popup.html", {"request":request, "historique":historique})

#quand on clique sur le boutou de validation pour créer la palette 
@app.post("/nouv_palette", response_class=HTMLResponse)
def nouv_palette(request:Request, nom_palette : str = Form(...), couleur_palette : list = Form(...)):

    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()


    #on va créer une nouvelle table correspondant à la palette créée
    cur.execute(f"CREATE TABLE {nom_palette} (utilisateur, rgb VARCHAR(255), nom VARCHAR(255), img TEXT)")

    #ensuite on ajoute toutes les couleurs sélectionnées dans cette table
    for coul in couleur_palette:
        print(coul)
        #on recupere le rgb de la coul
        rgb_coul = coul
        #on recupere le nom de la coul
        res = cur.execute(f"SELECT nom FROM {uti} WHERE rgb = '{rgb_coul}';")
        n = res.fetchall()[0][0]
        nom_coul = n
        #on recupere l'image de la coul
        res2 = cur.execute(f"SELECT img FROM {uti} WHERE rgb = '{rgb_coul}';")
        im = res2.fetchall()[0][0]
        img_coul = im

        cur.execute(f"INSERT INTO {nom_palette} (utilisateur, rgb, nom, img) VALUES (?,?,?,?)", (uti,rgb_coul,nom_coul,img_coul))

    #on ferme la bd    
    con.commit()
    con.close()
    
    #on accède à la deuxième page du popup
    return templates.TemplateResponse("popup_2.html", {"request":request})

#popup qui s'ouvre lorsque l'on clique sur une palette à afficher
@app.get("/popup_palette", response_class=HTMLResponse)
def popup_palette(request: Request, nomBouton: str):

    #on connecte la BD
    import sqlite3
    con = sqlite3.connect('projet.db')
    cur = con.cursor()

    #on recupère les couleurs de cette palette 
    couleur = cur.execute(f"SELECT rgb,nom,img FROM {nomBouton};").fetchall()
    print(couleur)

    #on ferme la BD
    con.commit()
    con.close()

    #on accède au popup qui affiche la palette
    return templates.TemplateResponse("popup_palette.html", {"request":request,"couleur":couleur,"nomBouton":nomBouton})


    
if __name__ == "__main__":
    uvicorn.run(app) # lancement du serveur HTTP + WSGI avec les options de debug