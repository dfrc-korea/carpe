import carpe_db

def Main():
	data = "r/r|42-128-1|root/|[White] Logo.png|1533268698|1539172148|1539172148|png"
	db_test = carpe_db.Mariadb()
	conn=db_test.open()
	query=db_test.query_builder("1", data, "file")
	data=db_test.execute_query(conn,query)
	print (data)

if __name__ == '__main__':
	Main()