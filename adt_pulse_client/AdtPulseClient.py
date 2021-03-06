import logging
import os.path
import pickle
from bs4 import BeautifulSoup
from dateutil.parser import parse
import requests
from requests.auth import AuthBase

logging.basicConfig(filename='./adtpulse.log',level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

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

DEFAULT_COOKIEPATH = './adtpulse_cookies.pickle'
ATTRIBUTION = 'Information provided by portal.adtpulse.com'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/41.0.2228.0 Safari/537.36'


class AdtPulseClient:
    DISARMED = 10200
    ARMED_STAY = 10203
    ARMED_AWAY = 10201

    if 'CONF_COOKIEPATH' in globals():
        cookie_path = config.get(CONF_COOKIEPATH)
	_LOGGER.debug(cookie_path)
    else:
	cookie_path = DEFAULT_COOKIEPATH
	_LOGGER.debug(cookie_path)
		
    def _save_cookies(requests_cookiejar, filename):
        """Save cookies to a file."""
        with open(filename, 'wb') as handle:
            pickle.dump(requests_cookiejar, handle)

    def _load_cookies(filename):
        """Load cookies from a file."""
        with open(filename, 'rb') as handle:
            return pickle.load(handle)
        
    def __init__(self, hass, name, username, password, cookie_path):
        _LOGGER.info('Setting up ADTPulse...')
        self._name = name
        self._username = username
        self._password = password
        self._token = False
        self._cookie_path = cookie_path

        self.authenticate(self, username, password, cookie_path)

    def authenticate(self, username, password, cookie_path):
        """login to the system"""
        session = requests.session()
        login = session.get(LOGIN_URL)
        _LOGGER.info('Logging in to ADTPulse...')

        payload = {'usernameForm': username, 
                   'passwordForm': password}

        _LOGGER.warning('payload = %s', payload)

        if os.path.exists(cookie_path):
            session.cookies = _load_cookies(cookie_path)     

        login = session.post(LOGIN_URL, data = payload)
        
        _LOGGER.warning('Login POST URL: \n %s \n \n cookies are = %s ', login.url, session.cookies)

        self._save_cookies(session.cookies, cookie_path)

        login = session.get(DASHBOARD_URL, data = payload)

        _LOGGER.warning('Login GET URL: \n %s \n \n cookies are = %s ', login.url, session.cookies)
        
        if login.status_code == '200':
            self._JSESSIONID = login.JSESSIONID
#            self._x-token = login.x-token
#            self.populate_details()
            _LOGGER.info('Successfully logged in')

        else:
            Exception('Unable to login to portal.adtpulse.com')
            _LOGGER.warning('Unable to login to portal.adtpulse.com -- login_status_code = %s and cookies are = %s ! ', login.status_code, session.cookies)                
        
        get_armed_status()
        
        return login


    def populate_details(self):
        """populates system details"""

#        response = self._client.GetSessionDetails(self.token)

#        _LOGGER.info('Getting session details')

#        self.locations = zeep.helpers.serialize_object(response.Locations)['LocationInfoBasic']

#        _LOGGER.info('Populated locations')

    def arm_stay(self, location_name=False):
        """arm - stay"""

        self.arm(ARM_TYPE_STAY, location_name)

    def arm_away(self, location_name=False):
        """arm - away"""

        self.arm(ARM_TYPE_AWAY, location_name)

    def arm(self, arm_type, location_name=False):
        """arm system"""

#        location = self.get_location_by_location_name(location_name)
#        deviceId = self.get_security_panel_device_id(location)

#        self._client.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type,
#                                                  '-1')  # Quickarm

#        _LOGGER.info('armed')

    def get_security_panel_device_id(self, location):
        """find the device id of the security panel"""
        deviceId = False
#        for device in location['DeviceList']['DeviceInfoBasic']:
#            if device['DeviceName'] == 'Security Panel':
#                deviceId = device['DeviceID']

        if deviceId is False:
            raise Exception('No security panel found')

        return deviceId

    def get_location_by_location_name(self, location_name=False):
        """get the location object for a given name (or the default location if none is provided"""

        location = False

#        for loc in self.locations:
#            if location_name is False and location is False:
#                location = loc
#            elif loc['LocationName'] == location_name:
#                location = loc

        if location is False:
            raise Exception('Could not select location. Try using default location.')

        return location

    def get_armed_status(self, alarm_state_value=False):
        """Get the status of the panel"""
        _LOGGER.info('Retrieving alarm state from ADTPulse...')
        _load_cookies('adtpulse_cookies.pickle')

        session = requests.session()
        dashboard = session.get(DASHBOARD_URL)
        
        parsed = BeautifulSoup(dashboard.content, HTML_PARSER)
        # Find the DIV that contains the current alarm state
        alarm_state_div = parsed.find_all('div', id = 'divOrbTextSummary')
        #print (alarm_state_div)
        # Split the DIV into an array so that we can extract the value
        alarm_state_array = str(alarm_state_div).split('>')
        # If we check the array, we can see that the value we need is the 3rd item in the array (DIV-open, SPAN-open, ALARM STATE including SPAN-close, DIV-close)
        #print (alarm_state_array)
        # We can easily get rid of the DIV-open tag and the SPAN-open tag, by directly selecting the 3rd value from the array.
        #print(alarm_state_array[2])
        # However, this still includes a SPAN-close tag that we need to get rid of
        # Let's remove the closing SPAN tag as well by splitting this string by the opening of the tag with the '<' character
        alarm_state_string = str(alarm_state_array[2]).split('<')
        #print(alarm_state_string)
        # We can now simply select the cleaned up Alarm State by using the first value out of this new array
        alarm_state_value = alarm_state_string[0]
        state = alarm_state_value
        return state
        _LOGGER.info("Current Alarm State %s", state)

    def is_armed(self, location_name=False):
        """return True or False if the system is alarmed in any way"""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10201 or alarm_code == 10203:
            return True
        else:
            return False

    def disarm(self, location_name=False):
        """disarm the system"""

#        location = self.get_location_by_location_name(location_name)
#        deviceId = self.get_security_panel_device_id(location)

#        self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, '-1')
