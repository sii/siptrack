#!/usr/bin/env python

import os
import sys
import shutil

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)), '..'))
OUT_DIR = os.path.join(BASE_DIR, 'dist')
SIPTRACK_BIN = os.path.join(BASE_DIR, 'siptrack')
SIPTRACK_NON_CONSOLE_BIN = os.path.join(BASE_DIR, 'siptrack-no-console')
SETUP_BIN = os.path.join(BASE_DIR, 'setup.py')
GTK_DIR = 'c:\\opt\\gtk'
INNO_SCRIPT = os.path.join('build-tools', 'siptrack.iss')
INNO_EXECUTABLE = '"c:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe"'
PYTHON_BIN='c:\\Python25\\python.exe'

def delete_old_out_dir():
    print 'deleting old output directory'
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)

def run_setup():
    bin = '%s "%s" py2exe' % (PYTHON_BIN, SETUP_BIN)
    print 'running py2exe: %s' % (bin)
    os.system(bin)

def run_inno():
    bin = INNO_EXECUTABLE + ' ' + INNO_SCRIPT
    print 'running inno setup: %s' % (bin)
    os.system(bin)

def copy_gtk():
    print 'copying gtk'
    for filename in os.listdir(GTK_DIR):
        filepath = os.path.join(GTK_DIR, filename)
        out_dir = os.path.join(OUT_DIR, filename)
        if os.path.isdir(filepath):
            shutil.copytree(filepath, out_dir)
        else:
            shutil.copy(filepath, out_dir)

def make_non_console_siptrack():
    shutil.copy(SIPTRACK_BIN, SIPTRACK_NON_CONSOLE_BIN)

def main():
    if not os.path.exists(os.path.join(BASE_DIR, 'siptrack')):
        print 'Can\'t find siptrack executable, are we in the right place?'
        sys.exit(1)
    delete_old_out_dir()
    make_non_console_siptrack()
    run_setup()
#    copy_gtk()
    run_inno()

if __name__ == '__main__':
    main()
