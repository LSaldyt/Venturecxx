import subprocess

subprocess.call("sudo docker run -ti -p 8888:8888 -p 5900:5900 -v $(pwd):/root/Venturecxx venture", shell=True)
