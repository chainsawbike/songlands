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
import gobject
pygtk.require('2.0')
import gtk
gtk.threads_init()
import MySQLdb
from PIL import Image
import sys
import os
import StringIO
import threading
import time

############
#move the status bar during updates
############

class statusbar(threading.Thread):


	def run(self):
		"""Run method, this is the code that runs while thread is alive."""
		#Thread event, stops the thread if it is set.
		self.stopthread = threading.Event()
		gtk.threads_enter()
		upload_3.update.hide()
		upload_3.exit.hide()
		upload_3.progressbar.show_now()
		gtk.threads_leave()
		#While the stopthread event isn't set, the thread keeps going on
		#but go for atleast 1 seconds
		delay = 0
		while (self.stopthread.isSet() == False) or (delay <= 10):
			gtk.threads_enter()
			upload_3.progressbar.pulse()
			gtk.threads_leave()
			#Delaying 100ms until the next iteration
			time.sleep(0.1)
			print delay
			delay +=1
		gtk.threads_enter()
		upload_3.progressbar.hide()
		upload_3.update.show()
		upload_3.exit.show_now()
		gtk.threads_leave()
		return


class upload_3:
	short_input_limit=50
	text_box_input_limit=250
	imageset={}
	currentimage=None
	horse_id = None
## you need to set this stuff##############################################
	#host="server.lan"
	#user="admin"
	#database="site"
	#password="reallyhard"

	dbversion="1"

## up to here :) ##########################################################
############
# init stuff
############
	def initstuff(self):
		self.gui_setup()
		self.processing("connecting",False)
		self.mysql_connect()
		#is this the correct version for the database
		rows = self.mysql_get("info","value","setting = 'version'")
		if not (rows[0]["value"]) == self.dbversion:
			self.dialog("this verison is to old - please contact aaron for an update")
			self.delete_event()
		if (len(sys.argv) <= 1):
			self.new = False
		else:
			self.imagebuffer=StringIO.StringIO()
			self.new=True
		if self.new:
			self.image_pre_process()
		self.populate()
		time.sleep(15)
		self.processing("connecting",True)
		return False
##############
#populate drop-down boxes
##############
	def populate(self):
		#catogery
		##sql abuse
		cat_rows = self.mysql_get("data","cat")
		cat_srows = []
		self.cat_index = []
		for cat_x in cat_rows:
			if cat_x not in cat_srows:
				cat_srows.append(cat_x)
				self.catogery.append_text(self.text_out(cat_x["cat"]))
				self.cat_index.append(cat_x["cat"])

		#name
		name_rows = self.mysql_get("data","fullname")
		name_srows = []
		self.nameindex = []
		self.fullname.append_text("")
		self.nameindex.append("")
		for name_x in name_rows:
			if name_x not in name_srows:
				name_srows.append(name_x)
				self.fullname.append_text(self.text_out(name_x["fullname"]))
				self.nameindex.append(name_x["fullname"])
		#grey out unnessary input boxes
		if self.new == False:
			#images
			self.imagetitle.set_sensitive(False)
			#general
			self.catogery.set_sensitive(False)
			self.forsale.set_sensitive(False)
			self.height.set_sensitive(False)
			self.section.set_sensitive(False)
			self.sire.set_sensitive(False)
			self.dam.set_sensitive(False)
			self.blurb.set_sensitive(False)
		#always set to locked
		self.button_delete.set_sensitive(False)
		self.button_delete_horse.set_sensitive(False)


##############
#hides exit/update buttons and puts a "procesing bar" there
##############
	def processing(self,action,complete):

		if complete == False:
			print "start"
			self.statusthread = statusbar()
			self.progressbar.set_text(action)
			self.statusthread.start()
			print "here"
		else:
			print "done"
			self.statusthread.stopthread.set()
			print "complete"

###############
# exit function
###############
	def delete_event(self, widget=None, event=None, data=None):
		gtk.main_quit()
		return False
###############
#event handling
###############
	def delete_horse(self,event):
		self.processing("deleting horse",False)
		if self.horse_id == None:
			self.dialog("please select a horse to delete first")
		else:
			self.dialog("this is not reversable __setup the cancel system__")
			self.mysql_put('DELETE FROM data WHERE horse_id={horse_id}'.format(horse_id=self.horse_id))
			self.mysql_put('DELETE FROM images WHERE horse_id={horse_id}'.format(horse_id=self.horse_id))
			#remove entry from fullname list
			self.fullname.remove_text(self.fullnameindex.index(self.fullname.get_active_text()))
			self.fullname.set_active(0)
			#lock all un-needed entry
			self.imagetitle.set_sensitive(False)
			self.catogery.set_sensitive(False)
			self.forsale.set_sensitive(False)
			self.height.set_sensitive(False)
			self.section.set_sensitive(False)
			self.sire.set_sensitive(False)
			self.dam.set_sensitive(False)
			self.blurb.set_sensitive(False)
			self.button_delete.set_sensitive(False)
			self.button_delete_horse.set_sensitive(False)
			self.processing("deleting horse",True)
			############################################################################################

	def process_update(self,event):
		self.processing("updating",False)
		# if this is a new photo:
		if self.new:
			#if this is a new horse
			if not self.horse_id:
				self.horse_id = self.mysql_update()
			else:
				self.mysql_update(self.horse_id)
			self.mysql_image_upload(self.horse_id)
			self.delete_event()
		# no new photo:
		if not self.new:
			self.mysql_update(self.horse_id)
			self.image_update("","update")
		self.processing("updating",True)

	def image_update(self,widget,action):
		image_id = self.currentimage
		if action:
			if action == "update":
				if(self.imagetitle.get_text()):
					self.mysql_put('UPDATE images SET caption="{caption}" WHERE image_id={image_id} LIMIT 1'.format(caption=self.text_in(self.imagetitle.get_text()), image_id=image_id))
			elif action == "delete":
				self.mysql_put('DELETE FROM images WHERE image_id={image_id} LIMIT 1'.format(image_id=image_id))


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

	def mysql_put(self,sql):
		cursor = self.conn.cursor()
		#print sql
		cursor.execute (sql)
		rows = cursor.fetchall()
		last_id = cursor.lastrowid
		cursor.close ()
		return rows,last_id

	def mysql_image_upload(self,horse_id):
		#if there was an image on the commandline
		if self.new:
			print horse_id
			print self.text_in(self.imagetitle.get_text())
			sql='INSERT INTO images (horse_id, image, caption) VALUES (%s,%s,%s)'
			args = (horse_id, self.imagebuffer.getvalue(), self.text_in(self.imagetitle.get_text()), )
			cursor = self.conn.cursor()
			cursor.execute (sql,args)
			cursor.close ()


	def dialog(self,reason):
		dialog = gtk.Dialog("Error",self.window,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_OK,gtk.RESPONSE_CLOSE))
		dialog.vbox.pack_start(gtk.Label(reason))
		dialog.show_all()
		dialog.run()
		dialog.destroy()

	def mysql_update(self,horse_id=None):

		#if the shortname or catogery entry boxes are empty
		if self.fullname.get_active_text() == '':
			self.dialog("you need to fill in atleast the \ncatogery section")
		else:
			# if no horse_id passed then assume its a new horse
			if horse_id:
				#not a new horse
				self.mysql_put(
				'UPDATE data SET fullname="{fullname}", for_sale="{for_sale}", section="{section}", height="{height}", sire="{sire}", dam="{dam}", blurb="{blurb}" WHERE horse_id="{horse_id}" LIMIT 1'.format(
				horse_id=horse_id, fullname=self.text_in(self.fullname.get_active_text()), for_sale=self.text_in(self.forsale.get_active_text()), section=self.text_in(self.section.get_active_text()),
				height=self.text_in(self.height.get_text()), sire=self.text_in(self.sire.get_text()), dam=self.text_in(self.dam.get_text()),
				blurb=self.text_in(self.blurb.get_buffer().get_text(self.blurb.get_buffer().get_start_iter(), self.blurb.get_buffer().get_end_iter()))))
			else:
				#new horse
				result = self.mysql_put('INSERT INTO data SET cat="{cat}", fullname="{fullname}", for_sale="{for_sale}", section="{section}", height="{height}", sire="{sire}", dam="{dam}", blurb="{blurb}"'.format(
				cat=self.text_in(self.catogery.get_active_text()), fullname=self.text_in(self.fullname.get_active_text()), for_sale=self.text_in(self.forsale.get_active_text()),
				section=self.text_in(self.section.get_active_text()), height=self.text_in(self.height.get_text()), sire=self.text_in(self.sire.get_text()), dam=self.text_in(self.dam.get_text()),
				blurb=self.text_in(self.blurb.get_buffer().get_text(self.blurb.get_buffer().get_start_iter(), self.blurb.get_buffer().get_end_iter()))))
				horse_id = result[1]
		return(horse_id)

	def mysql_connect(self):
		self.conn = MySQLdb.connect (host = self.host,user = self.user,passwd = self.password ,db = self.database)
#######
# misc
#######
	def text_in(self,text):
		if text:
			i = 1
			var = ["_","/","\'",";",",","\\"," ","\n"]
			for char in var:
				text = text.replace(char,"__"+str(i)+"_")
				i += 1
			text = text.strip()
			text = text.replace("&","&amp;")
			return text
		else:
			return ""

	def text_out(self,text):
		i = 2
		var = ["/","\'",";",",","\\"," ","\n"]
		for char in var:
			text = text.replace("__"+str(i)+"_",char)
			i += 1
		text = text.replace("__1_","_")
		text = text.replace("&amp;","&")
		return text

	def show_image(self,widget,image_id):
		if self.currentimage:
			self.image_update("","update")
		if image_id == "new":
			contents = self.imagebuffer.getvalue()
			self.imagetitle.set_text("")
		else:
			images = self.mysql_get("images","*","image_id = '"+ str(image_id) +"'")
			fd = StringIO.StringIO()
			fd.write(images[0]['image'])
			contents = fd.getvalue()
			fd.close()
			self.imagetitle.set_text(self.text_out(images[0]['caption']))
		loader = gtk.gdk.PixbufLoader()
		loader.write(contents, len(contents))
		pixbuf = loader.get_pixbuf()
		loader.close()
		self.image.set_from_pixbuf(pixbuf)
		self.image.show()
		self.currentimage = image_id

	def update_entry(self, widget):
		self.processing("loading",False)
		if self.currentimage:
			self.image_update("","update")
		rows = self.mysql_get("data","*","fullname = '"+self.text_in(self.fullname.get_active_text())+"'")
		if(len(rows) == 1):
			# set horse_id
			self.horse_id = str(rows[0]['horse_id'])
			if(rows[0]['cat']):
				self.catogery.set_active(self.cat_index.index(rows[0]['cat']))
			else:
				self.catogery.set_active(-1)

			if(rows[0]['for_sale']):
				if (self.text_out(rows[0]['for_sale']).capitalize() == "For sale"):
					self.forsale.set_active(1)
				elif (self.text_out(rows[0]['for_sale']).capitalize() == "Sold"):
					self.forsale.set_active(2)
				elif (self.text_out(rows[0]['for_sale']).capitalize() == "No"):
					self.forsale.set_active(0)
			else:
				self.forsale.set_active(0)

			if(rows[0]['height']):
				self.height.set_text(self.text_out(rows[0]['height']))

			if(rows[0]['section']):
				if (rows[0]['section'])== "sec__7_A":
					self.section.set_active(1)
				elif (rows[0]['section'])== "sec__7_B":
					self.section.set_active(2)
				else:
					self.section.set_active(0)
			else:
				self.section.set_active(0)

			if(rows[0]['sire']):
				self.sire.set_text(self.text_out(rows[0]['sire']))
			else:
				self.sire.set_text("")
			if(rows[0]['dam']):
				self.dam.set_text(self.text_out(rows[0]['dam']))
			else:
				self.dam.set_text("")

			blurbbuffer = self.blurb.get_buffer()
			if(rows[0]['blurb']):
				blurbbuffer.set_text(self.text_out(rows[0]['blurb']))
			else:
				blurbbuffer.set_text("")
			self.blurb.set_buffer(blurbbuffer)


			images = self.mysql_get("images","image_id","horse_id = '"+ self.horse_id +"'")
			#clear image buttons
			if self.imageset:
				for line in self.imageset:
					self.imageset[line].destroy()
				self.imageset.clear()
			for image in images:
				#make a button for each image
				self.imageset[str(image['image_id'])] = gtk.Button(str(image['image_id']))
				self.imageset[str(image['image_id'])].connect("clicked", self.show_image, image['image_id'])
				self.imagetopvbox.pack_start(self.imageset[str(image['image_id'])],True)
				self.imageset[str(image['image_id'])].show()
			if not self.new:
				#if not adding a new image
				#show the last one (its eaiser :P)
				self.show_image("",image['image_id'])
				self.currentimage = str(image['image_id'])
			#images
			self.imagetitle.set_sensitive(True)
			#general
			self.catogery.set_sensitive(True)
			self.forsale.set_sensitive(True)
			self.height.set_sensitive(True)
			self.section.set_sensitive(True)
			self.sire.set_sensitive(True)
			self.dam.set_sensitive(True)
			self.blurb.set_sensitive(True)
			if not self.new:
				if len(images) == 1:
					self.button_delete.set_sensitive(False)
				else:
					self.button_delete.set_sensitive(True)
				self.button_delete_horse.set_sensitive(True)

		else:
			if not self.new:
				if self.imageset:
					for line in self.imageset:
						self.imageset[line].destroy()
					self.imageset.clear()
				self.currentimage = None
				self.image.clear()
			self.sire.set_text("")
			self.dam.set_text("")
			self.horse_id = None
			self.catogery.set_active(-1)
		self.processing("loading",True)
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
		newimagebutton = gtk.Button("new")
		newimagebutton.connect("clicked", self.show_image,"new")
		self.imagetopvbox.pack_start(newimagebutton,True)
		newimagebutton.show()
		self.show_image("","new")


###########
# gui setup
###########
	def gui_setup(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title(self.host)
		self.window.set_default_size(700,790)
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
		# box for image preview
		self.imagetopvbox=gtk.VBox()
		imagetophbox.pack_start(self.imagetopvbox,False)
		self.imagetopvbox.pack_start(gtk.Label("image:"),False)

		#bottom box
		image_data_box = gtk.HBox()
		imagevbox.pack_start(image_data_box,False)
		image_data_box.pack_start(gtk.Label("image caption:"),False)
		self.imagetitle = gtk.Entry(40)
		image_data_box.pack_start(self.imagetitle,True)
		self.button_delete=gtk.Button("Delete image")
		self.button_delete.connect("clicked", self.image_update,"delete",)
		image_data_box.pack_start(self.button_delete,False)

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

		#full name
		vbox2.pack_start(gtk.Label("full name:"))
		self.fullname = gtk.combo_box_entry_new_text()

		fullnamehbox = gtk.HBox(False)
		vbox3.pack_start(fullnamehbox)
		fullnamehbox.pack_start(self.fullname,True)
		self.fullname.connect("changed", self.update_entry)
		#delete horse button
		self.button_delete_horse=gtk.Button("Delete Horse")
		self.button_delete_horse.connect("clicked", self.delete_horse,)
		fullnamehbox.pack_start(self.button_delete_horse,False)


		#catogery
		vbox2.pack_start(gtk.Label("catogery:"))
		self.catogery = gtk.combo_box_new_text()

		vbox3.pack_start(self.catogery)
		#section/for_sale/height

		vbox2.pack_start(gtk.Label("for sale?:"))
		self.forsale = gtk.combo_box_new_text()
		forsaleopts = ["No","For sale","Sold"]
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
		self.section = gtk.combo_box_new_text()
		sectionopts = ["","sec A","sec B"]
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
		actionbuttons = gtk.HBox()
		vbox1.pack_start(actionbuttons,False)
		self.exit = gtk.Button("exit")
		self.exit.connect("clicked", self.delete_event)
		actionbuttons.pack_start(self.exit,True)
		self.update = gtk.Button("update")
		# FIXME
		self.update.connect("clicked", self.process_update)
		actionbuttons.pack_start(self.update,True)
		self.progressbar = gtk.ProgressBar()
		#self.progressbar.set_no_show_all(True)
		actionbuttons.pack_start(self.progressbar)


		self.window.show_all()
		self.window.show()
######
# init
######
	def __init__(self):
		 gobject.idle_add(self.initstuff)


def main():
	gtk.main()
if __name__ == "__main__":
	upload_3 = upload_3()
	main()
