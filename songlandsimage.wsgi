#!/usr/bin/env python
import cgi
import MySQLdb
import settings

def application(environ, start_response):
	parameters = cgi.parse_qs(environ.get('QUERY_STRING', ''))
	if 'id' in parameters:
		id = cgi.escape(parameters['id'][0])
	else:
		id = '1'

	conn = MySQLdb.connect (host = settings.host,user = settings.user,passwd = settings.password ,db = settings.database)
	rows = mysql_get(conn,"SELECT image FROM images WHERE id = '" + id + "'")
	data = rows[0]['image']
	start_response('200 OK', [('content-type', 'image/jpeg'),('content-length', str(len(data)))])
	return [data]

def mysql_get(conn,qureystring):
	cursor = conn.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute (qureystring)
	rows = cursor.fetchall ()
	cursor.close ()
	return rows
