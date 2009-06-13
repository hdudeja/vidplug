import gtk
import gobject
import gst

class Player():
	def __init__(self,window_xid,rescale_cb,update_cb):
		self.xid=window_xid
		self.rescale_cb=rescale_cb
		self.update_cb=update_cb
		self.playbin = gst.element_factory_make("playbin", "player")
		self.videosink = gst.element_factory_make("autovideosink", "video-output")
		self.playbin.set_property("video-sink", self.videosink)
		bus=self.playbin.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect("sync-message::element", self.on_sync_message)
		self.timeout_id=None
		self.duration=None
	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == "prepare-xwindow-id":
			imagesink = message.src
			imagesink.set_property("force-aspect-ratio", True)
			imagesink.set_xwindow_id(self.xid)
	def pos_cb_set(self,on=True):
		if self.timeout_id:
			gobject.source_remove(self.timeout_id)
		self.timeout_id=None
		if on:
			self.timeout_id=gobject.timeout_add(1000,self.cb_pos)
	def play(self):
		self.playbin.set_state(gst.STATE_PLAYING)
		self.pos_cb_set(True)
	def pause(self):
		self.playbin.set_state(gst.STATE_PAUSED)
		self.pos_cb_set(False)
	def playpause(self):
		state=self.playbin.get_state()[1]
		if state is not gst.STATE_PLAYING:
			state=gst.STATE_PLAYING
		else:
			state=gst.STATE_PAUSED
		self.playbin.set_state(state)
		self.pos_cb_set(False if state==gst.STATE_PLAYING else False)
	def reset(self):
		self.playbin.set_state(gst.STATE_NULL)
		self.pos_cb_set(False)
		self.playbin.set_state(gst.STATE_PAUSED)
	def set_source(self,filename):
		self.reset()
		self.playbin.set_property("uri","file://"+filename)
		self.reset()
	def destroy(self):
		self.playbin.set_state(gst.STATE_NULL)
	def cb_pos(self):
		duration=None
		pos=None
		try:
			duration=self.playbin.query_duration(gst.FORMAT_TIME,None)[0]
			duration=float(duration/1000000)/1000.0
		except gst.QueryError:
			pass
		try:
			pos=self.playbin.query_position(gst.FORMAT_TIME,None)[0]
			pos=float(pos/1000000)/1000.0
		except gst.QueryError:
			pass
		if duration and not duration==self.duration:
			self.rescale_cb(duration)
			self.duration=duration
		if pos:
			self.update_cb(pos)
		return True
	def seek(self,pos):
		self.playbin.seek_simple(gst.Format(gst.FORMAT_TIME), gst.SEEK_FLAG_FLUSH, pos*1000000000)

class Interface():
	def __init__(self):
		self.builder=gtk.Builder()
		self.builder.add_from_file("interface.glade")
		window=self.builder.get_object("MainWindow")
		window.connect("destroy",self.on_destroy)
		window.show()
		self.builder.get_object("AddRealFile").connect("activate",self.on_AddRealFile)
		self.builder.get_object("RemRealFile").connect("activate",self.on_RemRealFile)
		self.builder.get_object("PreviewPlay").connect("activate",self.on_PreviewPlay)
		self.builder.get_object("PreviewPause").connect("activate",self.on_PreviewPause)
		self.builder.get_object("PreviewStop").connect("activate",self.on_PreviewStop)
		self.source_file_dialog=gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		self.source_file_dialog.set_default_response(gtk.RESPONSE_OK)
		self.init_real_file_store()
		self.init_virt_file_store()
		self.player=Player(self.builder.get_object("VideoPreview").window.xid,self.slider_rescale_cb,self.slider_update_cb)
		self.player_slider=self.builder.get_object("PlayerSlider")
		self.player_slider.set_update_policy(gtk.UPDATE_CONTINUOUS)
		self.player_slider.set_property("draw-value",False)
		self.player_slider.connect("change-value",self.cb_player_slider_changed)

	def init_real_file_store(self):
		tv=self.builder.get_object("RealFilesView")
		ts=gtk.ListStore(gobject.TYPE_STRING)
		tv.set_property("model",ts)
		self.real_files_store=ts
		tv.append_column(gtk.TreeViewColumn("Filename",gtk.CellRendererText(),text=0))
		self.real_files_dict={}
		self.real_files_view=tv

	def init_virt_file_store(self):
		tv=self.builder.get_object("VirtFilesView")
		ts=gtk.ListStore(gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)
		tv.set_property("model",ts)
		self.virt_files_store=ts
		tv.append_column(gtk.TreeViewColumn("Name",gtk.CellRendererText(),text=1))
		self.virt_files_dict={}
		self.virt_files_view=tv

	def on_AddRealFile(self,*args):
		try:
			response = self.source_file_dialog.run()
			if response == gtk.RESPONSE_OK:
				fn=self.source_file_dialog.get_filename()
				if not self.real_files_dict.has_key(fn):
					self.real_files_store.append((fn,))
					self.real_files_dict[fn]=None
		finally:
			self.source_file_dialog.hide()

	def on_RemRealFile(self,*args):
		path=self.real_files_view.get_cursor()[0]
		if path is not None:
			iter=self.real_files_store.get_iter(path)
			fn=self.real_files_store.get(iter,0)[0]
			self.real_files_store.remove(iter)
			self.real_files_dict.pop(fn)
			pos=path[0]-1
			if pos>=0:
				self.real_files_view.set_cursor((pos,))
	def on_PreviewPlay(self,*args):
		self.on_PreviewStop()
		path=self.real_files_view.get_cursor()[0]
		if path is not None:
			iter=self.real_files_store.get_iter(path)
			fn=self.real_files_store.get(iter,0)[0]
			self.player.set_source(fn)
			self.player.play()
	def on_PreviewPause(self,*args):
		self.player.playpause()
	def on_PreviewStop(self,*args):
		self.player.reset()

	def slider_rescale_cb(self,size):
		self.player_slider.set_range(0.0,size)
		adj=gtk.Adjustment(value=0.0,
				lower=0.0, upper=size,
				step_incr=0.01, page_incr=0.1, page_size=0.1)
		self.player_slider.set_adjustment(adj)

	def slider_update_cb(self,pos):
		self.player_slider.set_value(pos)
	
	def cb_player_slider_changed(self,widget,type,pos):
		new_pos=min(pos,widget.get_adjustment().get_property("upper"))
		self.player.seek(new_pos)

	def on_destroy(self,*args):
		self.player.destroy()
		gtk.main_quit()


Interface()

gtk.gdk.threads_init()
gtk.main()
