#!/usr/bin/env python
import cgi
from cgi import parse_qs, escape
import MySQLdb
host="localhost"
database="songlands3"
def application(environ, start_response):
	parameters = parse_qs(environ.get('QUERY_STRING', ''))
	conn = MySQLdb.connect (host = host,db = database)
	if 'image' in parameters:
		image = cgi.escape(parameters['image'][0])
		rows = mysql_get(conn,"SELECT image FROM images WHERE id = '" + image + "'")
		data = rows[0]['image']
		start_response('200 OK', [('content-type', 'image/jpeg'),('content-length', str(len(data)))])
		return [data]
	else:
		if 'page' in parameters:
			page = escape(parameters['page'][0]), escape(parameters['page'][1])
		else:
			page = 'cat','Home'
		write = start_response('200 OK', [('Content-type', 'text/html')])
		write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN""http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en"><head><meta http-equiv="Content-Type" content="text/html;charset=utf-8" /><link rel="stylesheet" type="text/css" href="media/slp.css" /><title>songlands ponies</title></head><body><div id="header"><img style="border:0;display:block;margin-left:auto;margin-right:auto" src="media/banner.gif" alt="songlands ponies"/><br/><h1>Breeding quality ponies with gentle temperament<br/>Welsh and Connemara</h1></div><div id="menu"><ul>""")
		menurows = mysql_get(conn,"SELECT * FROM sidebar ORDER BY `order`")
		limit=0
		for row in menurows:
			#what page are we on?
			if row['title'] == page[1]:
				write("<li><b>"+text_out(row['title'])+"</b></li>")
				limit=row['imagelimit']
			else:
				write("<li><a href=?"+row['qurey']+">"+text_out(row['title'])+"</a></li>")
		write('</ul></div><div id="content">')
		rows = mysql_get(conn,"SELECT * FROM data WHERE "+page[0]+" = '"+page[1]+"' ORDER BY `sort`,shortname")
		if page[0] == "shortname" and rows[0]["fullname"]:
			write('<h1>'+text_out(rows[0]["fullname"])+'</h1>')
		else:
			write('<h1>'+text_out(page[1])+'</h1>')
		for row in rows:
			imagerows = mysql_get(conn,"SELECT caption,id FROM images WHERE shortname = '"+row['shortname']+"' ORDER BY `order`")
			i=1
			for image in imagerows:
				write('<p><a href="?page=shortname&page='+row['shortname']+'"><img src="?image='+ str(image['id']) +'" alt="[loading]"/>')
				if(image['caption']):
					write("<br/>"+text_out(image['caption']))
				if limit and limit<=i:
					break
				i+=1
			write('<br/>'+text_out(row['fullname']))
			if(row['section']):
				write(" (" + text_out(row['section']) + ")" )
			if(row['height']):
			                        write(" (" + text_out(row['height']) + ")" )
			write("</a>")
			if(row['for_sale']):
				if not(row['for_sale'] == "No"):
					write(" (" + text_out(row['for_sale'])+")")
			if(row['sire']):
				write('<br/>sire: '+text_out(row['sire']))
			if(row['dam']):
				write('<br/>dam: '+text_out(row['dam']))
			if(row['blurb']):
				write('<br/>'+text_out(row['blurb']))
			write ("</p>")
		write("""
	        <script type="text/javascript">
	        var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
	        document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
	        </script>
	        <script type="text/javascript">
	        try{
	        var pageTracker = _gat._getTracker("UA-5517043-1");
	        pageTracker._trackPageview();
	        } catch(err) {}</script>
	        """)
		return '</div></body></html>'

### text out of db
def text_out(text):
	i = 2
	var = ["/","\'",";",",","\\"," "]
	for char in var:
		text = text.replace("__"+str(i)+"_",char)
		i += 1
	text = text.replace("__1_","_")
	return text

## db qurey stuff
def mysql_get(conn,qureystring):
	cursor = conn.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute (qureystring)
	rows = cursor.fetchall ()
	cursor.close ()
	return rows
