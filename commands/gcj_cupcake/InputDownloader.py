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
import httplib, urllib, sys
from . import ZipUtils

# Class to download inputs from a specific problem.
# Create using the factory method at the end.
class _InputDownloader:
  # Initialize an input downloader for a specific problem.
  def __init__(self, host, cookie, middleware_token, contest_id, problem_id):
    # Store the specified attributes in the object.
    self.host = host
    self.cookie = cookie
    self.middleware_token = middleware_token
    self.contest_id = contest_id
    self.problem_id = problem_id

  # Download the specified input and store it in the specified file.
  def download(self, input_id, filename):
    # Format the selector inside the specified host.
    selector_format = '/codejam/contest/dashboard/do/{filename}'
    selector = selector_format.format(filename = filename)

    # Prepare request data for the server.
    request_data_map = {
      'cmd'                 : 'GetInputFile',
      'contest'             : self.contest_id,
      'problem'             : self.problem_id,
      'input_id'            : input_id,
      'filename'            : filename,
      'input_file_type'     : '0',
      'csrfmiddlewaretoken' : self.middleware_token,
    }

    # Prepare headers for the HTTP request.
    request_headers = {
      'Accept'          : 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
      'Accept-Encoding' : 'gzip,deflate,sdch',
      'Accept-Language' : 'en-US,en;q=0.8',
      'Accept-Charset'  : 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Referer'         : 'http://{host}/codejam/contest/dashboard?c={contest_id}'.format(host = self.host, contest_id = self.contest_id),
      'User-Agent'      : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4',
      'Cookie'          : self.cookie,
    }

    try:
      # Get input file from the server.
      sys.stdout.write('Getting input file "{0}" from "{1}"...\n'.format(filename, self.host))

      # Construct the final selector using the selector and the request data,
      # and the send the GET command to the server.
      request_data = urllib.urlencode(request_data_map)
      final_selector = selector + '?' + request_data
      http_connection = httplib.HTTPConnection(self.host)
      http_connection.request('GET', final_selector, '', request_headers)

      # Get the result and show the status and the number of bytes read.
      http_response = http_connection.getresponse()
      bytes_read = int(http_response.getheader('content-length', '0'))

      # Check if the server sent a response or ignored the request.
      if bytes_read > 0:
        # Unzip response data and log message with their sizes.
        unzipped_data = ZipUtils.unzip_data(http_response.read())
        sys.stdout.write('{0} {1}, {2} bytes read from server ({3} uncompressed).\n'.format(
          http_response.status, http_response.reason, bytes_read, len(unzipped_data)))

        try:
          # Write unzipped input data to the desired file.
          input_file = open(filename, 'wt')
          input_file.write(unzipped_data)
          input_file.close()
          sys.stdout.write('File "{0}" downloaded successfully.\n'.format(filename))
        except IOError as error:
          # Log the IO error and exit with error.
          sys.stderr.write('IO error happened while writing '
            'file "{0}": {1}'.format(filename, str(error)))
          sys.exit(1)
      else:
        # No response from the server, output warning.
        sys.stdout.write('{0} {1}, {2} bytes read from server.\n'.format(
          http_response.status, http_response.reason, bytes_read))
        sys.stdout.write('No response received from the server, this happens if '
          'you try to download the large input before solving the small input.\n')

      # Close the connection with the server.
      http_connection.close()
    except httplib.HTTPException as error:
      # Log the http exception and exit with error.
      sys.stderr.write('HTTP Exception: {0}\n'.format(str(error)))
      sys.exit(1)

# Factory method to create an input downloader object.
def create(host, cookie, middleware_token, contest_id, problem_id):
  return _InputDownloader(host, cookie, middleware_token, contest_id, problem_id)
