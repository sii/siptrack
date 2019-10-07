import sys
import pygtk
pygtk.require('2.0')
import gtk

try:
    import dbus
    import dbus.service
    import dbus.glib
    have_dbus = True
except ImportError:
    have_dbus = False

import siptracklib
import siptracklib.config
import siptracklib.connections
import siptracklib.cmdconnect
import siptracklib.errors
from siptracklib import utils

class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.set_name('siptrack gtkconnect')
        self.set_version(siptracklib.__version__)
        self.set_website('http://launchpad.net/siptrack')
        self.connect('response', self.done)

    def done(self, dialog, r):
        dialog.destroy()

class NotifyMenu(gtk.Menu):
    max_devices = 10

    def __init__(self):
        super(NotifyMenu, self).__init__()
        item = gtk.ImageMenuItem(gtk.STOCK_ABOUT, None)
        item.connect('activate', self.showAbout)
        self.append(item)
        self.append(gtk.SeparatorMenuItem())
        item = gtk.ImageMenuItem(gtk.STOCK_QUIT, None)
        item.connect('activate', gtk.main_quit)
        self.append(item)
        self.append(gtk.SeparatorMenuItem())
        self.device_item_head_pos = 4
        self.added_devices = 0
        self.show_all()

    def display(self, icon, event_button, event_time):
        if sys.platform == 'win32':
            self.popup(None, None, None,
                    event_button, event_time, icon)
        else:
            self.popup(None, None, gtk.status_icon_position_menu,
                    event_button, event_time, icon)

    def showAbout(self, item):
        dialog = AboutDialog()
        dialog.run()

    def getDeviceItem(self, device):
        for item in self:
            if hasattr(item, 'device'):
                if item.device == device:
                    return item
        return None

    def removeLastDevice(self):
        match = None
        for item in self:
            if hasattr(item, 'device'):
                match = item
        if match:
            self.remove(match)

    def connectedDevice(self, device):
        item = self.getDeviceItem(device)
        if item:
            self.remove(item)
        else:
            item = gtk.MenuItem(device.attributes.get('name'))
            item.device = device
            item.connect('activate', self.clickedDevice)
            item.show()
            if self.added_devices >= self.max_devices:
                self.removeLastDevice()
            else:
                self.added_devices += 1
        self.insert(item, self.device_item_head_pos)

    def clickedDevice(self, item):
        self.stsearch.connectDevice(item.device)

class STSearchScreen(object):
    def __init__(self, connection_manager, notify_menu):
        self.connection_manager = connection_manager
        self.config = self.connection_manager.config
        self._matched_devices = []
        self._matched_passwords = []
        self._selected_device = None
        self.notify_menu = notify_menu
        self.hidden = False
        self.autoconnect_single_match = self.config.getBool('autoconnect-single-match', False)
        self.iconified = False
        self.hide_pos_x = None
        self.hide_pos_y = None
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("st search")
        self.window.set_border_width(10)
        self.window.set_geometry_hints(min_width = 500)
        self.window.connect('delete_event', self.deleteEvent)
        self.window.connect('window-state-event', self.windowStateEvent)
        self.window.set_position(gtk.WIN_POS_CENTER)

        self.root_box = gtk.VBox(False, 20)
        self.window.add(self.root_box)
        self.root_box.show()

        self.root_hbox = gtk.HBox(False, 20)
        self.root_box.pack_start(self.root_hbox)
        self.root_hbox.show()

        self.left_box = gtk.VBox(False, 0)
        self.root_hbox.pack_start(self.left_box)
        self.left_box.show()

        self.right_box = gtk.VBox(False, 10)
        self.root_hbox.pack_start(self.right_box)
        self.right_box.show()

        self.search_frame = gtk.Frame('Device search')
        self.right_box.pack_start(self.search_frame)
        self.search_frame.show()

        self.search_entry = gtk.Entry()
        self.search_entry.set_max_length(50)
        self.search_entry.connect('activate', self._cbSearch,
                self.search_entry)
        self.search_frame.add(self.search_entry)
        self.search_entry.grab_focus()
        self.search_entry.show()

        self.statusbar = gtk.Statusbar()
        self.status_context = self.statusbar.get_context_id('')
        self.setStatus('enter device name')
        self.root_box.pack_start(self.statusbar)
        self.statusbar.show()

        sep = gtk.HSeparator()
        self.right_box.pack_start(sep)
        sep.show()

        self.device_select_box = gtk.combo_box_new_text()
        self.device_select_box.connect('changed', self._cbDeviceSelected)
        self.right_box.pack_start(self.device_select_box)
        self.device_select_box.show()

        sep = gtk.HSeparator()
        self.right_box.pack_start(sep)
        sep.show()

        self.password_select_box = gtk.combo_box_new_text()
        self.password_select_box.connect('changed', self._cbPasswordSelected)
        self.right_box.pack_start(self.password_select_box)
        self.password_select_box.show()

        sep = gtk.HSeparator()
        self.right_box.pack_start(sep)
        sep.show()

        self.device_info_frame = gtk.Frame('Device information')
        self.right_box.pack_start(self.device_info_frame)
        self.device_info_frame.show()

        self.device_info_window = gtk.ScrolledWindow(hadjustment=None,
                vadjustment=None)
        self.device_info_window.set_policy(gtk.POLICY_AUTOMATIC,
                gtk.POLICY_AUTOMATIC)
        self.device_info_frame.add(self.device_info_window)
        self.device_info_window.show()

        self.device_info = gtk.TextView()
        self.device_info.set_editable(False)
        self.device_info.set_cursor_visible(False)
        self.device_info.set_wrap_mode(gtk.WRAP_NONE)
        self.device_info_window.add(self.device_info)
        self.device_info.show()

        sep = gtk.HSeparator()
        self.right_box.pack_start(sep)
        sep.show()

        self.connect_button = gtk.Button('connect to device')
        self.connect_button.connect("clicked", self._cbConnectDevice)
        self.right_box.pack_start(self.connect_button)
        self.connect_button.show()

        self.old_connects_frame = gtk.Frame('Previous Connections')
        self.left_box.pack_start(self.old_connects_frame)
        self.old_connects_frame.show()
        self.old_connects_liststore = gtk.ListStore(str)
        self.old_connects_list = []
        self.old_connects_view = gtk.TreeView(self.old_connects_liststore)
        self.old_connects_column = gtk.TreeViewColumn('Device name',
                gtk.CellRendererText(), text = 0)
        self.old_connects_column.set_min_width(150)
        self.old_connects_view.append_column(self.old_connects_column)
        self.old_connects_frame.add(self.old_connects_view)
        self.old_connects_view.connect('row-activated',
                self._cbOldConnectsSelected)

        self._initSiptrack()

        self.window.show_all()

    def windowStateEvent(self, widget, event, *args, **kwargs):
        if event.type == gtk.gdk.WINDOW_STATE:
            if event.changed_mask | gtk.gdk.WINDOW_STATE_ICONIFIED == \
                    gtk.gdk.WINDOW_STATE_ICONIFIED:
                if event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED == \
                        gtk.gdk.WINDOW_STATE_ICONIFIED:
                    self.iconified = True
                else:
                    self.iconified = False
        return False

    def _cbOldConnectsSelected(self, treeview, path, view_column):
        self._matched_devices = [self.old_connects_list[path[0]]]
        self._updateDeviceSelection()
        self.device_select_box.set_active(0)

    def _initSiptrack(self):
        connect_username = self.config.get('default-username', '')
        self.connect_usernames = connect_username.split()
        connected = False
        while not connected:
            try:
                self.st = self.connection_manager.connect()
            except siptracklib.errors.SiptrackError as e:
                self._requestPassword()
            else:
                connected = True
        self.config.set('password', None)
        self.connect = siptracklib.cmdconnect.get_connection_class(
                self.config)
        self.connect.open_new_terminal = True

    def _requestPassword(self):
        self.up_dialog = gtk.Dialog(title = 'Enter username/password',
                parent = self.window,
                buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.up_dialog.set_default_response(gtk.RESPONSE_ACCEPT)
        
        center_box = gtk.HBox(False, 0)
        self.up_dialog.vbox.pack_start(center_box)
        center_box.show()

        left_box = gtk.VBox(False, 0)
        center_box.pack_start(left_box)
        left_box.show()

        right_box = gtk.VBox(False, 10)
        center_box.pack_start(right_box)
        right_box.show()

        hbox = gtk.HBox(False, 0)
        left_box.pack_start(hbox)
        hbox.show()
        label = gtk.Label('Hostname: ')
        hbox.pack_start(label)
        label.show()

        self.up_hostname_entry = gtk.Entry(max = 20)
        self.up_hostname_entry.set_text(self.config.get('server') or '')
        self.up_hostname_entry.set_activates_default(True)
        right_box.pack_start(self.up_hostname_entry)
        self.up_hostname_entry.show()

        hbox = gtk.HBox(False, 0)
        left_box.pack_start(hbox)
        hbox.show()
        label = gtk.Label('Username: ')
        hbox.pack_start(label)
        label.show()

        self.up_username_entry = gtk.Entry(max = 20)
        self.up_username_entry.set_text(self.config.get('username') or '')
        self.up_username_entry.set_activates_default(True)
        right_box.pack_start(self.up_username_entry)
        self.up_username_entry.show()

        hbox = gtk.HBox(False, 0)
        left_box.pack_start(hbox)
        hbox.show()
        label = gtk.Label('Password: ')
        hbox.pack_start(label)
        label.show()

        self.up_password_entry = gtk.Entry(max = 20)
        self.up_password_entry.set_text('')
        self.up_password_entry.set_activates_default(True)
        self.up_password_entry.set_visibility(False)
        right_box.pack_start(self.up_password_entry)
        self.up_password_entry.show()

        self.up_dialog.show()
        response = self.up_dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            self.config.set('server', self.up_hostname_entry.get_text())
            self.config.set('username', self.up_username_entry.get_text())
            self.config.set('password', self.up_password_entry.get_text())
        else:
            raise siptracklib.errors.SiptrackError('no username/password supplied')
        self.up_dialog.destroy()

    def _cbUPOK(self, widget):
        pass

    def _cbUPCancel(self, widget):
        gtk.main_quit()

    def deleteEvent(self, widget, event, data = None):
#        self.st.logout()
#        gtk.main_quit()
        self.forceHide()
        return True

    def _cbSearch(self, widget, entry):
        self.setStatus('searching...')
        gtk.main_iteration()
        search_text = entry.get_text()
        if len(search_text) == 0:
            self.setStatus('invalid search...')
            return
        entry.select_region(0, len(search_text))
        try:
            self._matched_devices = \
                    utils.search_device(self.st, search_text)
        except siptracklib.errors.SiptrackError:
            self._initSiptrack()
        self._matched_devices.sort()
        self._updateDeviceSelection()
        if len(self._matched_devices) == 0:
            self.setStatus('no devices matched')
            self._matched_passwords = []
            self._updatePasswordSelection()
        else:
            self.device_select_box.set_active(0)
            self.setStatus('select device/search again')
            if len(self._matched_devices) == 1 and \
                    self.autoconnect_single_match:
                self.connectDevice(self._matched_devices[0])

    def _cbDeviceSelected(self, combobox):
        self._selected_device = self._getSelectedDevice()
        self.writeDeviceInfo(self._selected_device)
        if self._selected_device:
            self._matched_passwords = [password for password in \
                    self._selected_device.listChildren(include = ['password'])]
        else:
            self._matched_passwords = []
        self._updatePasswordSelection()

    def _cbPasswordSelected(self, combobox):
        self._selected_password = self._getSelectedPassword()

    def _clearDeviceSelection(self):
        model = self.device_select_box.get_model()
        for val in model:
            self.device_select_box.remove_text(0)

    def _clearPasswordSelection(self):
        model = self.password_select_box.get_model()
        for val in model:
            self.password_select_box.remove_text(0)

    def _updateDeviceSelection(self):
        self._clearDeviceSelection()
        for device in self._matched_devices:
            self.device_select_box.append_text(device.attributes.get('name', 'unknown'))

    def _updatePasswordSelection(self):
        self._selected_password = None
        self._clearPasswordSelection()
        for password in self._matched_passwords:
            self.password_select_box.append_text(password.attributes.get('username', 'unknown'))
        pos = self._selectDefaultPassword(self._matched_passwords,
                self.connect_usernames)
        if len(self._matched_passwords) > 0:
            self.password_select_box.set_active(pos)

    def _selectDefaultPassword(self, passwords, usernames):
        device_usernames = [p.attributes.get('username') for p in passwords]
        for username in usernames:
            pos = 0
            for password in passwords:
                if password.attributes.get('username') == username:
                    return pos
                pos += 1
        return 0

    def _getSelectedDevice(self):
        model = self.device_select_box.get_model()
        active = self.device_select_box.get_active()
        if active < 0:
            return None
        return self._matched_devices[active]

    def _getSelectedPassword(self):
        model = self.password_select_box.get_model()
        active = self.password_select_box.get_active()
        if active < 0:
            return None
        return self._matched_passwords[active]

    def setStatus(self, status):
        self.statusbar.pop(self.status_context)
        self.statusbar.push(self.status_context, 'Status: %s' % (status))

    def writeDeviceInfo(self, device):
        buffer = self.device_info.get_buffer()
        if device is None:
            buffer.set_text('')
        else:
            lines = []
            lines.append('Name: %s' % (device.attributes.get('name')))
            lines.append('Description: %s' % (device.attributes.get('description')))
            lines.append('OS: %s' % (device.attributes.get('os', 'unknown')))
            buffer.set_text('\n'.join(lines))

    def _cbConnectDevice(self, widget):
        if self._selected_device is None:
            self.setStatus('no device selected')
        else:
            self.connectDevice(self._selected_device)

    def connectDevice(self, device):
        if self._selected_password is None:
            self.setStatus('must select a user first')
            return
        username = self._selected_password.attributes.get('username', '')
        try:
            self.connect.connect(device, username)
        except siptracklib.errors.SiptrackError as e:
            self.setStatus(str(e))
        else:
            self._addOldConnectsDevice(device)

    def _addOldConnectsDevice(self, device):
        if device in self.old_connects_list:
            index = self.old_connects_list.index(device)
            self.old_connects_list.remove(device)
            iter = self.old_connects_liststore.get_iter(index)
            self.old_connects_liststore.remove(iter)
        self.old_connects_list.insert(0, device)
        self.old_connects_liststore.prepend(
                [device.attributes.get('name', 'unknown')])
        self.notify_menu.connectedDevice(device)

    def displayOrHide(self, *args, **kwargs):
        if self.hidden or self.iconified:
            self.forceDisplay()
        else:
            self.forceHide()

    def forceDisplay(self):
        self.forceHide()
        if self.hide_pos_x:
            self.window.move(self.hide_pos_x, self.hide_pos_y)
        if self.iconified:
            self.window.deiconify()
        self.window.present()
        self.search_entry.grab_focus()
#        self.window.set_keep_above(True)
        self.window.window.focus()
        self.window.show_all()
        self.hidden = False

    def forceHide(self):
        if not self.hidden:
            self.hide_pos_x, self.hide_pos_y = self.window.get_position()
        self.window.hide_all()
        self.hidden = True

if have_dbus:
    class DBUSListener(dbus.service.Object):
        def __init__(self):
            self.stsearch = None
            name = dbus.service.BusName('org.siptrack.gtkconnect',
                    bus=dbus.SessionBus())
            dbus.service.Object.__init__(self, name,
                    '/org/siptrack/gtkconnect')

        @dbus.service.method('org.siptrack.gtkconnect')
        def display(self):
            self.stsearch.displayOrHide()

    def display_via_dbus():
        bus = dbus.SessionBus()
        try:
            st_service = bus.get_object('org.siptrack.gtkconnect',
                    '/org/siptrack/gtkconnect')
            st_service.get_dbus_method('display', 'org.siptrack.gtkconnect')()
        except dbus.exceptions.DBusException:
            return False
        return True

def cmd_gtkconnect(connection_manager, daemonize):
    dbus_listener = None
    if daemonize:
        if have_dbus:
            if display_via_dbus():
                return
            dbus_listener = DBUSListener()
        utils.daemonize()
    connection_manager.config.sections = ['GTKCONNECT', 'STCONNECT', 'DEFAULT']
    connection_manager.interactive = False
    menu = NotifyMenu()
    autoconnect_single_match = False
    stsearch = STSearchScreen(connection_manager, menu)
    menu.stsearch = stsearch
    icon = gtk.status_icon_new_from_file(utils.get_icon_path('64x64.png'))
    icon.connect('popup-menu', menu.display)
    icon.connect('activate', stsearch.displayOrHide)
    if dbus_listener:
        dbus_listener.stsearch = stsearch
    gtk.main()

if __name__ == '__main__':
    main()
