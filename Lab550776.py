import mysql.connector
my_con = mysql.connector.connect(
    host="remotemysql.com",
    user="bPHiiRCWTe",
    passwd="Ftl2nnrmAp",
    database="bPHiiRCWTe"
)

cursor = my_con.cursor()

cursor.execute("SELECT * FROM characters \
    INNER JOIN anime \
    ON anime.id=characters.animeFK WHERE anime.title LIKE 'karakai-jouzu-no-takagi-san'")
for i in cursor:
    print(i, sep=" ")

cursor.execute("INSERT INTO characters (id,fName,lName,popularity,animeFK) \
    VALUES (507761,'jaikwang','gnawkiaj',4,12)")
my_con.commit()

print('\n')
cursor.execute("SELECT * FROM characters \
   INNER JOIN anime \
   ON anime.id=characters.animeFK WHERE characters.id LIKE '50776_'")
for i in cursor:
    print(i, sep=" ")

cursor.close()
my_con.close()