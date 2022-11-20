import hashlib
import requests
import time
#import threading
import paho.mqtt.client as mqtt #import the client1
import time
from bs4 import BeautifulSoup
import re
import json
import functools
import argparse
import urllib.parse

#loe parameetrid jsonist
def __init__(opt_file):
  with opt_file:
    _cfg = json.load(opt_file)
    _will = (self._cfg['CTRL_PUBLISH_TOPIC'], 'Disconnected', 1, True)


#MQTT DEF
############
def on_log(client, userdata, level, buf):
  print("log: ",buf)


def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)


_areas_action_map = {
    # Mappring from human readable commands to machine readable
    'Disarm'   : 'd',
    'Arm'      : 'r',
    'Arm_sleep': 'p',
    'Arm_stay' : 's'
}

# based on zone type set icon, Icons definition
_icons_map = {
     'but': 'mdi:alarm-light-outline',
     'smo': 'mdi:fire',
     'win': 'mdi:window-closed-variant',
     'doo': 'mdi:door',
     'ine': 'mdi:door',
     'pir': 'mdi:motion-sensor',
     'Area': 'mdi:shield-home'
}


#  make YAML content 
def mqtt_YAML_areas(n, teekond):
  with open('pd_YAML_MQTT.txt', 'a') as f:
    if sisu != " ":
      f.writelines("    - name: 'pd-area-" + str(n) +"'\n")
      f.writelines("      unique_id: 'sensor.pd_area_" + str(n) +"'"+"\n")
      f.writelines("      state_topic: '"+ teekond +"areas_status/"+str(n)+"/state'"+"\n")
      #f.writelines("      payload_on: 'ON'"+"\n")
      #f.writelines("      payload_off: 'OFF'"+"\n")
      f.writelines("      availability_topic: '"+ teekond +"availability'"+"\n")
      f.writelines("      payload_available: 'online'"+"\n")
      f.writelines("      payload_not_available: 'offline'"+"\n")
      f.writelines("      qos: 0"+"\n")
      #f.writelines("      device_class: opening"+"\n")
      f.writelines("      value_template: '{{ value_json.state }}'"+"\n")
      f.writelines("      icon: '"+_icons_map['Area']+"'"+"\n")
      f.writelines("\n")

def mqtt_YAML(n,sisu,teekond):
  with open('pd_YAML_MQTT.txt', 'a') as f:
    if sisu != " ":
      f.writelines("    - name: '" + sisu +"'"+"\n")
      f.writelines("      unique_id: '"+  sisu +"'"+"\n")
      f.writelines("      state_topic: '"+ teekond +"zones_status/"+str(n)+"/state'"+"\n")
      f.writelines("      payload_on: 'ON'"+"\n")
      f.writelines("      payload_off: 'OFF'"+"\n")
      f.writelines("      availability_topic: '"+ teekond +"availability'"+"\n")
      f.writelines("      payload_available: 'online'"+"\n")
      f.writelines("      payload_not_available: 'offline'"+"\n")
      f.writelines("      qos: 0"+"\n")
      f.writelines("      device_class: opening"+"\n")
      f.writelines("      value_template: '{{ value_json.state }}'"+"\n")
      f.writelines("      icon: '"+_icons_map[sisu[3:6]]+"'"+"\n")
      f.writelines("\n")


class Paradox_IP100_Error(Exception):

    pass

def to_8bits(s):
   return "".join(map(lambda x: chr(ord(x) % 256), s))

def paradox_rc4(data, key):
    S, j, out = list(range(256)), 0, []

    # This is not standard RC4
    for i in range(len(key) - 1, -1, -1):
        j = (j + S[i] + ord(key[i])) % 256
        S[i], S[j] = S[j], S[i]

    i = j = 0
    # This is not standard RC4
    for ch in data:
        i = i % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(ord(ch) ^ S[(S[i] + S[j]) % 256])
        i += 1

    return "".join(map(lambda x: '{0:02x}'.format(x), out)).upper()



def prep_cred(user, pwd, sess):
        pwd_8bits = to_8bits(pwd)
        pwd_md5 = hashlib.md5(pwd_8bits.encode('ascii')).hexdigest().upper()
        spass = pwd_md5 + sess
        return {'u': paradox_rc4(user, spass),'p': hashlib.md5(spass.encode('ascii')).hexdigest().upper()}
        #return { sisu } 


_tables_map = {
    # A map from human readable info about the alarm, to "table" (in fact, array) names used in IP150 software
    #'triggered_alarms': 'tbl_alarmes', # Redundant list of zones with an alarm currently triggered. A zone in alarm will also be reported in the 'tbl_useraccess' table
    #'troubles': 'tbl_troubles', # Could use this list to publish alarm troubles, not required for now
    # The next list provides the status (0=Closed, 1=Open) for each zone
    'zones_status': {
        'name': 'tbl_statuszone',
        'map' : {
#            0: 'Closed',
#            1: 'Open',
#            2: 'In_alarm',
#            3: 'Closed_Trouble',
#            4: 'Open_Trouble',
#            5: 'Closed_Memory',
#            6: 'Open_Memory',
#            7: 'Bypass',
#            8: 'Closed_Trouble2',
#            9: 'Open_Trouble2'
            0: 'OFF',
            1: 'ON',
            2: 'ON',
            3: 'OFF',
            4: 'ON',
            5: 'OFF',
            6: 'ON',
            7: 'OFF',
            8: 'OFF',
            9: 'ON'

        }
    },
    # The next list provides the status (as an integer, 0 for area not enabled) for each supported area
    'areas_status': {
        'name': 'tbl_useraccess',
        'map' : {
            0: 'Unset',
            1: 'Disarmed',
            2: 'Armed',
            3: 'Triggered',
            4: 'Armed_sleep',
            5: 'Armed_stay',
            6: 'Entry_delay',
            7: 'Exit_delay',
            8: 'Ready',
            9: 'Not_ready',
            10: 'Instant'
        }
    },
    # tbl_alarmes  - Siia panna õiged veakoodid
    'alarmes_status': {
        'name': 'tbl_alarmes',
        'map' : {
             '': 'Unarmed',   
            '0': 'Alarm',
            '1': 'Disarmed',
            '2': 'Armed',
            '3': 'Triggered',
            '4': 'Armed_sleep',
            '5': 'Armed_stay',
            '6': 'Entry_delay',
            '7': 'Exit_delay',
            '8': 'Ready',
            '9': 'Not_ready',
            '15': 'Battery Fault'
        }
    },

    # tbl_troubles  - Siia panna õiged veakoodid
    'troubles_status': {
        'name' : 'tbl_troubles',
        'map'  : {
            '0': 'Clean smoke detector, fire zone trouble or zone communication failure',
            '1': 'Fire loop trouble',
            '2': 'Module missing or failed to communicate',
            '3': 'Module power failure (AC fail)',
            '4': 'Module reporting via phone line failed',
            '5': 'Modules auxiliary power interrupted(aux. limit.)',
            '6': 'Modules battery low or disconnected',
            '7': 'Modules enclosure has been tampered',
            '8': 'Modules ROM memory corrupted',
            '9': 'Printer module does not detect a printer',
            '10': 'System cannot detect a phone line(TLM)',
            '11': 'System communication with modules has failed(combus)',
            '12': 'System power failure(AC fail)',
            '13': 'System reporting via phone failed',
            '14': 'Systems auxiliary power interrupted(aux limit)',
            '15': 'Systems battery low or disconnected',
            '16': 'Systems bell/siren not connected',
            '17': 'Systems bell/siren power interrupted(bell limit)',
            '18': 'Systems ROM memory corrupted',
            '19': 'Time and date have been lost',
            '20': 'Too many modules are connected to the system',
            '21': 'Wireless zone low battery',
            '22': 'Wireless zone supervision loss',
            '23': 'Zone has been tampered',
            '24': 'System RF interference',
            '25': ' '     
        }
     }
}

_areas_action_map = {
    # Mappring from human readable commands to machine readable
    'Disarm'   : 'd',
    'Arm'      : 'r',
    'Arm_sleep': 'p',
    'Arm_stay' : 's'
}


_tables_list = {'tbl_areanam','tbl_troublename' }


def _js2array(varname, script):
   res = re.search('{} = new Array\((.*?)\);'.format(varname), script)
   res = '[{}]'.format(res.group(1))
   return json.loads(res)


def find_nth(string, substring, n):
   if (n == 1):
       return string.find(substring)
   else:
       return string.find(substring, find_nth(string, substring, n - 1) + 1)


def LoadConfigDatafromFile():
   argp = argparse.ArgumentParser(description='MQTT adapter for Paradox IP100 Alarms')
   argp.add_argument('config', type=argparse.FileType(), default='options.json', nargs='?')
   args = vars(argp.parse_args())
   configFile = args['config'] 
   config = json.load(configFile)
   print(config)
   return config




# ----------------------------------------------------------------

# MAIN PROGRAM

if __name__ == '__main__':
   print("IP100 to MQTT is started")
   
   config = LoadConfigDatafromFile()
   print("Config Data is loaded")
   #print(config['MQTT_YAML_WRITE'])
   
   #print(config['MQTT_USERNAME'])

   
   #segaduse parast
   config['MQTT_YAML_WRITE']=False

   #broker_address="test.mosquitto.org"
   #MQTT_ADDRESS=config['MQTT_ADDRESS']
   #print('.........',MQTT_ADDRESS)
   #MQTT_ADDRESS="192.168.2.204"
   
   #IP100 userinfo
   user = "mqttbroker"
   passw = "sittjakusi123"
   publish_root = 'homeassistant/binary_sensor/paradox/'
   mqtt_yaml_write = False  #True Do not print YAML setting for MQTT into text files

   config['IP00_ADDRESS']='http://192.168.2.115'
   
   
   print("create MQTT instances")
   client = mqtt.Client("IP100_info") 
   client.on_message=on_message 
   client.username_pw_set(username=user, password=passw)
      
   print("connecting to broker")
   client.connect(config['MQTT_ADDRESS']) #connect to broker
   client.loop_start() #start the loop
   
   
   #exit()
   
   # Ask for a login page, to get the 'sess' salt
   lpage = requests.get('{}/login_page.html'.format(config['IP00_ADDRESS']), verify=False)
   # Extract the 'sess' salt
   off = lpage.text.find('loginaff')

   if off == -1:   # juhul kui ei laetud õiget lehte siis tee logout ja lae uuesti
      time.sleep(1) 
      logout = requests.get('{}/logout.html'.format(config['IP00_ADDRESS']), verify=False)
      time.sleep(2)
      #raise Paradox_IP100_Error('Wrong page fetcehd. Did you connect to the right server and port? Server returned: #{}'.format(lpage.text))
      lpage = requests.get('{}/login_page.html'.format(config['IP00_ADDRESS']), verify=False)
      # Extract the 'sess' salt
      off = lpage.text.find('loginaff')
      #print('logi välja ja sisse')   
     
   sess = lpage.text[off + 10:off + 26]
   creds = prep_cred(config['PANEL_CODE'], config['PANEL_PASSWORD'], sess)
   print('Secret:', sess,",",creds)
   
   #login
   defpage = requests.get('{}/default.html'.format(config['IP00_ADDRESS']), params=creds, verify=True)
   #print (defpage.text)
   time.sleep(6)  # wait as long IP100 login is processing
   
   # read zones names to table
   mapdef_page = requests.get('{}/index.html'.format(config['IP00_ADDRESS']), params=creds, verify=False)
   mapdef_parsed = BeautifulSoup(mapdef_page.text, 'html.parser')
   #print (mapdef_parsed)
   
   script=find_nth("mapdef_parsed", "script", 2)
   sisu = str(mapdef_parsed.find("head"))
   
   script=sisu[sisu.find("tbl_zone"):]
   
   zone_names = _js2array('tbl_zone', script)
   
   
   # Publish zone names to MQTT   
   # Make MQTT YAML faili sisu
   
   if config['MQTT_YAML_WRITE']:
     print('save YAML setting for MQTT into  "mqtt_entities.yaml"')
     with open('pd_YAML_MQTT.txt', 'w') as f:
       f.write('  binary_sensor:'+"\n")
       f.close()    
       
   for n in range(0, 96): 
     if (n % 2) != 0:
       zonenr=int(n/2)+1
       sisu =  config['PUBLISH_ROOT'] + 'zones_status' '/' + str(zonenr) + '/name'
       if config['MQTT_YAML_WRITE']: 
         mqtt_YAML(zonenr,zone_names[n], config['PUBLISH_ROOT'])  #tekstifaili panek   juhul kui soovitakse
       client.publish(sisu,zone_names[n])
   # textifaili sulgemine
   
   if config['MQTT_YAML_WRITE']:
     with open('pd_YAML_MQTT.txt', 'a') as f:
       f.write('  sensor:'+"\n")    
     for n in range(1, 4): 
       mqtt_YAML_areas(n, config['PUBLISH_ROOT'])  #tekstifaili panek   juhul kui soovitakse
   
      
   # Paradoxi logbook card-i entity list
   if config['MQTT_YAML_WRITE']:  
     print('save entity setting for logbookinto  "mqtt_entities.yaml"')
     with open('pd_MQTT_entities.txt', 'w') as f:
       f.write("type: logbook"+"\n")
       f.write("entities:"+"\n")
       for n in range(0, 96): 
         if (n % 2) != 0:
           zonenr=int(n/2)+1
           if zone_names[n] != " ":
             zonename=zone_names[n]
             zonename=zonename.replace('-', '_')
             f.write("  - binary_sensor."+ zonename+"\n")
       f.write("hours_to_show: 24"+"\n")
   
   
   #Eelmised staatused defineerida/nullida
   prev_state = {}
   
   # SIIA TEE TSÜKKEL  < ///////////
   print("MQTT Cycle ----->")
   
   #Statusdata sisselugemine
   
   while True:
     status_page = requests.get('{}/statuslive.html'.format(config['IP00_ADDRESS']), params=creds, verify=False) 
     htmltext = status_page.text
     
     status_parsed = BeautifulSoup(status_page.text, 'html.parser')
     if status_parsed.find('form', attrs={'name': 'statuslive'}) is None:
        raise Paradox_IP150_Error('Could not retrieve status information')
     script = status_parsed.find('script').string
     #print(script)
   
     #  siia tuleb teha keepalive message, mitte iga kord saata
     topic=config['PUBLISH_ROOT'] + 'availability'
     client.publish(topic,'online')
     
     cur_state = {}   
     for table in _tables_map.keys():
         #print (table)
         #Extract the js array for the current "table"
         tmp = _js2array(_tables_map[table]['name'], script)
         #Map the extracted machine values to the corresponding human values
         cur_state[table] = [(i, _tables_map[table]['map'][x]) for i,x in enumerate(tmp, start=1)]
         #print (sisu[table])
         #print('------------------')
   
     
     # Make table of updated parameters
     updated_state = {}
     for d1 in cur_state.keys():
        if d1 in prev_state:
             
             for cur_d2, prev_d2 in zip(cur_state[d1], prev_state[d1]):
                 #print('-------->',cur_d2, ', ',prev_d2)
                 if cur_d2 != prev_d2:
                     if d1 in updated_state:
                         updated_state[d1].append(cur_d2)
                     else:
                         updated_state[d1] = [cur_d2]
        else:
             updated_state[d1] = cur_state[d1]
     
     # make current state previous 
     prev_state = cur_state
     #sisu = updated_state  
   
     # publish changes only  
     if len(updated_state) > 0:
       for data_topic in updated_state.keys():
           for d2 in zip(updated_state[data_topic]):
             #print(data_topic)
             #print('d2 ',d2)
             topic = config['PUBLISH_ROOT'] + data_topic +'/'+ str(d2[0][0])+'/state'
             state = d2[0][1]
             #print(topic,' ', state)
             client.publish(topic,state)
     
     time.sleep(1)
    # End of main Cycle

   #MOTTETU KRAAM 
   client.on_log=on_log
   client.loop_forever()
   time.sleep(14)
   client.loop_stop() #stop the loop
   #logout
   defpage = requests.get('{}/logout.html'.format(config['IP00_ADDRESS']), params=creds, verify=True)
   #htmltext = defpage.text
   #print (htmltext)
