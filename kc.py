from optparse import OptionParser
import subprocess

# Start of program execution
parser = OptionParser()
parser.add_option('-d', '--docker', action='store_true', dest='docker', help='clone cs4480-2025-s/pa3 from gitlab and start up docker') 
parser.add_option('-t', '--topology', action='store_true', dest='topology', help='create network topology using Docker containers') 
parser.add_option('-e', '--ends', action='store_true', dest='ends', help='installs end host routes')
parser.add_option('-o', '--ospf', action='store_true', dest='ospf', help='start OSPF daemons on each router') 
parser.add_option('-p', '--path', type="choice", choices=["north", "south"], dest='path', help='path traffic should take. Either "north" or "south"') 
(options, args) = parser.parse_args()

if options.topology:
    subprocess.run("docker compose up -d", shell=True, check=True)
if options.ends:
    subprocess.run("docker exec -it part1-ha-1 route add -net 10.0.15.0/24 gw 10.0.14.4", shell=True, check=True)
    subprocess.run("docker exec -it part1-hb-1 route add -net 10.0.14.0/24 gw 10.0.15.4", shell=True, check=True)
if options.ospf:
    containers = ["part1-r1-1", "part1-r2-1", "part1-r3-1", "part1-r4-1"]
    for container in containers:
        r_cmd = f"docker exec -it {container} "
        # install ospf
        subprocess.run(r_cmd + "apt -y install curl", shell=True, check=True)
        subprocess.run(r_cmd + "apt -y install gnupg", shell=True, check=True)
        subprocess.run(r_cmd + "curl -s https://deb.frrouting.org/frr/keys.gpg | tee /usr/share/keyrings/frrouting.gpg > /dev/null", shell=True, check=True)
        subprocess.run(r_cmd + "apt install lsb-release", shell=True, check=True)
        subprocess.run(r_cmd + "FRRVER=\"frr-stable\"", shell=True, check=True)
        subprocess.run(r_cmd + "echo deb '[signed-by=/usr/share/keyrings/frrouting.gpg]' https://deb.frrouting.org/frr $(lsb_release -s -c) $FRRVER | tee -a /etc/apt/sources.list.d/frr.list", shell=True, check=True)
        subprocess.run(r_cmd + "apt update", shell=True, check=True)
        subprocess.run(r_cmd + "apt -y install frr frr-pythontools", shell=True, check=True)
        # edit daemon
        subprocess.run(r_cmd + "sed -i 's/^ospfd=no$/ospfd=yes/' /etc/frr/daemons", shell=True, check=True)
        subprocess.run(r_cmd + "service frr restart", shell=True, check=True)
        # configure routers in vtysh
        if container == "part1-r1-1":
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 1.1.1.1' -c 'network 10.0.14.0/24 area 0.0.0.0' -c 'network 10.0.21.0/24 area 0.0.0.0' -c 'network 10.0.41.0/24 area 0.0.0.0'  -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
        elif container == 'part1-r2-1':
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 2.2.2.2' -c 'network 10.0.21.0/24 area 0.0.0.0' -c 'network 10.0.23.0/24 area 0.0.0.0' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
        elif container == 'part1-r3-1':
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 3.3.3.3' -c 'network 10.0.15.0/24 area 0.0.0.0' -c 'network 10.0.23.0/24 area 0.0.0.0' -c 'network 10.0.43.0/24 area 0.0.0.0'  -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
        elif container == 'part1-r4-1':
            subprocess.run(r_cmd + "vtysh -c 'config' -c 'router ospf' -c 'ospf router-id 4.4.4.4' -c 'network 10.0.41.0/24 area 0.0.0.0' -c 'network 10.0.43.0/24 area 0.0.0.0' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
        # configure weights default 
        subprocess.run(r_cmd + "vtysh -c 'config' -c 'interface eth0' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
        subprocess.run(r_cmd + "vtysh -c 'config' -c 'interface eth1' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
        subprocess.run(r_cmd + "vtysh -c 'config' -c 'interface eth2' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
if options.path == "north":
    # r1
    subprocess.run("docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface 10.0.21.4' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
    subprocess.run("docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface 10.0.41.4' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
    # r3
    subprocess.run("docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface 10.0.23.4' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
    subprocess.run("docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface 10.0.43.4' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
if options.path == "south":
    # r1
    subprocess.run("docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface 10.0.21.4' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
    subprocess.run("docker exec -it part1-r1-1 vtysh -c 'config' -c 'interface 10.0.41.4' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
    # r3
    subprocess.run("docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface 10.0.23.4' -c 'ip ospf cost 10' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)
    subprocess.run("docker exec -it part1-r3-1 vtysh -c 'config' -c 'interface 10.0.43.4' -c 'ip ospf cost 5' -c 'exit' -c 'exit' -c 'write'", shell=True, check=True)

    
    
