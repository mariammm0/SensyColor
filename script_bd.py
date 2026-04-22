
import sqlite3


#création de la BD du projet
con = sqlite3.connect('projet.db')
cur = con.cursor()

#création de la table utilisateur
cur.execute("CREATE TABLE utilisateur (id_uti INTEGER PRIMARY KEY AUTOINCREMENT, pseudo VARCHAR(255), mdp VARCHAR(255))")

#fermeture de la BD
con.commit()
con.close()

