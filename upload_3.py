#!/usr/bin/env python

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import pygtk
pygtk.require('2.0')
import gtk
import MySQLdb
from PIL import Image
import sys
import os
import StringIO
import settings
class upload_3:
	short_input_limit=50
	text_box_input_limit=250
############
# init stuff
############
	def initstuff(self):
		if (len(sys.argv) <= 1):
			self.new = False
		else:
			self.imagebuffer=StringIO.StringIO()
			self.new=True
###############
# exit function
###############
	def delete_event(self, widget=None, event=None, data=None):
		gtk.main_quit()
		return False
###############
#event handling
###############
	def process_update(self,event):
		#self.mysql_image_upload()
		self.mysql_update()
		if not self.new:
			self.delete_event()
#############
# mysql stuff
#############
	def mysql_get(self,table="images",column="*",where=""):
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		if(where):
			qureystring = "SELECT "+column+" FROM " + table + " WHERE " + where
		else:
			qureystring = "SELECT "+column+" FROM " + table
		cursor.execute (qureystring)
		rows = cursor.fetchall ()
		cursor.close ()
		return rows

	def mysql_put(self,sql,args):
		cursor = self.conn.cursor()
		cursor.execute (sql, args)
		cursor.close ()

	def mysql_image_upload(self):
		if self.new:
			sql='INSERT INTO images (shortname, image, caption) VALUES (%s, %s,%s)'
			args = (self.text_in(self.shortname.get_active_text()), self.imagebuffer.getvalue(), self.text_in(self.imagetitle.get_text()), )
			self.mysql_put(sql, args)

	def mysql_update(selptyyf):
		if self.shortname.get_active_text() == '' or self.catogery.get_active_text() == '':
			dialog = gtk.Dialog("My dialog",None,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_OK,gtk.RESPONSE_CLOSE))
			dialog.vbox.pack_start(gtk.Label("you need to fill in atleast the \n catogery and short name sections"))
			dialog.show_all()
			dialog.run()
			dialog.destroy()
		else:
			if self.new:
				rows = self.mysql_get("data","*")
				for row in rows:
					if self.text_in(self.shortname.get_active_text()) == row["shortname"] and self.text_in(self.catogery.get_active_text()) == row['cat'] :
						update=False
						break
				if update and not self.new:
					print "updating"
					sql='INSERT INTO data (shortname, cat, fullname, for_sale, section, height, sire, dam, blurb, sort) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s )'
					args=(self.text_in(self.shortname.get_active_text()), self.text_in(self.catogery.get_active_text()), self.text_in(self.fullname.get_text()), self.text_in(self.forsale.get_active_text()), self.text_in(self.section.get_active_text()), self.text_in(self.height.get_text()), self.text_in(self.sire.get_text()),self.text_in(self.dam.get_text()),  self.text_in(self.blurb.get_buffer().get_text(self.blurb.get_buffer().get_start_iter(), self.blurb.get_buffer().get_end_iter())), "15", )
					self.mysql_put(sql, args)

	def mysql_connect(self):
		self.conn = MySQLdb.connect (host = settings.host,user = settings.user,passwd = settings.password ,db = settings.database)
#######
# misc
#######
	def text_in(self,text):
		i = 1
		var = ["_","/","\'",";",",","\\"," "]
		for char in var:
			text = text.replace(char,"__"+str(i)+"_")
			i += 1
		text = text.strip().capitalize()
		return text

	def text_out(self,text):
		i = 2
		var = ["/","\'",";",",","\\"," "]
		for char in var:
			text = text.replace("__"+str(i)+"_",char)
			i += 1
		text = text.replace("__1_","_")
		return text

	def show_image(self,image):
		fd = StringIO.StringIO()
		image.save(fd, "ppm")
		contents = fd.getvalue()
		fd.close()
		loader = gtk.gdk.PixbufLoader("pnm")
		loader.write(contents, len(contents))
		pixbuf = loader.get_pixbuf()
		loader.close()
		self.image.set_from_pixbuf(pixbuf)
		self.image.show()

	def update_short_name(self, widget):
		rows = self.mysql_get("data","shortname","cat = '"+self.text_in(self.catogery.get_active_text())+"'")
		srows = []
		for x in rows:
			if x not in srows:
				srows.append(x)
		self.shortname.get_model().clear()
		for row in srows:
			self.shortname.append_text(self.text_out(row['shortname']))

	def update_entry(self, widget):
		rows = self.mysql_get("data","*","shortname = '"+self.text_in(self.shortname.get_active_text()) +"' AND cat = '"+self.text_in(self.catogery.get_active_text())+"'")
		if(len(rows) == 1):
			if(rows[0]['fullname']):
				self.fullname.set_text(self.text_out(rows[0]['fullname']))
			if(rows[0]['for_sale']):
				print self.text_out(rows[0]['for_sale'])
				if (self.text_out(rows[0]['for_sale']) == "For sale"):
					self.forsale.set_active(1)
				if (self.text_out(rows[0]['for_sale']) == "sold"):
					self.forsale.set_active(2)
			else:
				self.forsale.set_active(0)
			#if(rows[0]['section']):
				#self.section.set_text(self.text_out(rows[0]['section']))
			if(rows[0]['sire']):
				self.sire.set_text(self.text_out(rows[0]['sire']))
			if(rows[0]['dam']):
				self.dam.set_text(self.text_out(rows[0]['dam']))
			if(rows[0]['blurb']):
				blurbbuffer = self.blurb.get_buffer()
				blurbbuffer.set_text(self.text_out(rows[0]['blurb']))
				self.blurb.set_buffer(blurbbuffer)
			self.imagename.get_model().clear()
			images = self.mysql_get("images","image ,id","shortname = '"+self.text_in(self.shortname.get_active_text()) +"'")
			for image in images:
				self.imagename.append_text(str(image['id']))
				self.imagename.set_active_iter(self.imagename.get_model().get_iter_first())
		else:
			self.fullname.set_text("")
			self.sire.set_text("")
			self.dam.set_text("")
##################
# image processing
##################
	def image_pre_process(self):
		im = Image.open(sys.argv[1])
		img =  im.size
		imgsize = img[0] / 600.00
		imgsize = img[1] / imgsize
		imgsize = int(round(imgsize))
		imgresult = 600,imgsize
		im = im.resize(imgresult)
		im.save(self.imagebuffer,"jpeg")
		pixbuf = self.show_image(im)
###########
# gui setup
###########
	def gui_setup(self):
		self.mysql_connect()
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title(settings.host)
		self.window.set_default_size(800,780)
		self.window.connect("delete_event", self.delete_event)
		self.window.set_border_width(10)
		#layout setup
		vbox1 = gtk.VBox()
		self.window.add(vbox1)

		#put image above everything else
		#border around all image related stuff
		imageframe = gtk.Frame ()
		vbox1.pack_start(imageframe,True)

		##stuff inside imageframe
		imagevbox = gtk.VBox()
		imageframe.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
		imageframe.add(imagevbox)
		imagetophbox = gtk.HBox()
		imagevbox.pack_start(imagetophbox,True)

		imagewindow = gtk.ScrolledWindow()
		imagewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		imagetophbox.pack_start(imagewindow,True)

		self.imagetopvbox=gtk.VBox()
		imagetophbox.pack_start(self.imagetopvbox,False)
		self.imagetopvbox.pack_start(gtk.Label("image:"),False)


		imagehbox = gtk.HBox()
		imagevbox.pack_start(imagehbox,False)

		leftimagevbox = gtk.VBox()
		imagehbox.pack_start(leftimagevbox,False)

		rightimagevbox = gtk.VBox()
		imagehbox.pack_start(rightimagevbox,True)

		leftimagevbox.pack_start(gtk.Label("image caption:"))

		self.imagetitle = gtk.Entry(40)
		rightimagevbox.pack_start(self.imagetitle,False)

		self.image = gtk.Image()
		imagewindow.add_with_viewport(self.image)

		##end of image stuff

		vbox1.pack_start(gtk.Label(""),False)
		vbox1.pack_start(gtk.Label("general:"),False)

		hbox1 = gtk.HBox()
		vbox1.pack_start(hbox1, False)

		vbox2 = gtk.VBox(True)
		hbox1.pack_start(vbox2, False)

		vbox3 = gtk.VBox(True)
		hbox1.pack_start(vbox3, True)

		#catogery
		vbox2.pack_start(gtk.Label("catogery:"))

		self.catogery = gtk.combo_box_entry_new_text()
		rows = self.mysql_get("data","cat")
		srows = []
		for x in rows:
			if x not in srows:
				srows.append(x)
		for row in srows:
			self.catogery.append_text(self.text_out(row["cat"]))
		vbox3.pack_start(self.catogery)
		self.catogery.connect("changed", self.update_short_name)


		#short name
		vbox2.pack_start(gtk.Label("short name:"))
		self.shortname = gtk.combo_box_entry_new_text()
		vbox3.pack_start(self.shortname)
		self.shortname.connect("changed", self.update_entry)

		#full name
		vbox2.pack_start(gtk.Label("full name:"))
		self.fullname = gtk.Entry(40)
		vbox3.pack_start(self.fullname)

		#section/for_sale
		vbox2.pack_start(gtk.Label("for sale?:"))
		self.forsale = gtk.combo_box_new_text()
		forsaleopts = ["no","for sale","sold"]
		for x in forsaleopts:
			self.forsale.append_text(self.text_out(x))
		self.forsale.set_active_iter(self.forsale.get_model().get_iter_first())
		hboxforsale = gtk.HBox(False)
		vbox3.pack_start(hboxforsale)
		hboxforsale.pack_start(self.forsale)

		hboxforsale.pack_start(gtk.Label("height:"))
		self.height = gtk.Entry()
		hboxforsale.pack_start(self.height)

		hboxforsale.pack_start(gtk.Label("section:"))
		self.section = gtk.combo_box_entry_new_text()
		sectionopts = ["sec A","sec B"]
		for x in sectionopts:
			self.section.append_text(self.text_out(x))
		hboxforsale.pack_start(self.section)


		#sire
		vbox2.pack_start(gtk.Label("sire:"))
		self.sire = gtk.Entry(40)
		vbox3.pack_start(self.sire)

		#dam
		vbox2.pack_start(gtk.Label("dam:"))
		self.dam = gtk.Entry(40)
		vbox3.pack_start(self.dam)

		#blurb
		vbox1.pack_start(gtk.Label("blurb:"),False)
		blurbwindow = gtk.ScrolledWindow()
		blurbwindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
		blurbwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		vbox1.pack_start(blurbwindow,False)

		self.blurb = gtk.TextView()
		blurbwindow.add(self.blurb)

		#bottom buttons
		hbox2 = gtk.HBox()
		vbox1.pack_start(hbox2,False)
		hbox2.show()
		exit = gtk.Button("exit")
		exit.connect("clicked", self.delete_event)
		hbox2.pack_start(exit,True)
		update = gtk.Button("update")
		update.connect("clicked", self.process_update)
		hbox2.pack_start(update,True)
		self.window.show_all()
		self.window.show()
######
# init
######
	def __init__(self):
		self.initstuff()
		self.gui_setup()
		if self.new:
			self.image_pre_process()

def main():
	gtk.main()
if __name__ == "__main__":
	upload_3 = upload_3()
	main()