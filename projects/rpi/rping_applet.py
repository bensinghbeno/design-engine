#!/usr/bin/python

# This code is an example for a tutorial on Ubuntu Unity/Gnome AppIndicators:
# http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html

import os
import signal
import json

from urllib2 import Request, urlopen, URLError

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GObject as gobject

def check_ping():
    hostname = "192.168.2.7"
    response = os.system("ping -c 1 " + hostname)
    # and then check the response...
    if response == 0:
        pingstatus = "connected"
    else:
        pingstatus = "disconnected"

    return pingstatus

def init_vars():
    global prev_pingstatus
    prev_pingstatus = "disconnected"
    return prev_pingstatus

def rpi_ping_timer():
    global prev_pingstatus
    if check_ping() == "connected":
        if prev_pingstatus == "disconnected":
            print("connected")
            notify_rpi_connected()
            prev_pingstatus = "connected"
            os.system("mplayer -really-quiet ~/engine/data/msg_tone.mp3 >> /dev/null &");
    else:
        print("disconnected")
        if prev_pingstatus != "disconnected":
            notify_rpi_disconnected()
            prev_pingstatus = "disconnected"
    return True# do ur work here, but not for long



APPINDICATOR_ID = 'myappindicator'


def main():
    global indicator
    indicator = appindicator.Indicator.new(APPINDICATOR_ID, os.path.abspath('/home/ben/Pictures/raspberry_pi_disconnected.png'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(build_menu())
    notify.init(APPINDICATOR_ID)
    gobject.timeout_add(4000, rpi_ping_timer)
    gtk.main()
    


def build_menu():
    menu = gtk.Menu()
    item_joke = gtk.MenuItem('Joke')
    item_joke.connect('activate', joke)
    menu.append(item_joke)
    item_quit = gtk.MenuItem('Quit')
    item_quit.connect('activate', quit)
    menu.append(item_quit)
    menu.show_all()
    return menu

def fetch_joke():
    request = Request('http://api.icndb.com/jokes/random?limitTo=[nerdy]')
    response = urlopen(request)
    joke = json.loads(response.read())['value']['joke']
    return joke

def joke(_):
    notify.Notification.new("<b>Joke</b>", fetch_joke(), None).show()

def notify_rpi_connected():
    indicator.set_icon("/home/ben/Pictures/raspberry_pi_connected.png")
    notify.Notification.new("<b>Rpinger</b>","Raspberry Pi is Online.", None).show()

def notify_rpi_disconnected():
    indicator.set_icon("/home/ben/Pictures/raspberry_pi_disconnected.png")
    notify.Notification.new("<b>Rpinger</b>","Raspberry Pi is Offline.", None).show()

def quit(_):
    notify.uninit()
    gtk.main_quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    init_vars()
    main()
