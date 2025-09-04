#!.\.venv\Scripts\python.exe
# -*- coding: utf-8 -*-
import src
# assert reqmanb.main
# assert reqmanb.reqman.__version__=="3.3.0", f"bad reqman version {reqmanb.reqman.__version__}"

import os,sys,shutil
from PyInstaller import __main__ as py

##################################################################
if not "win" in sys.platform.lower():
    print("Only on windows ;-)")
    sys.exit(-1)
##################################################################
if sys.prefix==sys.base_prefix:
    print("Tu n'es pas dans le venv (virual env, faut ./venv/scripts/activate !!!!)!")
    sys.exit(-1)
    
# def convVerPatch(v): # conv versionning to windows x.x.x.x
#     a,b,c=v.split(".")
#     clean=lambda x: x and x.isnumeric() and x or "0"
#     return ".".join([clean(a), clean(b), clean(c), "0"])

# assert convVerPatch("1.2.3") == "1.2.3.0"
# assert convVerPatch("1.2.3a") == "1.2.0.0"

def rm(f):
    print("  Supprime:", f)
    if os.path.isdir(f):
        shutil.rmtree(f)
    elif os.path.isfile(f):
        os.unlink(f)

def log(*a):
    print("="*80)
    print( " ".join([str(i) for i in a]))
    print("="*80)

try:
    # os.system(f"py.exe ui/templates/__init__.py") 

    log("Nettoyage")
    os.chdir(os.path.split(sys.argv[0])[0])
    rm("build")
    rm("dist/rq.exe")

    # log("Build WHL",reqmanb.__version__)
    # os.system(f"py.exe setup.py bdist_wheel") # reutilise le "setup.py" (pourrait etre inclus ici)
    # rm("reqmanb.egg-info")
    # rm("build")

    log("Build EXE")
    excludes = []
    # les packages python auto devine qui sont sur mon poste, et que je veux exclure de l'exe (car c des faux positifs)
    for i in "tkinter numpy scipy tk PIL matplotlib webview pytest jinja2 jedi IPython sqlite3 pygments zmq".split():
        excludes.append("--exclude-module")
        excludes.append(i)

    py.run([
        'src/main.py',
        "-n","rq",
        '--onefile',
        # "--upx-dir",r"C:\tmp\upx-4.1.0-win64",
        # '--icon=ressources/reqman.ico',
        "--log-level","DEBUG"
    ] + excludes)

    import time;time.sleep(2)

    # v=convVerPatch(reqmanb.__version__)
    # log("Set windows/reqmanb.exe Version:",reqmanb.__version__,"-->",v)
    # os.system(f"""ressources\\verpatch.exe dist\\rq.exe {v} /high /va /pv {v} /s description "Rq" /s product "Rq" /s copyright "MIT, 2025" /s company "no" """)

    # log("Copy l'exe sur C -> reqman.exe")
    # shutil.copy2("./dist/reqmanb.exe","C:/.../reqman.exe")
finally:
    rm("rq.spec")
