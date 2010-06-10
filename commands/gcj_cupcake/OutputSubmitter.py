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
import httplib, random, os, shutil, sys
from . import ZipUtils, MultipartData

# Class to submit outputs from a specific problem.
# Create using the factory method at the end.
class _OutputSubmitter:
  # Initialize an output submitter for a specific problem.
  def __init__(self, host, cookie, middleware_token, contest_id, problem_id):
    # Store the specified attributes in the object.
    self.host = host
    self.cookie = cookie
    self.middleware_token = middleware_token
    self.contest_id = contest_id
    self.problem_id = problem_id

  # Zip all source directories into files, 
  def _prepare_source_files(self, source_names):
    # Initialze set for the source names, the ignored zip files and all
    # temporary created files.
    new_source_names = set()
    ignored_zips = set()
    tmp_files = set()

    # Process each source specified by the user.
    for source in source_names:
      # Check if the source is a directory or a file.
      if os.path.isdir(source):
        # Create a zip file for the folder and add it to the prepared sources
        # and the temporary files to erase.
        zip_filename = '{1}_{0}.zip'.format(random.randrange(0, 2**31 - 1),
          source.replace('\\', '_').replace('/', '_'))
        print 'Compressing directory "{0}" into file "{1}"...'.format(source, zip_filename)
        ignored_zips.update(ZipUtils.make_zip_file([source], zip_filename, ['.zip']))
        new_source_names.update([zip_filename])
        tmp_files.update([zip_filename])
      else:
        # Add files directly to the prepared sources.
        new_source_names.update([source])

    # Return all generated sets.
    return new_source_names, ignored_zips, tmp_files

  # Extract the result from the server response data.
  def _parse_result(self, response_data):
    # Convert the response data to a dictionary and return the message.
    values = eval(response_data, {'false':False, 'true':True})
    return values.get('msg', 'No message found')

  # Submit the specified output and sources file to the problem.
  def submit(self, input_id, output_name, source_names, gzip_body = True,
             zip_sources = False, add_ignored_zips = False):
    # Prepare the source files (zipping all directories). After this, source_names
    # will only contain text files and zip files specified directly or by compressing
    # a directory.
    source_names, ignored_zips, tmp_files = self._prepare_source_files(set(source_names))

    # Check if the user requested to zip source files.
    if zip_sources:
      # Generate a random name for the zipped source files and print message.
      zip_filename = '__plain_files_{0}.zip'.format(random.randrange(0, 2**31 - 1))
      print 'Compressing files "{1}" into file "{0}"...'.format(zip_filename,
        ', '.join(source for source in source_names if os.path.splitext(source)[1] != '.zip'))

      # Fill the zip file with the remaining text sources (ignoring zip files).
      # Then, substitute the list with the ignored zip files and the new one,
      # adding it to the temporary file list.
      source_names = ZipUtils.make_zip_file(source_names, zip_filename, ignore_exts = ['.zip'])
      source_names.update([zip_filename])
      tmp_files.update([zip_filename])

    # Check if the user requested to add the ignored zip files inside
    # included directories.
    if add_ignored_zips:
      # Copy and add each ignored file to the source list.
      for ignored_zip in ignored_zips:
        # Generate the zip copy filename by substituting path with underscores and
        # adding a random number to prevent collisions.
        path, ext = os.path.splitext(ignored_zip)
        zip_copy_filename = '{1}_{0}{2}'.format(random.randrange(0, 2**31 - 1),
          path.replace('\\', '_').replace('/', '_'), ext)
        print 'Copying file "{1}" to temporary file "{0}"...'.format(
          zip_copy_filename, os.path.basename(ignored_zip))

        try:
          # Make a copy of the ignored zip file and add the copy to the sources
          # list and the temporary list.
          shutil.copy(ignored_zip, zip_copy_filename)
          source_names.update([zip_copy_filename])
          tmp_files.update([zip_copy_filename])
        except OSError as error:
          # Log the OS error and exit with error.
          sys.stderr.write('OS error happened while copying zip file "{0}" to '
            '"{1}": {2}'.format(ignored_zip, zip_copy_filename, str(error)))
          sys.exit(1)

    # Generate a random boundary string to separate multipart data and
    # create a multipart data object with it.
    multipart_boundary = '----jbernadasMultipartBoundary{0}'.format(random.randrange(0, 2**31 - 1))
    multipart_data = MultipartData.create(multipart_boundary)

    # Create HTTP headers to send in the POST package.
    request_headers = {
      'Accept'           : 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
      'Accept-Encoding'  : 'gzip,deflate,sdch',
      'Accept-Language'  : 'en-US,en;q=0.8',
      'Accept-Charset'   : 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Content-Type'     : 'multipart/form-data; boundary={0}'.format(multipart_boundary),
      'Content-Encoding' : 'gzip' if gzip_body else 'text/plain',
      'Referer'          : 'http://{host}/codejam/contest/dashboard?c={contest_id}'.format(host = self.host, contest_id = self.contest_id),
      'User-Agent'       : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4',
      'Cookie'           : self.cookie
    }

    # Assemble the multipart data using the specified values.
    multipart_data.add_string('csrfmiddlewaretoken', self.middleware_token)
    multipart_data.add_file('answer', output_name)
    for i, source in enumerate(source_names):
      multipart_data.add_file('source-file{0}'.format(i), source)
      multipart_data.add_string('source-file-name{0}'.format(i), source)
    multipart_data.add_string('cmd', 'SubmitAnswer')
    multipart_data.add_string('contest', self.contest_id)
    multipart_data.add_string('problem', self.problem_id)
    multipart_data.add_string('input_id', input_id)
    multipart_data.add_string('num_source_files', str(len(source_names)))

    try:
      # Print message and check that at least one source file was included.
      if source_names:
        sys.stdout.write('Sending output file "{0}" and source(s) {1} to "{2}"...\n'.format(
          output_name, ', '.join('"{0}"'.format(source) for source in source_names), self.host))
      else:
        # Print warning saying that no source file, this might cause disqualification
        # in a real contest.
        sys.stdout.write('Warning, no source files are being sent for output file "{0}"!\n'.format(output_name))
        sys.stdout.write('Sending output file "{0}" to "{1}"...\n'.format(output_name, self.host))

      # Get the message body and check if compression was requested.
      body = str(multipart_data)
      if gzip_body:
        # Compress the body using gzip and show sizes.
        compressed_body = ZipUtils.zip_data(body)
        sys.stdout.write('Sending {0} bytes to server ({1} uncompressed)...\n'.format(
          len(compressed_body), len(body)))
        body = compressed_body
      else:
        # Just log the message with the size, as no compression was requested.
        sys.stdout.write('Sending {0} bytes to server...\n'.format(len(body)))

      # Send the multipart data to the server using POST.
      http_connection = httplib.HTTPConnection(self.host)
      http_connection.request('POST', '/codejam/contest/dashboard/do', body, request_headers)

      # Get the result and show the status and the number of bytes read.
      http_response = http_connection.getresponse()
      bytes_read = int(http_response.getheader('content-length', '0'))
      sys.stdout.write('{0} {1}, {2} bytes read from server.\n'.format(
        http_response.status, http_response.reason, bytes_read))

      # Check if the server sent a response or ignored the request.
      if bytes_read > 0:
        # Get the response data, parse the submit result and print it.
        response_data = ZipUtils.unzip_data(http_response.read())
        submit_result = self._parse_result(response_data)
        sys.stdout.write('{0}\n'.format(submit_result))
      else:
        # No response from the server, output warning.
        sys.stdout.write('No response received from the server, this happens if '
          'you try to submit the large output before solving the small input.\n')

      # Close the connection with the server.
      http_connection.close()
    except httplib.HTTPException as error:
      # Log the http exception and exit with errors.
      sys.stderr.write('HTTP Exception while submitting output: {0}\n'.format(str(error)))
      sys.exit(1)

    # Erase all temporary files generated during the source preparation.
    for tmp_file in tmp_files:
      try:
        # Remove the temporary zipped file.
        os.remove(tmp_file)
      except OSError as error:
        # Log the OS error and exit with error.
        sys.stderr.write('OS error happened while removing temporary '
          'file at "{0}": {1}'.format(tmp_file, str(error)))
        sys.exit(1)

# Factory method to create an output submitter object.
def create(host, cookie, middleware_token, contest_id, problem_id):
  return _OutputSubmitter(host, cookie, middleware_token, contest_id, problem_id)
