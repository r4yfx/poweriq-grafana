#
#
# .SYNOPSIS
# PowerIQ -  Raritan Rack PDU API Data to Grafana using InfluxDB
#
# .DESCRIPTION
# This script speaks to the PowerIQ API and transfers the pdu information
# The information provided gives us the currently power reading, unutilized capacity,
# along with the watt hour & delta.
#
# .NOTES
#       Name:           poweriq-dualpdu.py
#       LastEdit:       02/05/2018
#       Version:        1.0
#       KeyWords:       PowerIQ, Grafana, InfluxDB, Raritan, Python
#
# Copyright 2018 Raymond Setchfield
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Use: poweriq.py <api-token> <pdu id> <pdu id>
#
import getopt
import sys
import requests
import urllib3
import json
import time
from influxdb import InfluxDBClient

#################################################################################
#                                                                               #
#                   Editable information on this section                        #
#                                                                               #
#################################################################################

#API URL
api_url_base = 'https://pdu-url/api/v2/'

#InfluxDB Configuration
host = '127.0.0.1'
port = '8086'
user = 'username'
password = 'password'
dbname = 'influxdb-name'

#################################################################################
#                                                                               #
#                        Do not edit past this line                             #
#                                                                               #
#################################################################################
#
# Store Input Arguements
api_token = ''
pdu_id_a = ''
pdu_id_b = ''

# Going to to check the Arguements and store the data
#
# Reading the Command line Arguements
api_token = sys.argv[1]
pdu_id_a = sys.argv[2]
pdu_id_b = sys.argv[3]

#Making the API call
#Creating the URL so we can prepare it for the API call
full_urla = api_url_base + 'pdus/' + pdu_id_a
full_urlb = api_url_base + 'pdus/' + pdu_id_b

#Creating the Headers
headers = {
    'Authorization': 'Basic ' + api_token,
    'Content-Type': 'application/json',
        'Accept': 'application/json',
}
##print headers
# Now the data is all formed the way I want it. I shall start making the call, but we are also going to supress the insecure SSL request warnings too
# The verification of the SSL is set to False too, to stop any issues with self signed certs, or invalid certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
respa = requests.get(full_urla,headers=headers, verify=False)
respb = requests.get(full_urlb,headers=headers, verify=False)
payloada = respa.content
payloadb = respb.content

# initialize data here
data_a = json.loads(payloada)
data_b = json.loads(payloadb)

#now to collect the data which we are interested in
pdu_namea= data_a['pdu']['name']
pdu_name_edita= pdu_namea.replace(' ', '')
pdu_name= pdu_name_edita[:8]
currenta = data_a['pdu']['reading']['inlet_readings'][0]['current']
currentb = data_b['pdu']['reading']['inlet_readings'][0]['current']
watt_houra = data_a['pdu']['reading']['inlet_readings'][0]['watt_hour']
watt_hourb = data_b['pdu']['reading']['inlet_readings'][0]['watt_hour']
watt_hour_deltaa = data_a['pdu']['reading']['inlet_readings'][0]['watt_hour_delta']
watt_hour_deltab = data_b['pdu']['reading']['inlet_readings'][0]['watt_hour_delta']
unutilized_capacitya = data_a['pdu']['reading']['inlet_readings'][0]['unutilized_capacity']
unutilized_capacityb = data_b['pdu']['reading']['inlet_readings'][0]['unutilized_capacity']
voltagea = data_a['pdu']['reading']['inlet_readings'][0]['voltage']
voltageb = data_b['pdu']['reading']['inlet_readings'][0]['voltage']
kilowatta = currenta * voltagea
kilowattb = currentb * voltageb
totalkilowatt = kilowatta + kilowattb

#So now we have the data collected, we are going to push this into influxdb
client = InfluxDBClient(host, port, user, password, dbname)
json_body = [
        {
            "measurement": "pdus",
            "tags": {
                "host": pdu_name,
            },
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": {
                "current-pdu-a": currenta,
                "current-pdu-b": currentb,
                "watt-hour-pdu-a": watt_houra,
				        "watt-hour-pdu-b": watt_hourb,
				        "watt-hour-delta-pdu-a": watt_hour_deltaa,
				        "watt-hour-delta-pdu-b": watt_hour_deltab,
                "voltage-pdu-a": voltagea,
				        "voltage-pdu-b": voltageb,
				        "kilowatt-pdu-a": kilowatta,
				        "kilowatt-pdu-b": kilowattb,
				        "total-kilowatt": totalkilowatt				
            }
        }
    ]

#Place the data into the influxdb database
client.write_points(json_body)
