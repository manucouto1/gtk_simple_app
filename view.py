#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, Gdk, GdkPixbuf
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from PIL import Image
import gettext

from types import SimpleNamespace
import gettext
_ = gettext.gettext
N_ = gettext.ngettext

import io
import os
from itertools import tee

'''
es = gettext.translation('view', localedir='locale', languages=['es'])
es.install()

_ = es.gettext
N_ = es.ngettext
'''

class View(Gtk.Window):
    def init_window(self):
        win = Gtk.Window(title="IPM-p1")
        #self.set_size_request(1500, 700)
        self.win = win
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "IPM-p1"
        win.set_titlebar(hb)
        self.spinner = Gtk.Spinner()

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")
        box.add(self.spinner)
        hb.pack_end(box)
        self.hb = hb

        self.win.set_size_request(1300, 750)
        self.main_box = Main_box()
        self.video_box = Video_box()
        self.parent_box = Gtk.Box(spacing=6)
        self.build_view(self.main_box)

    def build_view(self, current_box):
        self.current_box = current_box
        self.parent_box.pack_start(self.current_box, True, True, 0)
        self.win.add(self.parent_box)

    def gtk_main(self):
        Gtk.main()
        
    def start_spinner(self):
        self.spinner.start()

    def stop_spinner(self):
        self.spinner.stop()

    def show_all(self):
        self.win.show_all()

    def workout_content_init(self):
        self.current_box.workout_init()

    def exercise_content_load(self, rows):
        self.current_box.load_exercises(rows)

    def video_content_init(self, selectedVideo, videoRoute):
        self.current_box.load_videos(selectedVideo, videoRoute)
        #self.show_all()

    def replace_widget(self, parent, current, new):
        self.current_box = new
        Gtk.Container.remove(parent, current)
        parent.pack_start(new, True, True, 0)

    ## Handler
    def connect_warning(self, callback):
        self.main_box.delete.connect('clicked', callback)
    def connect_close(self, callback):
        self.win.connect('delete-event', callback)
        
    ## close
    def main_quit(self, x, y):
        Gtk.main_quit(x, y)


class Main_box(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, spacing=6)

        self.next_click_rollback = False
        self.rollback_selected = None
        self.state = 0

        ## WORKOUT
        self.workouts_arrayData = []
        self.workouts_dictData = {}
        self.workouts_store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str)
        self.workout_entries = self.build_workout_entries()

        scrolled_window = Gtk.ScrolledWindow(expand=True)
        #scrolled_window.set_size_request(500, 700)
        scrolled_window.add(self.workout_entries)

        ## EXERCISES
        self.all_exercises_dicData = {}
        self.exercises_dictData = {}

        self.exercises_store = Gtk.ListStore(
            GdkPixbuf.Pixbuf, str, str, str, self.VideoInfo, self.DescriptionInfo)
        self.exercises_entries = self.build_exercises_entries()

        scrolled_window2 = Gtk.ScrolledWindow(expand=True)
        #scrolled_window2.set_size_request(575, 700)
        scrolled_window2.add(self.exercises_entries)

        ## MAIN Grid

        grid_master = Gtk.Grid(margin=10, column_spacing=10, row_spacing=10)
        grid_master.set_column_homogeneous(True)
        grid_master.set_row_homogeneous(True)

        grid1 = Gtk.Grid(margin=10, column_spacing=10, row_spacing=10)
        grid1.set_column_homogeneous(True)
        grid1.set_row_homogeneous(True)

        grid2 = Gtk.Grid(margin=10, column_spacing=10, row_spacing=10)
        grid2.set_column_homogeneous(True)
        grid2.set_row_homogeneous(True)

        grid1.attach(scrolled_window, 0, 0, 6, 12)
        grid2.attach(scrolled_window2, 0, 0, 6, 12)

        grid_master.attach(grid1, 0, 0, 6, 12)
        grid_master.attach(grid2, 6, 0, 8, 12)
        
        
        self.delete = Gtk.Button(label=_("Delete Workout"), use_underline=True)
        Gtk.Widget.set_sensitive(self.delete, False)
        self.delete.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        grid1.attach(self.delete, 0, 12, 3, 1)

        self.reorder = Gtk.Button(label=_("Reorder"), use_underline=True)
        Gtk.Widget.set_sensitive(self.reorder, False)
        grid1.attach(self.reorder, 3, 12, 3, 1)
        
        self.video = Gtk.Button(label=_("Start Training"), use_underline=True)
        Gtk.Widget.set_sensitive(self.video, False)
        self.video.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        grid2.attach(self.video, 0, 12, 6, 1)

        ######
        ###### STATE = 1
        self.cache_store = None
        self.selected_to_reorder = None

        self.up = Gtk.Button(label=_("Up"), use_underline=True)
        Gtk.Widget.set_sensitive(self.up, False)
        self.up.connect('clicked', self.on_reorder_up_clicked)
        # Gdk.KEY_uparrow
        
        self.down = Gtk.Button(label=_("Down"), use_underline=True)
        Gtk.Widget.set_sensitive(self.down, False)
        self.down.connect('clicked', self.on_reorder_down_clicked)
        #Gdk.KEY_downarrow

        self.done = Gtk.Button(label=_("Done"), use_underline=True)
        self.done.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.done.connect('clicked', self.on_done_reorder_clicked)

        self.cancel = Gtk.Button(label=_("Cancel"), use_underline=True)
        self.cancel.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        self.cancel.connect('clicked', self.on_cancel_reorder_clicked)
        ######
        ######

        self.grid1 = grid1
        self.grid2 = grid2

        self.pack_start(grid_master, True, True, 0)

        ## WORKOUTS

    def build_workout_entries(self):
        entries = Gtk.TreeView(self.workouts_store, headers_visible=True)
        self.workout_tree_selection = entries.get_selection()
        self.workout_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)

        renderer0 = Gtk.CellRendererPixbuf()
        column0 = Gtk.TreeViewColumn(_("image"), renderer0, pixbuf=0)
        Gtk.TreeViewColumn.set_alignment(column0, 0.5)

        renderer1 = Gtk.CellRendererText()
        renderer1.set_alignment(0.5, 0.5)
        column1 = Gtk.TreeViewColumn(_("activity"), renderer1, text=1)
        column1.set_min_width(100)
        Gtk.TreeViewColumn.set_alignment(column1, 0.5)

        renderer2 = Gtk.CellRendererText()
        renderer2.set_alignment(0.5, 0.5)
        column2 = Gtk.TreeViewColumn(_("date"), renderer2, text=2)
        Gtk.TreeViewColumn.set_alignment(column2, 0.5)

        entries.append_column(column0)
        entries.append_column(column1)
        entries.append_column(column2)
        return entries

    def workout_init(self):
        self.workouts_store.clear()
        for data in self.workouts_arrayData:
            print(" * "+data[1])
            self.workouts_store.append([data[0], data[1], data[2], data[3]])

    def workouts_data_to_row(self, data):
        if data.id not in self.workouts_dictData:
            self.workouts_dictData[data.id] = data.exercises
            im = Image.open(io.BytesIO(data.image.fromStringToBinary()))
            im.save("downloads/images/"+data.workout+".png")
            image = self.image2pixbuf(
                im, "downloads/images/"+data.workout+".png", 4.5, 4, False)
        return [image, data.workout, data.date, data.id]

    ## EXERCISES

    def build_exercises_entries(self):
        entries = Gtk.TreeView(self.exercises_store, headers_visible=True)
        self.exercises_tree_selection = entries.get_selection()
        self.exercises_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.exercises_tree_selection.connect(
            'changed', self.on_exercises_selection_changed)

        renderer0 = Gtk.CellRendererPixbuf()
        column0 = Gtk.TreeViewColumn(_("image"), renderer0, pixbuf=0)
        column0.set_min_width(160)
        Gtk.TreeViewColumn.set_alignment(column0, 0.5)

        renderer1 = Gtk.CellRendererText()
        renderer1.set_alignment(0.5, 0.5)
        column1 = Gtk.TreeViewColumn(
            _("exercise"), renderer1, text=1)
        column1.set_min_width(220)
        Gtk.TreeViewColumn.set_alignment(column1, 0.5)

        renderer2 = Gtk.CellRendererText()
        renderer2.set_alignment(0.5, 0.5)
        column2 = Gtk.TreeViewColumn(
            _("repetitions"), renderer2, text=2)
        column2.set_min_width(90)
        Gtk.TreeViewColumn.set_alignment(column2, 0.5)

        renderer3 = Gtk.CellRendererText()
        renderer3.set_alignment(0.5, 0.5)
        column3 = Gtk.TreeViewColumn(
            _("in Workouts"), renderer2, text=3)
        Gtk.TreeViewColumn.set_alignment(column3, 0.5)

        entries.append_column(column0)
        entries.append_column(column1)
        entries.append_column(column2)
        entries.append_column(column3)

        return entries

    def load_exercises(self, rows):
        self.exercises_store.clear()
        for row in rows:
            self.exercises_store.append(row)

    def get_image(self, fileName, rutaImagen, is404):
        im = Image.open(io.BytesIO(rutaImagen))
        im.save("downloads/images/"+fileName+".png")
        if is404:
            image = self.image2pixbuf(  # 4, 5 bien
                im, "downloads/images/"+fileName+".png", 6, 7, False)
        else:
            image = self.image2pixbuf(
                im, "downloads/images/"+fileName+".png", 3.8, 3.8, False)

        return image

    def exercises_data_to_dic(self, exercise):
        image = self.get_image(
            exercise.name, exercise.image.fromStringToBinary(), exercise.notReduce)
        video = self.VideoInfo(exercise.video)
        return self.ExerciseInfo(exercise.id, image, exercise.name, exercise.description, video)

    def exercises_data_to_row(self, data, repetitions):
        store = []
        if not data.description:
            store.append([str(404),  "No description available"])
        else:
            count = 0
            for entry in data.description:
                if entry is not None:
                    for part in entry.split("."):
                        if part.strip():
                            count += 1
                            store.append([str(count), part.strip()+"."])

        descriptionInfo = self.DescriptionInfo(store)

        return data.info_to_row(repetitions, descriptionInfo)
    

    def error_dialog(self, operacion):
        message = "The " + operacion + " Failed!"
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.OK, _(message))
        dialog.format_secondary_text(_("Rollback will be applied"))
        dialog.run()
        print("ERROR dialog closed")

        dialog.destroy()

    ## UTILS
    class ExerciseInfo():
        def __init__(self, id, image, name,  description,  video):
            self.id = id
            self.image = image
            self.name = name
            self.description = description
            self.video = video

        def set_workouts_ocurance(self, workouts_ocurance):
            self.ocurrencia = workouts_ocurance

        def info_to_row(self, repetitions, scrolled_window):
            return [self.image, self.name, repetitions, self.ocurrencia, self.video, scrolled_window]
        
        def row_to_info(self, row,  id, description):
            self.id = id
            self.image = row[0]
            self.name = row[1]
            self.ocurrencia = row[3]
            self.video = row[4]
            #self.description = description #Podría obtenerse
            


    class VideoInfo(GObject.GObject):
        def __init__(self, video):
            GObject.GObject.__init__(self)
            self.video = video

    class DescriptionInfo(GObject.GObject):
        def __init__(self, entries):
            GObject.GObject.__init__(self)
            self.entries = entries

    def image2pixbuf(self, im, imageName, redTaxW, redTaxH, preserve):
        data = im.tobytes()
        w, h = im.size
        data = GLib.Bytes.new(data)
        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            imageName, width=w/redTaxW, height=h/redTaxH, preserve_aspect_ratio=False)
        return pix
    
    def delete_selected_row(self, row):
        (store, it) = row
        store.remove(it)
        Gtk.Widget.set_sensitive(self.delete, False)
        Gtk.Widget.set_sensitive(self.reorder, False)
    
    ## CONNECTORS

    def connect_exercises(self, callback):
        self.workout_tree_selection.connect('changed', callback)

    def connect_watch(self, callback):
        self.video.connect('clicked', callback)

    def connect_reorder(self, callback):
        self.reorder.connect('clicked', callback)

    ## EVENT HANDLERS
    
    def start_spinner(self):
        self.video.set_sensitive(False)
        self.video.set_label(_("Loading..."))

    def stop_spinner(self):
        self.video.set_sensitive(True)
        self.video.set_label(_("Start Training"))

    def on_workout_selection_changed(self, tree_selection):
        (store, iter) = tree_selection.get_selected()
        if iter is not None:
            sWorkout = Gtk.TreeModel.get_value(store, iter, 1)
            id = Gtk.TreeModel.get_value(store, iter, 3)
            Gtk.Widget.set_sensitive(self.delete, True)
            Gtk.Widget.set_sensitive(self.reorder, True)
            self.selectedWorkout = {"id": id, "workout": sWorkout,
                                    "exercises": self.workouts_dictData[id], "row": (store, iter)}


    def on_exercises_selection_changed(self, tree_selection):
        if self.state == 0: #INITIAL STATE
            Gtk.Widget.set_sensitive(self.video, True)
            (store, iter) = tree_selection.get_selected()
            if iter is not None:
                Gtk.Widget.set_sensitive(self.video, True)
                value3 = Gtk.TreeModel.get_value(store, iter, 4)
                value4 = Gtk.TreeModel.get_value(store, iter, 5)
                self.selectedVideo = {"video": value3.video, "description": value4}
        if self.state == 1:  # REORDERING STATE
            (store, iter) = tree_selection.get_selected()
            if iter:
                Gtk.Widget.set_sensitive(self.up, True)
                Gtk.Widget.set_sensitive(self.down, True)
                self.selected_to_reorder = (store, iter)

    
    def on_reorder_clicked(self):
        self.grid2.remove_row(12)
        self.grid2.attach(self.up, 0, 12, 3, 1)
        self.grid2.attach(self.down, 3, 12, 3, 1)

        self.grid1.remove_row(12)
        self.grid1.attach(self.cancel, 0, 12, 3, 1)
        self.grid1.attach(self.done, 3, 12, 3, 1)
        self.state = 1
        
        self.exercises_tree_selection.set_mode(Gtk.SelectionMode.NONE)
        self.workout_tree_selection.set_mode(Gtk.SelectionMode.NONE)
        self.exercises_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)

        (_, iter) = self.exercises_tree_selection.get_selected()
        self.cache_store = self.selectedWorkout["exercises"]
        
        if iter:
            print("fallo 1")
            Gtk.Widget.set_sensitive(self.up, True)
            Gtk.Widget.set_sensitive(self.down, True)
        
    def on_cancel_reorder_clicked(self, w):
        self.grid2.remove_row(12)
        self.grid2.attach(self.video, 0, 12, 6, 1)

        self.grid1.remove_row(12)
        self.grid1.attach(self.delete, 0, 12, 3, 1)
        self.grid1.attach(self.reorder, 3, 12, 3, 1)

        self.state = 0
        self.workout_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.exercises_store.clear()
        
        for exInf in self.cache_store:
            print("EXINF ---- ")
            print(exInf)
            if exInf[0] in self.all_exercises_dicData:
                row = self.exercises_data_to_row(self.all_exercises_dicData[exInf[0]], exInf[1])
                self.exercises_store.append(row)
        
    def on_done_reorder_clicked(self, w):
        self.grid2.remove_row(12)
        self.grid2.attach(self.video, 0, 12, 6, 1)

        self.grid1.remove_row(12)
        self.grid1.attach(self.delete, 0, 12, 3, 1)
        self.grid1.attach(self.reorder, 3, 12, 3, 1)

        self.state = 0
        self.workout_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)

        if self.selected_to_reorder:
            (store, _) = self.selected_to_reorder
            
            id = self.selectedWorkout["id"]
            aux = []

            for row in store:
                print(row[1])
                aux.append([row[1],row[2]])
            self.workouts_dictData[id] = aux

    
    def on_reorder_up_clicked(self, w):
        (store, iter) = self.selected_to_reorder
        it_prev = store.iter_previous(iter)
        if it_prev:
            store.swap(iter,it_prev)
        print("Up clicked")

    def on_reorder_down_clicked(self, w):
        (store, iter) = self.selected_to_reorder
        it_next = store.iter_next(iter)
        if it_next:
            store.swap(iter, it_next)
        print("Down clicked")

    def on_delete_clicked(self, workout):
        Gtk.Widget.set_sensitive(self.delete, False)
        Gtk.Widget.set_sensitive(self.reorder, False)
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.WARNING,
                                   Gtk.ButtonsType.OK_CANCEL, _("WARNING Are you shure?"))
        dialog.format_secondary_text(
            _(workout+" Will be deleted permanently."))
        response = dialog.run()
        aux = False
        if response == Gtk.ResponseType.OK:
            aux = True
            print("WARN dialog closed by clicking OK button")
        elif response == Gtk.ResponseType.CANCEL:
            Gtk.Widget.set_sensitive(self.delete, True)
            Gtk.Widget.set_sensitive(self.reorder, True)
            aux = False
            print("WARN dialog closed by clicking CANCEL button")
        dialog.destroy()

        return aux

    def _on_delete_failure_rollback(self, event):
        GLib.idle_add(self.rollback_worker, event)

    def rollback_worker(self, event):
        self.error_dialog(_("Database destructive"))
        self.workout_tree_selection.set_mode(Gtk.SelectionMode.NONE)
        self.workout_init()
        self.workout_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        event.set()

class Video_box(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, spacing=6)
        #GObject.threads_init()
        Gst.init(None)
        Gst.init_check(None)

        self.playerDic = {}
        self.video_box = Gtk.Box(spacing=6)

        self.description_store = Gtk.ListStore(str, str)
        self.description_entries = self.build_description_entries()

        scrolled_window = Gtk.ScrolledWindow(expand=True)
        #scrolled_window.set_size_request(650, 50)
        scrolled_window.add(self.description_entries)

        grid = Gtk.Grid(margin=20, column_spacing=10, row_spacing=20)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)

        grid.attach(self.video_box, 0, 0, 8, 8)
        grid.attach(scrolled_window, 0, 9, 8, 2)

        self.back = Gtk.Button(label=_("Back to Exercises"), use_underline=True)
        Gtk.Widget.set_sensitive(self.back, True)
        grid.attach(self.back, 0, 8, 4, 1)

        self.play = Gtk.Button(label=_("Play"), use_underline=True)
        self.play.connect('clicked', self._on_play_stop)
        Gtk.Widget.set_sensitive(self.play, False)
        grid.attach(self.play, 4, 8, 4, 1)

        self.grid = grid
        self.pack_start(grid, True, True, 0)

        self.pipeline = Gst.ElementFactory.make("playbin", "player")
        self.sink = Gst.ElementFactory.make("gtksink")
        self.video_box.pack_start(self.sink.props.widget, True, True, 0)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

    def build_description_entries(self):
        entries = Gtk.TreeView(self.description_store, headers_visible=False)

        renderer1 = Gtk.CellRendererText()
        column1 = Gtk.TreeViewColumn(_("count"), renderer1, text=0)

        renderer2 = Gtk.CellRendererText()
        column2 = Gtk.TreeViewColumn(_("description"), renderer2, text=1)

        entries.append_column(column1)
        entries.append_column(column2)

        return entries

    def load_description(self, exercise_description):
        self.description_store.clear()
        for description in exercise_description.entries:
            print("description -> "+description[1])
            self.description_store.append(description)

    def load_videos(self, video_uri, http_route):
        try:
            if http_route not in self.playerDic:
                rutaBase = os.getcwd()
                filepath = os.path.join(rutaBase, video_uri)
                filepath = os.path.realpath(filepath)
                self.playerDic[http_route] = {
                    "path": filepath}  # , "description": exerciseDescription
            else:
                filepath = self.playerDic[http_route]["path"]
                #description = self.playerDic[http_route]["description"]
        except Exception:
            print("load_video EXCEPTION")

        print(filepath)
        try:
            self.pipeline.set_property("uri", "file://"+filepath)
            self.pipeline.set_property("video-sink", self.sink)
            self.pipeline.set_state(Gst.State.PAUSED)
            Gtk.Widget.set_sensitive(self.play, True)
        except Exception:
            print("load_video EXCEPTION")

    def _on_load_video_finish(self, event):
        GLib.idle_add(self.activate_play, event)
        
    def activate_play(self, event):
        self.play.set_sensitive(True)
        event.set()

    def _on_play_stop(self, w):
        print(self.play.get_label())
        if self.play.get_label() == "Play":
            print("Playing...")
            self.play.set_label(_("Stop"))
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("Stoped...")
            self.pipeline.set_state(Gst.State.NULL)
            self.play.set_label(_("Play"))

    def _on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
            self.play.set_label(_("Play"))
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s", err, debug)
            self.play.set_label(_("Play"))

    def connect_back(self, callback):
        self.back.connect('clicked', callback)

    def clean(self):
        self.pipeline.set_state(Gst.State.NULL)
        #self.grid.remove_row(9) #Podría no ser necesario
        self.play.set_label(_("Play"))
        print("Back click")
