#!/home/markd/anaconda3/bin/python3

import re
import os, shutil
from subprocess import Popen, run, PIPE


BROADCAST = "192.168.1.0/24"

MAC_ADDRESSES = {
    "dc:a6:32:d6:cf:fb": "test"
}

def mapDevices(broadcast_addr=BROADCAST):
    process = Popen(f"nmap -sP {broadcast_addr}".split(), stdout=PIPE)
    process.wait()
    arp_process = run(f"arp -an".split(), stdout=PIPE)
    output = arp_process.stdout
    table = output.decode('utf8').split('\n')
    return table

def extractMacAddresses(apr_outputs, broadcast_addr=BROADCAST):
    ip_pattern = "\.".join(broadcast_addr.split(".")[0:3])
    mappingDict = {}
    pattern = re.compile(f".+(?P<ip>{ip_pattern}\.[0-9]+)\).+(?P<mac>[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}})\s.+")
    for line in apr_outputs:
        match = pattern.match(line)
        if match:
            mappingDict[match.group('mac')] = match.group('ip')
    return mappingDict

def mac_to_ips(mapping):
    address_dict = {}
    for mac in MAC_ADDRESSES.keys():
        name = MAC_ADDRESSES[mac]
        ip = mapping[mac]
        if name in address_dict:
            address_dict[name].append(ip)
        else:
            address_dict[name] = [ip]
    return address_dict

def generate_inventory(ip_dict):
    contents = ""
    for k in ip_dict:
        line = f"[{k}]\n"
        for ip in ip_dict[k]:
            line += f"{ip}\n"
        line += "\n"
        contents += line
    return contents

def write_to_file(inventory, filename="hosts.ini"):
    existing_files = os.listdir(os.getcwd())
    if filename in existing_files:
        shutil.copy(filename, filename+".old")

    with open(filename, "w") as fObj:
        fObj.write(inventory)

if __name__ == "__main__":
    print("refreshing and reading ARP table...")
    arp_table = mapDevices()
    print("Generating inventory file...\n")
    mapping = extractMacAddresses(arp_table)
    ip_dict = mac_to_ips(mapping)
    inventory = generate_inventory(ip_dict)
    print(inventory)
    write_to_file(inventory)

    