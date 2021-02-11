#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from pathlib import Path
import locale
import gettext
_ = gettext.gettext
N_ = gettext.ngettext

from controller import Controller
from view import View
from model import Model



if __name__ == '__main__':
    #workarround
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    #Default locale
    locale.setlocale(locale.LC_ALL, '')
    LOCALE_DIR = Path(__file__).parent / "locale"
    locale.bindtextdomain('IPM-p1', LOCALE_DIR)
    gettext.bindtextdomain('IPM-p1', LOCALE_DIR)
    gettext.textdomain('IPM-p1')
    
    model = Model("mongodb://localhost:27017")
    controller = Controller()
    controller.set_model(model)
    controller.set_view(View())
    controller.main(True)
    print("APP EXIT ")
