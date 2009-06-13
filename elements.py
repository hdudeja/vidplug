import pygst
pygst.require("0.10")
import gst

import gtk
import gobject

class PluginList(gtk.ScrolledWindow):
	def __init__(self):
		self.store=gtk.ListStore(gobject.TYPE_PYOBJECT,gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)
		gtk.ScrolledWindow.__init__(self)
		self.view=gtk.TreeView(self.store)
		column=gtk.TreeViewColumn("Name",gtk.CellRendererText(),text=1)
		column.connect("clicked",self.cb_sort,1)
		self.view.append_column(column)
		column=gtk.TreeViewColumn("Type",gtk.CellRendererText(),text=3)
		column.connect("clicked",self.cb_sort,3)
		self.view.append_column(column)
		self.view.append_column(gtk.TreeViewColumn("Description",gtk.CellRendererText(),text=2))
		self.add(self.view)
		for fact in gst.registry_get_default().get_feature_list(gst.TYPE_ELEMENT_FACTORY):
			self.store.append((fact,fact.get_name(),fact.get_description(),fact.get_klass()))
		#print gst.registry_get_default().get_feature_list(gst.TYPE_ELEMENT_FACTORY)[40].get_static_pad_templates()[1].get_caps()
		self.store.set_sort_column_id(1,gtk.SORT_ASCENDING)
		self.store.set_sort_column_id(3,gtk.SORT_ASCENDING)
		self.view.connect("row-activated",self.cb_activated)
		self.view.set_property("reorderable",True)
		self.view.set_property("headers-clickable",True)
	def cb_activated(self,view,path,column):
		iter=self.store.get_iter(path)
		factory=self.store.get(iter,0)[0]
		print 
		print "-------------------"
		print factory.get_name()
		print factory.get_description()
		print 
		print "Sources"
		for p in [p for p in factory.get_static_pad_templates() if p.direction==gst.PAD_SRC]:
			print "%s: %s"%(p.name_template,p.get_caps())
			print
		print 
		print "Sinks"
		for p in [p for p in factory.get_static_pad_templates() if p.direction==gst.PAD_SINK]:
			print "%s: %s"%(p.name_template,p.get_caps())
			print
	def cb_sort(self,column,col_num):
		#get the current sort indicator on this item, flipping it if it was the most recent search
		#otherise use ascending
		dir=gtk.SORT_ASCENDING
		if column.get_property("sort-indicator"):
			if column.get_property("sort-order")==gtk.SORT_ASCENDING:
				dir=gtk.SORT_DESCENDING
			else:
				dir=gtk.SORT_ASCENDING
		for col in self.view.get_columns():
			col.set_property("sort-indicator",False)
		self.store.set_sort_column_id(col_num,dir)
		column.set_property("sort-order",dir)
		column.set_property("sort-indicator",True)



class PluginListWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)
		self.connect("destroy",gtk.main_quit)
		self.add(PluginList())

w=PluginListWindow()
w.show_all()
gtk.main()

