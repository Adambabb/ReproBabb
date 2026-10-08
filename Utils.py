import os
import sys

def resource_path(route):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, route)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), route)
