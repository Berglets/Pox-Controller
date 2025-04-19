from optparse import OptionParser
import subprocess
import os

# get mappings from interface ip to eth id
def getEthMappings():
    cmd1 = "docker exec part1-r1-1 ip -o -4 addr show | grep 10.0.21.4 | awk '{{print $2}}'"  # r1 north
    cmd2 = "docker exec part1-r1-1 ip -o -4 addr show | grep 10.0.41.4 | awk '{{print $2}}'"  # r1 south 
    cmd3 = "docker exec part1-r3-1 ip -o -4 addr show | grep 10.0.23.4 | awk '{{print $2}}'"  # r3 north
    cmd4 = "docker exec part1-r3-1 ip -o -4 addr show | grep 10.0.43.4 | awk '{{print $2}}'"  # r3 south
    
    # string is eth0, eth1, or eth2
    e1 = subprocess.check_output(cmd1, shell=True).decode().strip() 
    e2 = subprocess.check_output(cmd2, shell=True).decode().strip() 
    e3 = subprocess.check_output(cmd3, shell=True).decode().strip() 
    e4 = subprocess.check_output(cmd4, shell=True).decode().strip() 
    
    return e1, e2, e3, e4

# Start of program execution
parser = OptionParser()
parser.add_option('-d', '--docker', action='store_true', dest='docker', help='0. clone class files and start up docker') 
parser.add_option('-t', '--topology', action='store_true', dest='topology', help='1. create network topology using Docker containers') 
parser.add_option('-o', '--ospf', action='store_true', dest='ospf', help='2. start OSPF daemons on each router') 
parser.add_option('-e', '--ends', action='store_true', dest='ends', help='3. installs end host routes')
parser.add_option('-p', '--path', type="choice", choices=["north", "south"], dest='path', help='4. path traffic should take. Either "north" or "south"') 
parser.add_option('-a', '--all', action='store_true', dest='all', help='completes options 0-3 in order') 
(options, args) = parser.parse_args()

sdir = os.path.dirname(os.path.abspath(__file__)) # script directory
wdir = os.path.join(sdir, "cs4480-2025-s/pa3/part1/") # working directory

if options.docker or options.all: 
    subprocess.run("git clone https://gitlab.flux.utah.edu/teach-studentview/cs4480-2025-s.git", shell=True, check=True, cwd=sdir)
    subprocess.run("./dockersetup", shell=True, check=True, cwd=wdir)
if options.topology or options.all:
    new_yaml = os.path.join(sdir, "docker-compose-new.yaml")
    old_yaml = os.path.join(wdir, "docker-compose.yaml")
    subprocess.run(f"mv {new_yaml} {old_yaml}", shell=True, check=True, cwd=sdir)
    subprocess.run("sudo docker compose up -d", shell=True, check=True, cwd=wdir)
if options.ends or options.all:
    subprocess.run("sudo docker exec -it part1-ha-1 route add -net 10.0.15.0/24 gw 10.0.14.4", shell=True, check=True, cwd=wdir)
    subprocess.run("sudo docker exec -it part1-hb-1 route add -net 10.0.14.0/24 gw 10.0.15.4", shell=True, check=True, cwd=wdir)
if options.ospf or options.all:
    containers = ["part1-r1-1", "part1-r2-1", "part1-r3-1", "part1-r4-1"]
    for container in containers:
        r_cmd = f"sudo docker exec -it {container} "
        # install ospf
        subprocess.run(r_cmd + "apt -y install curl", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "apt -y install gnupg", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "curl -s https://deb.frrouting.org/frr/keys.gpg | sudo tee /usr/share/keyrings/frrouting.gpg > /dev/null", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "apt install lsb-release", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "bash -c 'export FRRVER=\"frr-stable\"'", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "echo deb '[signed-by=/usr/share/keyrings/frrouting.gpg]' https://deb.frrouting.org/frr $(lsb_release -s -c) $FRRVER | sudo tee -a /etc/apt/sources.list.d/frr.list", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "apt update", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "apt -y install frr frr-pythontools", shell=True, check=True, cwd=wdir)
        # edit daemon
        subprocess.run(r_cmd + "sed -i 's/^ospfd=no$/ospfd=yes/' /etc/frr/daemons", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "service frr restart", shell=True, check=True, cwd=wdir)
        # configure routers in vtysh
        if container == "part1-r1-1":
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 1.1.1.1' -c 'network 10.0.14.0/24 area 0.0.0.0' -c 'network 10.0.21.0/24 area 0.0.0.0' -c 'network 10.0.41.0/24 area 0.0.0.0'  -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
        elif container == 'part1-r2-1':
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 2.2.2.2' -c 'network 10.0.21.0/24 area 0.0.0.0' -c 'network 10.0.23.0/24 area 0.0.0.0' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
        elif container == 'part1-r3-1':
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 3.3.3.3' -c 'network 10.0.15.0/24 area 0.0.0.0' -c 'network 10.0.23.0/24 area 0.0.0.0' -c 'network 10.0.43.0/24 area 0.0.0.0'  -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
        elif container == 'part1-r4-1':
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 4.4.4.4' -c 'network 10.0.41.0/24 area 0.0.0.0' -c 'network 10.0.43.0/24 area 0.0.0.0' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
        # configure weights default 
        subprocess.run(r_cmd + "vtysh -c 'config' -c 'interface eth0' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "vtysh -c 'config' -c 'interface eth1' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
        subprocess.run(r_cmd + "vtysh -c 'config' -c 'interface eth2' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
if options.path == "north":
    e1, e2, e3, e4 = getEthMappings()
    # r1
    subprocess.run(f"sudo docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface {e1}' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
    subprocess.run(f"sudo docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface {e2}' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
    # r3
    subprocess.run(f"sudo docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface {e3}' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
    subprocess.run(f"sudo docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface {e4}' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
if options.path == "south":
    e1, e2, e3, e4 = getEthMappings()
    # r1
    subprocess.run(f"sudo docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface {e1}' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
    subprocess.run(f"sudo docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface {e2}' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
    # r3
    subprocess.run(f"sudo docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface {e3}' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)
    subprocess.run(f"sudo docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface {e4}' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True, cwd=wdir)

    
    
