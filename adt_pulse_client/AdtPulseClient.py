import zeep
import logging
import pickle
from bs4 import BeautifulSoup
import requests
from requests.auth import AuthBase

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1

HTML_PARSER = 'html.parser'
LOGIN_FORM_TAG = 'form'
LOGIN_FORM_ATTRS = {'name': 'theform'}
ERROR_FIND_TAG = 'div'
ERROR_FIND_ATTR = {'id': 'warnMsgContents'}

ADTPULSE_DOMAIN = 'https://portal.adtpulse.com'

def adtpulse_version(ADTPULSE_DOMAIN):
    """Determine current ADT Pulse version"""
    resp = requests.get(ADTPULSE_DOMAIN)
    parsed = BeautifulSoup(resp.content, HTML_PARSER)
    adtpulse_script = parsed.find_all('script', type='text/javascript')[4].string
    if "=" in adtpulse_script:
        param, value = adtpulse_script.split("=",1)
    adtpulse_version = value
    adtpulse_version = adtpulse_version[1:-2]
    return(adtpulse_version)

ADTPULSE_CONTEXT_PATH = adtpulse_version(ADTPULSE_DOMAIN)
#print(ADTPULSE_CONTEXT_PATH)
LOGIN_URL = ADTPULSE_DOMAIN + ADTPULSE_CONTEXT_PATH + '/access/signin.jsp'
#print(LOGIN_URL)
DASHBOARD_URL = ADTPULSE_DOMAIN + ADTPULSE_CONTEXT_PATH + '/summary/summary.jsp'
#print(DASHBOARD_URL)

COOKIE_PATH = './adtpulse_cookies.pickle'
ATTRIBUTION = 'Information provided by portal.adtpulse.com'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/41.0.2228.0 Safari/537.36'





class AdtPulseClient:
    DISARMED = 10200
    ARMED_STAY = 10203
    ARMED_AWAY = 10201

    def __init__(self, username, password):
        self.soapClient = zeep.Client(LOGIN_URL)

        self.applicationVersion = ADTPULSE_CONTEXT_PATH
        self.username = username
        self.password = password
        self.token = False

        self.locations = []

        self.authenticate()

    def authenticate(self):
        """login to the system"""

        response = self.soapClient.service.AuthenticateUserLogin(self.username, self.password, self.applicationVersion)
        if response.ResultData == 'Success':
            self.token = response.SessionID
            self.populate_details()
        else:
            Exception('Authentication Error')

    def populate_details(self):
        """populates system details"""

        response = self.soapClient.service.GetSessionDetails(self.token, self.applicationVersion)

        logging.info('Getting session details')

        self.locations = zeep.helpers.serialize_object(response.Locations)['LocationInfoBasic']

        logging.info('Populated locations')

    def arm_stay(self, location_name=False):
        """arm - stay"""

        self.arm(ARM_TYPE_STAY, location_name)

    def arm_away(self, location_name=False):
        """arm - away"""

        self.arm(ARM_TYPE_AWAY, location_name)

    def arm(self, arm_type, location_name=False):
        """arm system"""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type,
                                                  '-1')  # Quickarm

        logging.info('armed')

    def get_security_panel_device_id(self, location):
        """find the device id of the security panel"""
        deviceId = False
        for device in location['DeviceList']['DeviceInfoBasic']:
            if device['DeviceName'] == 'Security Panel':
                deviceId = device['DeviceID']

        if deviceId is False:
            raise Exception('No security panel found')

        return deviceId

    def get_location_by_location_name(self, location_name=False):
        """get the location object for a given name (or the default location if none is provided"""

        location = False

        for loc in self.locations:
            if location_name is False and location is False:
                location = loc
            elif loc['LocationName'] == location_name:
                location = loc

        if location is False:
            raise Exception('Could not select location. Try using default location.')

        return location

    def get_armed_status(self, location_name=False):
        """Get the status of the panel"""
        location = self.get_location_by_location_name(location_name)

        response = self.soapClient.service.GetPanelMetaDataAndFullStatus(self.token, location['LocationID'], 0, 0, 1)

        status = zeep.helpers.serialize_object(response)

        alarm_code = status['PanelMetadataAndStatus']['Partitions']['PartitionInfo'][0]['ArmingState']

        return alarm_code

    def is_armed(self, location_name=False):
        """return True or False if the system is alarmed in any way"""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10201 or alarm_code == 10203:
            return True
        else:
            return False

    def disarm(self, location_name=False):
        """disarm the system"""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, '-1')
