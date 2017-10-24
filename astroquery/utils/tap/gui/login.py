# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

from astropy.extern import six

try:
    from six.moves.tkinter import Tk as TKTk
except ImportError:
    TKTk = None

try:
    from six.moves.tkinter import Toplevel as TKToplevel
except ImportError:
    TKToplevel = None

try:
    from six.moves.tkinter import Button as TKButton
except ImportError:
    TKButton = None

try:
    from six.moves.tkinter import Label as TKLabel
except ImportError:
    TKLabel = None

try:
    from six.moves.tkinter import Entry as TKEntry
except ImportError:
    TKEntry = None


class LoginDialog(object):

    def __init__(self, host):
        self.__interna_init()
        self.__host = host
        self.__initialized = False
        if TKTk is not None:
            self.__create_content()
            self.__initialized = True

    def __interna_init(self):
        self.__rootFrame = None
        self.__top = None
        self.__usrEntry = None
        self.__pwdEntry = None
        self.__accepted = False
        self.__host = None
        self.__usr = None
        self.__pwd = None

    def __cancel_action(self):
        self.__accepted = False
        self.__rootFrame.destroy()

    def __login_action(self):
        self.__accepted = True
        self.__usr = self.__usrEntry.get()
        self.__pwd = self.__pwdEntry.get()
        self.__rootFrame.destroy()

    def __enter_action(self, event):
        self.__login_action()

    def __create_content(self):
        self.__rootFrame = TKTk()
        self.__rootFrame.withdraw()

        self.__top = TKToplevel(self.__rootFrame)
        self.__top.title("Login")
        self.__top.protocol("WM_DELETE_WINDOW", self.__rootFrame.destroy)

        self.__top.bind('<Return>', self.__enter_action)

        self.__top.update_idletasks()
        width = self.__top.winfo_width()
        height = self.__top.winfo_height()
        x = (self.__top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.__top.winfo_screenheight() // 2) - (height // 2)

        self.__top.geometry("+%d+%d" % (x, y))

        row = 0
        expLabel = TKLabel(self.__top, text='Login to host:')
        expLabel.grid(row=row, column=0, columnspan=4, padx=5, pady=2)

        row = row+1
        urlLabel = TKLabel(self.__top, text=self.__host)
        urlLabel.grid(row=row, column=0, columnspan=4, padx=5, pady=2)

        row = row+1
        usrLabel = TKLabel(self.__top, text='User')
        usrLabel.grid(row=row, column=0, columnspan=2, padx=20, pady=5)
        self.__usrEntry = TKEntry(self.__top, width=20)
        self.__usrEntry.grid(row=row, column=2, columnspan=2, padx=5, pady=5)

        row = row+1
        pwdLabel = TKLabel(self.__top, text='Password')
        pwdLabel.grid(row=row, column=0, columnspan=2, padx=20, pady=5)
        self.__pwdEntry = TKEntry(self.__top, width=20, show="*")
        self.__pwdEntry.grid(row=row, column=2, columnspan=2, padx=5, pady=5)

        row = row+1
        cancelButton = TKButton(self.__top, text='Cancel', command=self.__cancel_action)
        cancelButton.grid(row=row, column=1, padx=5, pady=5)
        loginButton = TKButton(self.__top, text='Login', command=self.__login_action)
        loginButton.grid(row=row, column=2, padx=5, pady=5)

    def show_login(self):
        if self.__initialized:
            self.__usrEntry.focus_set()
            self.__rootFrame.mainloop()
        else:
            print("tkinter python module is not available.\n\
            Please, install tkinter module or use command line login utility.")

    def is_accepted(self):
        return self.__accepted

    def get_user(self):
        return self.__usr

    def get_password(self):
        return self.__pwd
