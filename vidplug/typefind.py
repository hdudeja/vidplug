import pygst
pygst.require("0.10")
import gst

import os,sys

def typefind(filename,callback,*args):
	"determine the audio/video types in 'filename', calling 'callback' with the results using supplied args."
	filename=os.path.abspath(filename)
	fsa=gst.element_factory_make("fakesink","asink")
	fsv=gst.element_factory_make("gdkpixbufsink","vidsink")
	pb=gst.element_factory_make("playbin2","player")
	pb.set_property("uri","file://"+filename)
	pb.set_property("audio-sink", fsa)
	pb.set_property("video-sink", fsv)
	def message_cb(bus,message,pb,audiosink,videosink,results,cb_num_in_list,callback,args,donecount):
		if message.type==gst.MESSAGE_TAG:
			d=message.parse_tag()
			if "video-codec" in d.keys():
				results["video"]={}
				results["video"]["codec"]=d["video-codec"]
			if "audio-codec" in d.keys():
				results["audio"]={}
				results["audio"]["codec"]=d["audio-codec"]
		elif message.type==gst.MESSAGE_STATE_CHANGED:
			if message.parse_state_changed()[1]==gst.STATE_PLAYING and message.src==pb:
				if len(donecount)==0:
					pos=pb.query_duration(gst.FORMAT_TIME,None)[0]/4
					pb.seek_simple(gst.Format(gst.FORMAT_TIME),gst.SEEK_FLAG_FLUSH,pos)
					donecount.append(None)
				else:
					error=None
					try:
						results["duration"]=pb.query_duration(gst.FORMAT_TIME,None)[0]
						results["pixbuf"]=videosink.get_property("last-pixbuf")
						if results.has_key("video"):
							caps_struct=videosink.get_static_pad("sink").get_negotiated_caps()[0]
							for key in caps_struct.keys():
								results["video"][key]=caps_struct[key]
						if results.has_key("audio"):
							caps_struct=audiosink.get_static_pad("sink").get_negotiated_caps()[0]
							for key in caps_struct.keys():
								results["audio"][key]=caps_struct[key]
					except:
						error="Python Programming Error! `%s'"%(str(sys.exc_info()[1]))
					finally:
						try:
							if error is not None:
								results=None
							callback(results,error,*args)
						finally:
							pb.set_state(gst.STATE_NULL)
							bus.disconnect(cb_num_in_list[0])
		elif message.type==gst.MESSAGE_ERROR:
			parsed=message.parse_error()
			error=""
			try:
				error=parsed[1].split('\n')[1]
			except:
				error=error.join(str(i) for i in [parsed])
			finally:
				try:
					callback(None,error,*args)
				finally:
					pb.set_state(gst.STATE_NULL)
					bus.disconnect(cb_num_in_list[0])

	results_dict={'file':filename}
	cbl=[]
	donecount=[]
	bus = pb.get_bus()
	bus.add_signal_watch()
	cb=bus.connect("message", message_cb,pb,fsa,fsv,results_dict,cbl,callback,args,donecount)
	cbl.append(cb)
	pb.set_state(gst.STATE_PLAYING)

