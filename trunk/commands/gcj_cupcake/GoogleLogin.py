# -*- coding: utf-8 -*-
#
# GCJ Cupcake by jbernadas
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
import sys, urllib, urllib2

# Exception class to indicate an error when authenticating with Google's ClientLogin.
class AuthenticationError(urllib2.HTTPError):
  # Initialize the error with the specified arguments.
  def __init__(self, url, code, message, headers, args):
    urllib2.HTTPError.__init__(self, url, code, message, headers, None)
    self.args = args
    self.reason = args["Error"]

# Create an http opener capable of handling anything needed to interact with
# Google's ClientLogin.
def _get_http_opener():
  # Create an http opener capable of handling proxies, http and https.
  opener = urllib2.OpenerDirector()
  opener.add_handler(urllib2.ProxyHandler())
  opener.add_handler(urllib2.UnknownHandler())
  opener.add_handler(urllib2.HTTPHandler())
  opener.add_handler(urllib2.HTTPDefaultErrorHandler())
  opener.add_handler(urllib2.HTTPErrorProcessor())
  opener.add_handler(urllib2.HTTPSHandler())
  return opener

# Parse the specified body as a dictionary with each element in a line, and
# key value pairs separated by '='.
def _parse_body_as_dict(body):
  return dict(line.split('=') for line in body.split('\n') if line)

def _get_google_authtoken(account_type, user, password, service, source):
  # Create a request for Google's Client login, with the specied data.
  auth_request_data_map = {
    'account_type' : account_type,
    'Email'        : user,
    'Passwd'       : password,
    'service'      : service,
    'source'       : source
  }
  auth_request_data = urllib.urlencode(auth_request_data_map)
  auth_url = 'https://www.google.com/accounts/ClientLogin'
  auth_request = urllib2.Request(auth_url, auth_request_data)
  
  try:
    # Create a custom opener, make the request and extract the body.
    http_opener = _get_http_opener()
    auth_response = http_opener.open(auth_request)
    auth_response_body = auth_response.read()

    # Parse the response data as a dictionary and return the 'Auth' key.
    auth_response_data = _parse_body_as_dict(auth_response_body)
    return auth_response_data['Auth']
  except urllib2.HTTPError as error:
    # Check if the error was a 403 - Forbidden. In that case, forward the exception
    # as an authentication error. Otherwise, just forward the exception.
    if error.code == 403:
      # Parse the error body as a dictionary and forward the exception as an
      # authentication error.
      response_dict = _parse_body_as_dict(error.read())
      raise AuthenticationError(auth_request.get_full_url(), error.code,
                                error.msg, error.headers, response_dict)
    else: raise

def _get_gae_cookie(host, service, auth_token):
  # Create a request for Google's service with the authentication token.
  continue_location = 'http://localhost/'
  cookie_request_data_map = {
    'continue' : continue_location,
    'auth'     : auth_token,
  }
  cookie_request_data = urllib.urlencode(cookie_request_data_map)
  cookie_url = 'https://{host}/_{service}/login?{data}'.format(
    host = host, service = service, data = cookie_request_data)
  cookie_request = urllib2.Request(cookie_url)
  
  try:
    # Create a custom opener, make the request and extract the body.
    http_opener = _get_http_opener()
    cookie_response = http_opener.open(cookie_request)
  except urllib2.HTTPError as error:
    # Keep the error as the cookie response.
    cookie_response = error

  # Check that a redirection was made to the required continue location.
  # Otherwise, return an HTTP error.
  response_code = cookie_response.code
  if (response_code != 302 or cookie_response.info()['location'] != continue_location):
    raise urllib2.HTTPError(cookie_request.get_full_url(), response_code, 
                            cookie_response.msg, cookie_response.headers,
                            cookie_response.fp)

  # Extract the cookie from the headers and remove 'HttpOnly' from it.
  cookie = cookie_response.headers.get('Set-Cookie')
  return cookie.replace('; HttpOnly', '')

# Retrieve the authentication token and cookie from the specified service, using
# the given user and password to authenticate.
def login(host, account_type, user, password, service, source):
  # Get the authentication token from Google's ClientLogin, and then get the cookie
  # from the application.
  auth_token = _get_google_authtoken(account_type, user, password, service, source)
  cookie = _get_gae_cookie(host, service, auth_token)
  return auth_token, cookie
