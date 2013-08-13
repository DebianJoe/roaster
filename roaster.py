#!/usr/bin/env python
#
# Copyright (C) 2007, 2008, 2009 Jan Michael Alonzo <jmalonzo@gmai.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# TODO:
#
# * fix tab relabelling
# * search page interface
# * custom button - w/o margins/padding to make tabs thin

from gettext import gettext as _

import sys
import os
import gobject
import gtk
import pango
import webkit
import urllib
import simplejson
import ConfigParser


ABOUT_PAGE = """
<html><head><title>PyWebKitGtk - About</title></head><body>
<h1>Welcome to <code>webbrowser.py</code></h1>
<p><a
href="http://code.google.com/p/pywebkitgtk/">http://code.google.com/p/pywebkitgtk/</a><br/>
</p>
</body></html>
"""

INFO_PAGE = """
<html><head><title>Roaster - About</title></head><body>
<h1>Welcome to <code>Roaster</code></h1>
<p><a href=http://www.pclinuxos.com/forum/index.php/topic,89031.0.html>A PCLinuxOS community project</a><br/>
</p>
<p>modified by Julius Hader <bacon@linuxbbq.org> for LinuxBBQ</p>
<p>further modified and FUBAR by Joe Brock <DebianJoe@linuxbbq.org></p>
</body></html>
"""
#Set Up config reading for global options

Config = ConfigParser.ConfigParser()
Config.read('/etc/roaster.conf')
Config.read(os.path.expanduser('~/.roaster.conf'))

# DEFAULT_PAGE can be overridden at the command line
DEFAULT_PAGE = Config.get("default", "d_page")
HOME_PAGE = Config.get("homepage", "homepage")
SEARCH_PAGE = "http://www.google.com/"
MIN_FONT_SIZE = float(Config.get("default", "min_font_size"))
DEFAULT_ZOOM = float(Config.get("default", "zoom"))
LANGUAGE = "en"

class BBToolbar(gtk.Toolbar):

    __gsignals__ = {
        "refresh-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "go-back-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "go-forward-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "zoom-in-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "zoom-out-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "go-home-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "google-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "load-requested": (gobject.SIGNAL_RUN_FIRST,
                               gobject.TYPE_NONE,
                               (gobject.TYPE_STRING,)),
        "new-tab-requested": (gobject.SIGNAL_RUN_FIRST,
                                  gobject.TYPE_NONE, ()),
        "info-dialog-requested": (gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE, ()),
        }


    def __init__(self, location_enabled=True, toolbar_enabled=True):
        gtk.Toolbar.__init__(self)

        if toolbar_enabled:

            if location_enabled:
                # location entry
                self._entry = gtk.Entry()
                self._entry.connect('activate', self._entry_activate_cb)
                entry_item = gtk.ToolItem()
                entry_item.set_expand(True)
                entry_item.add(self._entry)
                self._entry.show()
                self.insert(entry_item, -1)
                entry_item.show()

    def _refresh_cb(self, button):
        self.emit("load-requested", self._entry.props.text)

    def _go_back_cb(self, button):
        self.emit("go-back-requested")

    def _go_forward_cb(self, button):
        self.emit("go-forward-requested")

    def _zoom_in_cb(self, button):
        self.emit("zoom-in-requested")

    def _zoom_out_cb(self, button):
        self.emit("zoom-out-requested")

    def _google_cb(self, text):
        self.emit("google-requested")

    def location_set_text (self, text):
        self._entry.set_text(text)

    def _entry_activate_cb(self, entry):
        self.emit("load-requested", self._entry.props.text)

    def _add_tab_cb(self, button):
        self.emit("new-tab-requested")


class WebKitView(webkit.WebView):

    def __init__(self):
        webkit.WebView.__init__(self)
        settings = self.get_settings()
        settings.set_property("enable-developer-extras", True)
        settings.set_property("minimum-font-size", MIN_FONT_SIZE)
        self.set_zoom_level(DEFAULT_ZOOM)

        # scale other content besides from text as well
        self.set_full_content_zoom(True)

        # make sure the items will be added in the end
        # hence the reason for the connect_after
        self.connect_after("populate-popup", self.populate_popup)
        self.set_settings(settings)

    def populate_popup(self, view, menu):

        # zoom buttons
        zoom_in = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN)
        zoom_in.connect('activate', zoom_in_cb, view)
        menu.append(zoom_in)

        zoom_out = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT)
        zoom_out.connect('activate', zoom_out_cb, view)
        menu.append(zoom_out)

        roaster_exit = gtk.MenuItem("Exit Roaster")
        roaster_exit.connect('activate', exit_roast)
        menu.append(roaster_exit)

        menu.append(gtk.SeparatorMenuItem())

        menu.show_all()
        return False

class TabLabel (gtk.HBox):
    """A class for Tab labels"""

    __gsignals__ = {
        "close": (gobject.SIGNAL_RUN_FIRST,
                  gobject.TYPE_NONE,
                  (gobject.TYPE_OBJECT,))
        }

    def __init__ (self, title, child):
        """initialize the tab label"""
        gtk.HBox.__init__(self, False, 4)
        self.title = title
        self.child = child
        self.label = gtk.Label(title)
        self.label.props.max_width_chars = 30
        self.label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.label.set_alignment(0.0, 0.5)

        icon = gtk.image_new_from_stock(gtk.STOCK_ORIENTATION_PORTRAIT, gtk.ICON_SIZE_BUTTON)
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        close_button = gtk.Button()
        close_button.set_relief(gtk.RELIEF_NONE)
        close_button.connect("clicked", self._close_tab, child)
        close_button.set_image(close_image)
        self.pack_start(icon, False, False, 0)
        self.pack_start(self.label, True, True, 0)
        self.pack_start(close_button, False, False, 0)

        self.set_data("label", self.label)
        self.set_data("close-button", close_button)
        self.connect("style-set", tab_label_style_set_cb)

    def set_label (self, text):
        """sets the text of this label"""
        self.label.set_label(text)

    def _close_tab (self, widget, child):
        self.emit("close", child)

def tab_label_style_set_cb (tab_label, style):
    context = tab_label.get_pango_context()
    metrics = context.get_metrics(tab_label.style.font_desc, context.get_language())
    char_width = metrics.get_approximate_digit_width()
    (width, height) = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
    tab_label.set_size_request(16 * pango.PIXELS(char_width) + 2 * width,
                               pango.PIXELS(metrics.get_ascent() +
    metrics.get_descent()) +2)

class TabView (gtk.Notebook):

    __gsignals__ = {
        "focus-view-title-changed": (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_OBJECT, gobject.TYPE_STRING,)),
        "progress-changed": (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_OBJECT, gobject.TYPE_STRING,)),
        "hover-changed": (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_OBJECT, gobject.TYPE_STRING,)),
        "new-window-requested": (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_OBJECT,)),
        "go-home-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        }

    def __init__ (self):
        """initialize the tab_content"""
        gtk.Notebook.__init__(self)
        self.props.scrollable = True
        self.props.homogeneous = True
        self.connect("switch-page", self._switch_page)

        self.show_all()
        self._hovered_uri = None

    def load_uri (self, text):
        """load the given uri in the current web view"""
        child = self.get_nth_page(self.get_current_page())
        view = child.get_child()
        frame = view.get_main_frame()
        if frame.get_uri() == "about:blank":
            _close_tab(None, child)
            self.new_tab(text)
        else:
            view.open(text)
        self.emit("focus-view-title-changed", frame, text)

    def new_tab_with_webview (self, webview):
        """creates a new tab with the given webview as its child"""
        self._construct_tab_content(webview)

    def new_tab (self, url):
        """creates a new page in a new tab"""
        # create the tab content
        browser = WebKitView()
        self._construct_tab_content(browser, url)

    def _construct_tab_content (self, web_view, url):
        web_view.connect("hovering-over-link", self._hovering_over_link_cb)
        web_view.connect("populate-popup", self._populate_page_popup_cb)
        web_view.connect("load-finished", self._view_load_finished_cb)
        web_view.connect("create-web-view", self._new_web_view_request_cb)
        web_view.connect("title-changed", self._title_changed_cb)
        web_view.connect("load-progress-changed", self._notify_progress_cb)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.add(web_view)
        scrolled_window.show_all()

        # create the tab
        if not url:
            label = TabLabel("New Tab", scrolled_window)
        else:
            label = TabLabel(url, scrolled_window)
        label.connect("close", self._close_tab)
        label.show_all()

        new_tab_number = self.append_page(scrolled_window, label)
        self.set_tab_label_packing(scrolled_window, False, False, gtk.PACK_START)
        self.set_tab_label(scrolled_window, label)

        # hide the tab if there's only one
        self.set_show_tabs(self.get_n_pages() > 1)

        self.show_all()
        self.set_current_page(new_tab_number)

        # load the content
        self._hovered_uri = None
        if not url:
            url = ""
            #info_dialog_cb(self, url)
        else:
            web_view.load_uri(url)

    def _populate_page_popup_cb(self, view, menu):
        # misc
        if self._hovered_uri:
            #These are BB-menu over Linked Items
            open_in_new_tab = gtk.MenuItem(_("Open Link in New Tab"))
            open_in_new_tab.connect("activate", self._open_in_new_tab, view)
            menu.insert(open_in_new_tab, 0)

            wgetit = gtk.MenuItem("wget it")
            menu.insert(wgetit, 0)
            wgetit.connect('activate', _wget_it, self._hovered_uri)

            markL = gtk.MenuItem("Bookmark Link")
            menu.insert(markL, 0)
            markL.connect('activate', _bookmark_link_cb, self._hovered_uri)
        else:
            #These are BB-menu over non-links
            homeReq = gtk.MenuItem("Go Home")
            menu.insert(homeReq, 0)
            homeReq.connect('activate', self._go_home_cb)

            newTab = gtk.MenuItem("Open New tab")
            menu.insert(newTab, 0)
            newTab.connect('activate', self._open_in_new_tab, DEFAULT_PAGE)

            markC = gtk.MenuItem("Bookmark Current")
            menu.insert(markC, 0)
            markC.connect('activate', _bookmark_current_cb, view)

            wgetit = gtk.MenuItem("wget it")
            wgetit.connect('activate', _wget_it, self._hovered_uri)
            menu.insert(wgetit, 0)
            menu.show_all()

        if view.can_copy_clipboard():
            # translate dialog
            translate = gtk.MenuItem("Translate")
            menu.insert(translate, 0)
            translate.connect('activate', _trans_request_cb, view)

    def _go_home_cb(self, text):
        self.emit("go-home-requested")

    def _open_in_new_tab (self, menuitem, view):
        self.new_tab(self._hovered_uri)

    def _close_tab (self, label, child):
        page_num = self.page_num(child)
        if page_num != -1:
            view = child.get_child()
            view.destroy()
            self.remove_page(page_num)
        self.set_show_tabs(self.get_n_pages() > 1)

    def _switch_page (self, notebook, page, page_num):
        child = self.get_nth_page(page_num)
        view = child.get_child()
        frame = view.get_main_frame()
        self.emit("focus-view-title-changed", frame, frame.props.title)

    def _notify_progress_cb(self, view, data):
        self.emit("progress-changed", view, data)

    def _hovering_over_link_cb (self, view, title, uri):
        self._hovered_uri = uri
        self.emit("hover-changed", view, uri)

    def _title_changed_cb (self, view, frame, title):
        child = self.get_nth_page(self.get_current_page())
        label = self.get_tab_label(child)
        label.set_label(title)
        self.emit("focus-view-title-changed", frame, title)

    def _view_load_finished_cb(self, view, frame):
        child = self.get_nth_page(self.get_current_page())
        label = self.get_tab_label(child)
        title = frame.get_title()
        if not title:
            title = frame.get_uri()
        if title:
            label.set_label(title)

    def _new_web_view_request_cb (self, web_view, web_frame):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        view = WebKitView()

        scrolled_window.add(view)
        scrolled_window.show_all()

        vbox = gtk.VBox(spacing=1)
        vbox.pack_start(scrolled_window, True, True)

        window = gtk.Window()
        window.add(vbox)
        view.connect("web-view-ready", self._new_web_view_ready_cb)
        return view

    def _new_web_view_ready_cb (self, web_view):
        self.emit("new-window-requested", web_view)


class WebBrowser(gtk.Window):
    __gsignals__ = {
        "refresh-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "go-back-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "go-forward-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "zoom-in-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "zoom-out-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "go-home-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "google-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        "new-tab-requested": (gobject.SIGNAL_RUN_FIRST,
                                  gobject.TYPE_NONE, ()),
        "go-home-requested": (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE, ()),
        }

    def __init__(self):
        gtk.Window.__init__(self)
        toolbar = BBToolbar()
        tab_content = TabView()

        self.connect("key-press-event", self._catch_keypress)
        self.connect("go-back-requested", go_back_requested_cb, tab_content)
        self.connect("go-forward-requested", go_forward_requested_cb, tab_content)
        self.connect("new-tab-requested", new_tab_requested_cb, tab_content)
        self.connect("go-home-requested", load_requested_cb, HOME_PAGE, tab_content)
        self.connect("zoom-in-requested", zoom_in_requested_cb, tab_content)
        self.connect("zoom-out-requested", zoom_out_requested_cb, tab_content)
        tab_content.connect("new-window-requested", self._new_window_requested_cb)
        tab_content.connect("progress-changed", self._update_progress_cb)
        tab_content.connect("hover-changed", self._update_hover_cb)
        tab_content.connect("focus-view-title-changed", self._title_changed_cb, toolbar)
        tab_content.connect("go-home-requested", load_requested_cb, HOME_PAGE, tab_content)
        toolbar.connect("refresh-requested", load_requested_cb, tab_content)
        toolbar.connect("go-back-requested", go_back_requested_cb, tab_content)
        toolbar.connect("go-forward-requested", go_forward_requested_cb, tab_content)
        toolbar.connect("zoom-in-requested", zoom_in_requested_cb, tab_content)
        toolbar.connect("zoom-out-requested", zoom_out_requested_cb, tab_content)
        toolbar.connect("google-requested", load_requested_cb, SEARCH_PAGE, tab_content)
        toolbar.connect("load-requested", load_requested_cb, tab_content)
        toolbar.connect("new-tab-requested", new_tab_requested_cb, tab_content)

        self.pbar = gtk.ProgressBar()
        self.pbar.set_size_request(0, 18)
        
        label = gtk.Label()

        vbox = gtk.VBox(spacing=1)
        vbox.pack_start(toolbar, expand=False, fill=False)
        vbox.pack_start(tab_content)
        vbox.pack_start(self.pbar, expand=False, fill=False)

        self.add(vbox)
        self.set_default_size(800, 600)
        self.connect('destroy', destroy_cb, tab_content)

        self.show_all()

        tab_content.new_tab(is_url_file(DEFAULT_PAGE))

    def _catch_keypress(self, event, label):
        tab_content = TabView()
        keyval = label.keyval
        name = gtk.gdk.keyval_name(keyval)
        mod = gtk.accelerator_get_label(keyval, label.state)
        if str(Config.get("default","go_back")) == str(mod):
            self._go_back_key()
        if str(Config.get("default", "go_fwd")) == str(mod):
            self._go_fwd_key()
        if str(Config.get("default", "go_new_tab")) == str(mod):
            self._go_new_tab_key()
        if str(Config.get("default", "go_home")) == str(mod):
            self._go_home_key()
        if str(Config.get("default", "zoom_in")) == str(mod):
            self._zoom_in_key()
        if str(Config.get("default", "zoom_out")) == str(mod):
            self._zoom_out_key()
        if str(Config.get("default", "exit_k")) == str(mod):
            self._exit_k()

    def _go_back_key(self):
        self.emit("go-back-requested")

    def _go_fwd_key(self):
        self.emit("go-forward-requested")

    def _go_new_tab_key(self):
        self.emit("new-tab-requested")

    def _go_home_key(self):
        self.emit("go-home-requested")

    def _zoom_in_key(self):
        self.emit("zoom-in-requested")

    def _zoom_out_key(self):
        self.emit("zoom-out-requested")

    def _exit_k(self):
        sys.exit()

    def _old_window_requested_cb (self, tab_content, view):
        window = view.get_toplevel()
        features = view.get_window_features()

        scrolled_window = view.get_parent()
        if features.get_property("scrollbar-visible"):
            scrolled_window.props.hscrollbar_policy = gtk.POLICY_NEVER
            scrolled_window.props.vscrollbar_policy = gtk.POLICY_NEVER

        isLocationbarVisible = features.get_property("locationbar-visible")
        isToolbarVisible = features.get_property("toolbar-visible")
        if isLocationbarVisible or isToolbarVisible:
            toolbar = BBToolbar(isLocationbarVisible, isToolbarVisible)
            scrolled_window.get_parent().pack_start(toolbar, False, False, 0)

        window.set_default_size(features.props.width, features.props.height)
        window.move(features.props.x, features.props.y)

        window.show_all()
        return True

    def _new_window_requested_cb (self, tab_content, view):
        program = '/usr/bin/roaster'
        launcher = '/usr/bin/python'
        url = tab_content._hovered_uri
        command = [launcher, program, url]
        (cpid, cstdin, cstdout, cstderr)=gobject.spawn_async(command)

    def _title_changed_cb (self, tab_content, frame, title, toolbar):
        if not title:
           title = frame.get_uri()
        self.set_title(_("Roaster - %s") % title)
        load_committed_cb(tab_content, frame, toolbar)

    def _update_progress_cb (self, widget, tab_content, data):
         self.pbar.set_text("%s%%" % data)
         self.pbar.set_fraction(float(data) / 100.0)

    def _update_hover_cb (self, widget, tab_content, data):
        if not data:
            data = ''
        self.pbar.set_text("%s" % data)

# event handlers
def go_back_requested_cb (widget, tab_content):
    cview = current_view(tab_content)
    cview.go_back()

def go_forward_requested_cb (widget, tab_content):
    cview = current_view(tab_content)
    cview.go_forward()

def zoom_in_requested_cb (widget, tab_content):
    cview = current_view(tab_content)
    cview.zoom_in()

def zoom_out_requested_cb (widget, tab_content):
    cview = current_view(tab_content)
    cview.zoom_out()
    self.DEFAULT_ZOOM = cview.get_zoom_level()

def new_tab_requested_cb (toolbar, tab_content):
    text = ""
    tab_content.new_tab(None)
    toolbar.location_set_text(text)

def load_requested_cb (widget, text, tab_content):
    if text:
        url = is_url_file(text)
        tab_content.load_uri(url)
    return

def load_committed_cb (tab_content, frame, toolbar):
    uri = frame.get_uri()
    cview = current_view(tab_content)
    if not uri:
        uri = "http://"
    toolbar.location_set_text(uri)

# PCLOS Utility Function #
def current_view(tab_content):
    currentTab = tab_content.get_nth_page(tab_content.get_current_page())
    childView = currentTab.get_child()
    return childView

def is_url_file(text):
    try:
        text.index("://")
        return text
    except:
        text = "://" + text
    try:
        text.index(":///")
        text = "file" + text
    except:
        text = "http" + text
    return text

# PCLOS Context Menu Callbacks #
def _bookmark_current_cb(widget, view):
    print "bookmark current \n"

def _bookmark_link_cb(widget, url):
    print "bookmark link \n"

def _wget_it(widget, url):
    global Config
    target_dir = Config.get("default_dir", "d_dir")
    print ("wget launched on target " + str(url) + "\n")
    if url != None:
        os.system (str('wget -P ') + 
                   (str(target_dir)+" " + url))
        print 
    else:
        print "You cannot wget that."

def info_dialog_cb(self, widget):
    url = "http://www.linuxbbq.org"
    about = gtk.AboutDialog()
    about.set_program_name("Roaster")
    about.set_version("0.0.1")
    about.set_copyright("(c) original code written by Jan Michael Alonzo")
    about.set_comments("modified and fubar by Julius Hader for LinuxBBQ")
    about.set_website(url)
    about.set_logo(None)
    about.run()
    about.destroy()

def _trans_request_cb(self, view):

    view.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
    clipboard = gtk.Clipboard()
    view.copy_clipboard()
    info_text = clipboard.request_text(clipboard_text_received)
    view.get_window().set_cursor(None)

def clipboard_text_received(clipboard, text, data):
    # send google some text and they return it translated.
    url = "http://ajax.googleapis.com/ajax/services/language/translate"

    source = ""
    dest = "en" # edit LANGUAGE to suit
    params = {}
    params['langpair'] = "%s|%s" % (source, dest)
    params['v'] = '1.0'
    params['q'] = text
    data = urllib.urlencode(params)
    response = urllib.urlopen(url, data)
    translation = simplejson.load(response)
    trans_dlg(translation)

def trans_dlg(translation):

    tmp_file = "/tmp/xxx.html"
    preprefx = """<pre style="
    white-space: -moz-pre-wrap;
    white-space: -pre-wrap;
    white-space: -o-pre-wrap;
    white-space: pre-wrap;
    word-wrap: break-word;
    ">"""
    presufx = """</pre>"""
    htmhdr = """
    <!doctype html public "-//w3c//dtd html 4.0 transitional//en">
    <html>
    <head><title></title></head>
    <body>
    """
    htmftr = """
    </body></html>
    """
    with open(tmp_file, "w+") as fd:
        fd.write(preprefx+translation['responseData']['translatedText']+presufx)

    wkview = webkit.WebView()
    settings = wkview.get_settings()
    settings.set_property("enable-developer-extras", True)
    settings.set_property("minimum-font-size", MIN_FONT_SIZE)
    wkview.set_zoom_level(DEFAULT_ZOOM)
    wkview.set_full_content_zoom(True)
    wkview.set_settings(settings)
    wkview.open("file://"+tmp_file)

    scrwin = gtk.ScrolledWindow()
    scrwin.add(wkview)
    scrwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrwin.set_size_request(500, 200)
    scrwin.show_all()

    t8 = gtk.MessageDialog(None,
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
            gtk.BUTTONS_CLOSE, "Translation")
    t8.vbox.pack_start(scrwin)
    t8.run()
    t8.destroy()

def destroy_cb(window, tab_content):
    """destroy window resources"""
    num_pages = tab_content.get_n_pages()
    while num_pages != -1:
        child = tab_content.get_nth_page(num_pages)
        if child:
            view = child.get_child()
        num_pages = num_pages - 1
    window.destroy()
    gtk.main_quit()


def zoom_in_cb(menu_item, web_view):
    """Zoom into the page"""
    web_view.zoom_in()

def zoom_out_cb(menu_item, web_view):
    """Zoom out of the page"""
    web_view.zoom_out()

def exit_roast(menu_item):
    """exit roaster"""
    sys.exit()

def print_cb(menu_item, web_view):
    mainframe = web_view.get_main_frame()
    mainframe.print_full(gtk.PrintOperation(), gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG);

def page_properties_cb(menu_item, web_view):
    mainframe = web_view.get_main_frame()
    datasource = mainframe.get_data_source()
    main_resource = datasource.get_main_resource()
    window = gtk.Window()
    window.set_default_size(800, 600)
    vbox = gtk.VBox()
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label("MIME Type :"), False, False)
    hbox.pack_end(gtk.Label(main_resource.get_mime_type()), False, False)
    vbox.pack_start(hbox, False, False)
    hbox2 = gtk.HBox()
    hbox2.pack_start(gtk.Label("URI : "), False, False)
    hbox2.pack_end(gtk.Label(main_resource.get_uri()), False, False)
    vbox.pack_start(hbox2, False, False)
    hbox3 = gtk.HBox()
    hbox3.pack_start(gtk.Label("Encoding : "), False, False)
    hbox3.pack_end(gtk.Label(main_resource.get_encoding()), False, False)
    vbox.pack_start(hbox3, False, False)
    window.add(vbox)
    window.show_all()
    window.present()

def view_source_mode_requested_cb(widget, is_active, tab_content):
    cview = current_view(tab_content)
    cview.set_view_source_mode(is_active)
    cview.reload()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DEFAULT_PAGE = sys.argv[1]
    webbrowser = WebBrowser()
    gtk.main()
