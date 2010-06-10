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
import httplib, urllib, re, shutil, sys
from . import Constants, ZipUtils, DataManager, CodeJamLogin

# Read the dashboard of the specified contest.
def _read_dashboard(host, cookie, contest_id):
  # Prepare headers for the HTTP request.
  request_headers = {
    'Accept'          : 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
    'Accept-Encoding' : 'gzip,deflate,sdch',
    'Accept-Language' : 'en-US,en;q=0.8',
    'Accept-Charset'  : 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Referer'         : 'http://{host}/codejam'.format(host = host),
    'User-Agent'      : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4',
    'Cookie'          : cookie,
  }

  try:
    # Construct the final selection using the selector and the request data,
    # and the send the GET command to the server.
    selector = '/codejam/contest/dashboard'
    request_data = urllib.urlencode({'c' : contest_id})
    final_selector = selector + '?' + request_data
    http_connection = httplib.HTTPConnection(host)
    http_connection.request('GET', final_selector, '', request_headers)

    # Get the result and show the status and the number of bytes read.
    http_response = http_connection.getresponse()
    bytes_read = int(http_response.getheader('content-length', '0'))
    sys.stdout.write('{0} {1}, {2} bytes read from server.\n'.format(
      http_response.status, http_response.reason, bytes_read))

    # Get and unzip the dashboard and close the connection.
    contest_dashboard = ZipUtils.unzip_data(http_response.read())
    http_connection.close()
    return contest_dashboard
  except httplib.HTTPException as error:
    # Log the http exception and exit with error.
    sys.stderr.write('HTTP Exception: {0}\n'.format(str(error)))
    sys.exit(1)

# Parse the problem information from the dashboard contents.
def _parse_problems(dashboard):
  # Initialize regular expression and lists to hold parsed problems.
  problem_id, problem_name = [], []
  regexp = r'\s*GCJ\.problems\.push\s*\((\s*\{' \
           r'(\s*"[A-Za-z0-9]*"\s*:\s*"[^"]*",)*' \
           r'\s*"[A-Za-z0-9]*"\s*:\s*"[^"]*",?' \
           r'\s*})\);'

  # Process each match found in the dashboard, the match that represents the
  # problem is at the first position.
  for match in re.findall(regexp, dashboard, re.DOTALL):
    # Parse the problem data and add it to the array if and only if it has
    # an id. Also, assign '<unnamed>' to problems with no names.
    problem_data = eval(match[0], {}, {})
    if 'id' in problem_data:
      problem_id.append(problem_data['id'])
      problem_name.append(problem_data.get('name', '<unnamed>'))

  # Return the problems read in both lists.
  return problem_id, problem_name

# Parse the middleware tokens from the dashboard contents.
def _parse_middleware_tokens(dashboard):
  # Initialize regular expression and dictionary to hold parsed problems.
  middleware_tokens = {}
  regexp = r'\s*<form\s+id\s*=\s*"csrf-form-\w+"\s*>' \
           r'\s*<div\s+style\s*=\s*"\s*display:none;\s*"\s*>' \
           r'\s*<input\s+type\s*=\s*"hidden"\s*name\s*=\s*"csrfmiddlewaretoken"\s*value\s*=\s*"([^"]+)"\s*/>' \
           r'\s*</div\s*>' \
           r'\s*<input\s+type\s*=\s*"hidden"\s*name\s*=\s*"cmd"\s*value\s*=\s*"(\w+)"\s*/>'

  # Process each match found in the dashboard, the first match is the token and
  # the second match is its name.
  for token_value, token_name in re.findall(regexp, dashboard, re.DOTALL):
    middleware_tokens[token_name] = token_value

  # Return the dictionary with the tokens.
  return middleware_tokens

# Initialize configuration for the specified contest.
def init(contest_id, password = None):
  try:
    # Reset the current configuration file with the one provided by the user
    # and renew the cookie, so the middleware tokens are retrieved correctly.
    shutil.copy(Constants.USER_CONFIG_FILE, Constants.CURRENT_CONFIG_FILE)
    CodeJamLogin.login(password)
  except OSError as error:
    # Indicate that the current config file could not be created and exit with error.
    sys.stderr.write('Configuration file could not be created: {0}\n'.format(str(error)))
    sys.exit(1)

  try:
    # Read the current configuration file and extract the host and the cookie.
    contest_data = DataManager.read_data(Constants.CURRENT_CONFIG_FILE)
    host = contest_data['host']
    cookie = contest_data['cookie']
  except KeyError:
    # Indicate that no host or cookie was configured and exit with error.
    sys.stderr.write('No host or login cookie found in the configuration file.\n')
    sys.exit(1)

  # Get input file from the server.
  sys.stdout.write('Getting contest {1} information from "{0}"...\n'.format(host, contest_id))

  # Read the contest dashboard and parse the problems and middleware tokens from it.
  contest_dashboard = _read_dashboard(host, cookie, contest_id)
  problem_id, problem_name = _parse_problems(contest_dashboard)
  middleware_tokens = _parse_middleware_tokens(contest_dashboard)

  # Add the contest id, the problems and the middleware tokens to the contest data.
  contest_data['contest_id'] = contest_id
  contest_data['problem_id'] = problem_id
  contest_data['problem_name'] = problem_name
  contest_data['middleware_tokens'] = middleware_tokens

  # Finally, write the contest data to the current data file, and then
  # renew the cookie stored in the configuration.
  DataManager.write_data(contest_data, Constants.CURRENT_CONFIG_FILE)
  sys.stdout.write('Contest {0} initialized successfully, {1} problem(s) retrieved.\n'.format(
    contest_id, len(problem_id)))
