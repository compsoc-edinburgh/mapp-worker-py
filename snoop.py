# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys
import time
import re
import json
import urllib2
from datetime import datetime
from multiprocessing import Process, Lock, Pool
        

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self, username, password, hostname):
        self.hostname = hostname
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(username=username,
                            password=password,
                            hostname=hostname,
                            port=22)
        


    # Runs a user check on the remote host
    def usercheck(self):
        stdin, stdout, stderr = self.client.exec_command("w -h")
        users = stdout.readlines()
        
        data_dict = {
            "hostname":str(self.hostname),
            "user":"",
            "active":"",
            "timestamp":str(datetime.utcnow().isoformat())
        }
        ret = []
        
        for user in users:
            try:
                user = re.split("\s+", user)
                usr_i, usr_o, usr_e = self.client.exec_command("finger %s" % user[0])
                out = re.search("Name: (.*)", usr_o.readline())
                ret = (out.group(1), user[4])
                if user[1] == ":0":
                    data_dict['user']      = str(ret[0])
                    data_dict['active']    = str(ret[1])
            except AttributeError, IndexError:
                pass
        
        sys.stderr.write("USER @ %s: %s\n" % (self.hostname, data_dict['user']))
                
        req = urllib2.Request(
            "http://mapp.tardis.ed.ac.uk:5000/update",
            json.dumps(data_dict),
            {'Content-Type': 'application/json'})

        try:
            f = urllib2.urlopen(req)
            print json.loads(f.read())['status']
            f.close()
        except Exception as e:
            sys.stderr.write("DEBUG %s error when opening url : %s\n" % (self.hostname, str(e)))
        return ret
            
    # $wall the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % str(message))


        
        
if __name__ == "__main__":

    servers = ['ssh.tardis.ed.ac.uk','ssh1.tardis.ed.ac.uk']
    
    # servers = ['rosalinde', 'montparnasse', 'dancaire', 'lillas', 'vervcelli', 'zuniga',
    #            'rieti', 'venosa','trento', 'pavia', 'orlofsky', 'mereb', 'radames', 'ascoli',
    #            'tivoli', 'wideopen', 'twite', 'swanland', 'enna', 'gosforth', 'albenga',
    #            'hart', 'stork', 'brujon', 'pharoah', 'combeferre', 'remendado', 'escamillo',
    #            'micaela', 'lavello', 'marsala', 'mantua', 'spoleto', 'falconara', 'amelia',
    #            'parrot', 'wigton', 'falcon', 'raven', 'ciociosan', 'roxanne', 'yakuside',
    #            'lesgles', 'goro', 'daae', 'owl', 'owl', 'penguin', 'lodi', 'luni', 'palermo',
    #            'falke', 'scarpia', 'cavaradossi', 'amneris', 'babet', 'amanasro', 'ceilingcat',
    #            'lowick', 'seascale', 'ostiglia', 'allonby', 'yvan', 'claquesous', 'tosca',
    #            'spoletta', 'enjolras', 'nehebka', 'parma', 'carmen', 'messina', 'gabriel',
    #            'aida', 'frosch', 'thenardier', 'zoser', 'pollenzo', 'palestrina', 'ravenna',
    #            'bechstein', 'mocha', 'bluthner', 'dove', 'scarecrow', 'giry', 'savona',
    #            'vicenza', 'velma', 'avellino', 'morales', 'pontremoli', 'velletri',
    #            'angelotti', 'joly', 'courfeyrac', 'crow', 'giudicelli', 'pipit']


    lock = Lock()
    
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)
    
    def mapf(serv):
        try:
            s = Snoop(username, password, serv)
            userl = s.usercheck()
        except Exception as e:
            sys.stderr.write("DEBUG no-go for host %s : %s\n" % (serv, str(e)))
    
    p = Pool(20)
    p.map(mapf,servers)

    # Single threaded version:
    #for server in servers:
    #    mapf(server)
