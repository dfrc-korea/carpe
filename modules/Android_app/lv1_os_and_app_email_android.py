import sqlite3

class DB_schema:
    par_id = ''
    case_id = ''
    evd_id = ''
    subject = []
    fromlist = []
    tolist = []
    cc = []
    bcc = []
    message = []

def Email_android(input_db):
    data = []
    count = 0

    db = sqlite3.connect(input_db)
    cur = db.cursor()
    sql = "SELECT subject, fromList, toList, ccList, bccList, snippet FROM Message"

    cur.execute(sql)
    result = cur.fetchall()

    for i in range(len(result)):
        try:
            db_schema = DB_schema()
            data.append(db_schema)
            data[count].subject = result[count][0]

            datatmp = []
            for j in range(4):
                if result[count][j+1] is not None:
                    tmp = str(result[count][j+1]).replace(chr(2), "(").replace(chr(1), "), ")
                    if chr(2) in result[count][j+1]:
                        tmp = tmp + ")"
                else:
                    tmp = str(result[count][j+1])
                datatmp.append(tmp)

            data[count].fromlist = datatmp[0].replace('\'','')
            data[count].tolist = datatmp[1].replace('\'','')
            data[count].cc = datatmp[2].replace('\'','')
            data[count].bcc = datatmp[3].replace('\'','')
            data[count].message = result[count][5]
            count = count + 1

        except:
            print('Email Error')

    return data