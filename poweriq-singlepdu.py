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
#       Name:           poweriq-singlepdu.py
#       LastEdit:       30/04/2018
#       Version:        0.7
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
# Use: poweriq.py -a <api-token> -p <pdu id>
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
api_url_base = 'https://piq.exponential-e.com/api/v2/'

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
pdu_id= ''
api_token = ''

# Going to to check the Arguements and store the data
#
# Reading the Command line Arguements
myopts, args = getopt.getopt(sys.argv[1:],"a:p:")

for o, a in myopts:
    if o == '-a':
        api_token=a
    elif o == '-p':
        pdu_id=a
    else:
        print("Usage: %s -a api_token -p pdu_id" % sys.argv[0])

#Making the API call
#Creating the URL so we can prepare it for the API call
full_url = api_url_base + 'pdus/' + pdu_id


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
resp = requests.get(full_url,headers=headers, verify=False)
payload = resp.content

# initialize data here
data = json.loads(payload)

#now to collect the data which we are interested in
pdu_name= data['pdu']['name']
pdu_name_edit= pdu_name.replace(' ', '')
current = data['pdu']['reading']['inlet_readings'][0]['current']
watt_hour = data['pdu']['reading']['inlet_readings'][0]['watt_hour']
watt_hour_delta = data['pdu']['reading']['inlet_readings'][0]['watt_hour_delta']
unutilized_capacity = data['pdu']['reading']['inlet_readings'][0]['unutilized_capacity']


#So now we have the data collected, we are going to push this into influxdb
client = InfluxDBClient(host, port, user, password, dbname)
json_body = [
        {
            "measurement": "pdu",
            "tags": {
                "host": pdu_name_edit,
            },
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": {
                "current": current,
                "watt_hour": watt_hour,
                "watt_hour_delta": watt_hour_delta,
                "not_used_capacity": unutilized_capacity
            }
        }
    ]

#Place the data into the influxdb database
client.write_points(json_body)
