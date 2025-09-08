# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import os,sys,shutil,re,subprocess,time

########################################################################
def DO_WINDOWS( version:str ):
########################################################################
    exename = "rq"
    if sys.prefix==sys.base_prefix:
        print("Not in .venv ! (try 'uv run build.py')")
        sys.exit(-1)

    from PyInstaller import __main__ as py

    def convVerPatch(v): # conv versionning to windows x.x.x.x
        a,b,c=v.split(".")
        clean=lambda x: x and x.isnumeric() and x or "0"
        return ".".join([clean(a), clean(b), clean(c), "0"])

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

        log("Clean")
        os.chdir(os.path.split(sys.argv[0])[0])
        rm("build")
        rm(f"dist/{exename}.exe")

        # log("Build WHL",reqmanb.__version__)
        # os.system(f"py.exe setup.py bdist_wheel") # reutilise le "setup.py" (pourrait etre inclus ici)
        # rm("reqmanb.egg-info")
        # rm("build")

        log("Build EXE",version)
        excludes = []
        # les packages python auto devine qui sont sur mon poste, et que je veux exclure de l'exe (car c des faux positifs)
        for i in "tkinter numpy scipy tk PIL matplotlib webview pytest jinja2 jedi IPython sqlite3 pygments zmq".split():
            excludes.append("--exclude-module")
            excludes.append(i)

        py.run([
            'src/main.py',
            "-n",exename,
            '--onefile',
            # "--upx-dir",r"C:\tmp\upx-4.1.0-win64",
            # '--icon=ressources/reqman.ico',
            "--log-level","DEBUG"
        ] + excludes)

        time.sleep(2)

        # v=convVerPatch(reqmanb.__version__)
        # log("Set windows/reqmanb.exe Version:",reqmanb.__version__,"-->",v)
        # os.system(f"""ressources\\verpatch.exe dist\\rq.exe {v} /high /va /pv {v} /s description "Rq" /s product "Rq" /s copyright "MIT, 2025" /s company "no" """)

    finally:
        rm(f"{exename}.spec")


########################################################################
def DO_REAL_OS():
########################################################################
    os.system("uv build")


def get_version():
    return subprocess.run(["uv", "version", "--short"],capture_output=True,text=True).stdout.strip()


def replace_rq_version(version):
    fn="src/reqman4/common.py"
    with open(fn, "r+") as f:
        buf = re.sub(r'r\".+\" #', f'r"{version}" #', f.read(), 1)
        f.seek(0)
        f.write(buf)
        f.truncate()
    print(fn,"<-",version)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    version = get_version()

    replace_rq_version(version)
    # import time; time.sleep(0.5)
    # from src import reqman4
    # assert reqman4.__version__ == version

    ##################################################################
    if "win" in sys.platform.lower():
        DO_WINDOWS( version )
        sys.exit(-1)
    else:
        DO_REAL_OS()
    ##################################################################

