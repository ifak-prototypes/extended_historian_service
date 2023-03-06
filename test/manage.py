# -*- coding: utf-8 -*-
import cmd2
import os
import subprocess
import time
import yaml


METHODS = yaml.safe_load('''
    start: |
        def do_start_{canonical_component_name}(self, args):
            self.run('{component_name}', '{script_call}', cwd='{cwd}')
    stop: |
        def do_stop_{canonical_component_name}(self, args):
            self.run('{component_name}', '{script_call}', cwd='{cwd}')
    stop_generic: |
        def do_stop_{canonical_component_name}(self, args):
            self.processes['{component_name}'].kill()
    ''')


class AppManager(cmd2.Cmd):
    
    def __init__(self, prompt: str, config: str, font: str ="DejaVu Sans Mono") -> None:
        cmd2.Cmd.__init__(self)
        self.prompt: str = prompt
        self.font: str = font
        self.config: str = config

        self.win = 0
        self.cmd = "konsole -p tabtitle='TITLE' -p Font='FONT,9,-1,5,50,0,0,0,0,0' -geometry {w}x{h}+{x}+{y} -e 'ACTION'"
        self.cmd = self.cmd.replace('FONT', self.font)
        print(self.cmd)
        self.processes = {}

    def run(self, title, action, cwd='.'):
        screen_w = 1920
        screen_h = 1080
        rows = 5
        columns = 3

        n = self.win
        self.win += 1

        w = int(screen_w/columns)
        h = int(screen_h/rows)
        x = (int(n/rows) % columns) * w
        y = (n % rows) * (h + 30)

        cmd = self.cmd.format(w=w, h=h, x=x, y=y)
        cmd = cmd.replace('TITLE', title)
        cmd = cmd.replace('ACTION', action)

        path = os.path.join(os.getcwd(), cwd)

        proc = subprocess.Popen(cmd, shell=True, cwd=path)
        self.processes[title] = proc
        time.sleep(5)

    def do_print_architecture(self, args):
        print("System Architecture:")
        print_d(self.config, "  ")
        print()

def print_d(d, indent):
    for k in d:
        if k[0].isupper():
            print(indent + "- " + k)
            print_d(d[k], indent+"  ")


def extend_manager(d, cn):
    for k in d:
        ccn = cn.replace(" ", "_")

        if k[0].islower():

            # current working directory
            cwd = '.'
            if 'cwd' in d:
                cwd = d['cwd']

            # create start functions
            if k == 'start':
                fstr = METHODS['start'].format(component_name=cn, canonical_component_name=ccn, script_call=d['start'], cwd=cwd)
                exec(fstr)
                exec(f"setattr(AppManager, 'do_start_{ccn}', do_start_{ccn})")
            else:
                pass

            # create stop functions
            if k == 'stop':
                fstr = METHODS['stop'].format(component_name=cn, canonical_component_name=ccn, script_call=d['stop'], cwd=cwd)
                exec(fstr)
                exec(f"setattr(AppManager, 'do_stop_{ccn}', do_stop_{ccn})")
            else:
                # generate generic stop function
                if cn not in ["System", "Infrastructure", "Devices", "Adapters"]:
                    fstr = METHODS['stop_generic'].format(component_name=cn, canonical_component_name=ccn)
                    exec(fstr)
                    exec(f"setattr(AppManager, 'do_stop_{ccn}', do_stop_{ccn})")

        else:
            # recursion
            extend_manager(d[k], k)

