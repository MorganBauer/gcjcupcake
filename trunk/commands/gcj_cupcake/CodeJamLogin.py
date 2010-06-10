# -*- coding: utf-8 -*-
#
# GCJ Cupcake by jbernadas, v1.0 beta
# Copyright (C) 2010  Jorge Bernadas (jbernadas@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import getpass, sys, urllib2
import BaseHTTPServer
from . import GoogleLogin, Constants, DataManager

# Get the user password from a possible input string, a value inside the
# configuration file or directly from the user.
def _get_user_password(user):
  # Read configuration information from the configuration file
  # and see if the password is there.
  current_config = DataManager.read_data(Constants.USER_CONFIG_FILE)
  if 'password' in current_config:
    return current_config['password']

  # No password was specified in the command line or the configuration file,
  # read it from the user.
  print 'Cannot find password for user {0}.'.format(user)
  return getpass.getpass()

# Retrieve the authentication token and cookie from the code jam server,
# using the given user and password to authenticate.
def _make_login(host, user, password):
  try:
    # Get the authentication token and gae cookie using the GoogleLogin module.
    sys.stdout.write('Logging into "{0}" with user "{1}"...\n'.format(host, user))
    application_name = 'jbernadas-gcj_cupcake-v{0}'.format(Constants.VERSION)
    auth_token, cookie = GoogleLogin.login(host, 'GOOGLE', user, password, 'ah', application_name)
    sys.stdout.write('Successfully logged into "{0}" with user "{1}".\n'.format(host, user))
    return auth_token, cookie
  except GoogleLogin.AuthenticationError as error:
    # Print a human-readable error based on the error and exit with an error code.
    if error.reason == 'BadAuthentication':
      sys.stderr.write('Invalid username or password.\n')
    elif error.reason == 'CaptchaRequired':
      sys.stderr.write('Please go to '
                       'https://www.google.com/accounts/DisplayUnlockCaptcha\n'
                       'and verelify you are a human. Then try again.\n')
    elif error.reason == 'NotVerelified':
      sys.stderr.write('Account not verelified.')
    elif error.reason == 'TermsNotAgreed':
      sys.stderr.write('User has not agreed to TOS.')
    elif error.reason == 'AccountDeleted':
      sys.stderr.write('The user account has been deleted.')
    elif error.reason == 'AccountDisabled':
      sys.stderr.write('The user account has been disabled.')
    elif error.reason == 'ServiceDisabled':
      sys.stderr.write('The user\'s access to the service has been disabled.')
    elif error.reason == 'ServiceUnavailable':
      sys.stderr.write( 'The service is not available, try again later.')
    sys.exit(1)
  except urllib2.HTTPError as error:
    # Log the HTTP error and exit with an error code.
    sys.stderr.write('HTTP error while logging into the Google Code Jam server ({0}): {1}\n'.format(
      error.code, BaseHTTPServer.BaseHTTPRequestHandler.responses[error.code][0]))
    sys.exit(1)

# Renew contest cookie for the specified user in the host.
def login(password = None):
  try:
    # Read the current configuration file and extract the host and username.
    contest_data = DataManager.read_data(Constants.CURRENT_CONFIG_FILE)
    host = contest_data['host']
    user = contest_data['user']
  except KeyError:
    # Indicate that no host or username was configured and exit with error.
    sys.stderr.write('No host or username was found in the user configuration file.\n')
    sys.exit(1)

  # Retrieve the password from elsewhere, as the user didn't provide one.
  if not password:
    password = _get_user_password(user)

  # Log in into Google servers using Client Login and store it in the configuration.
  cookie = _make_login(host, user, password)[1]
  contest_data['cookie'] = cookie

  # Finally, write the contest data to the current data file and return the cookie.
  DataManager.write_data(contest_data, Constants.CURRENT_CONFIG_FILE)
  return cookie
