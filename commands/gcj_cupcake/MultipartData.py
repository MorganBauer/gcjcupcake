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
import mimetypes, sys

# Class to manage multipart data in HTTP requests.
# Create using the factory method at the end.
class _MultipartData:
  # Initialize a multipart data with the speciifed boundary.
  def __init__(self, boundary):
    self.data = []
    self.boundary = boundary

  # Convert this multipart data to a readable string.
  def __str__(self):
    return "\r\n".join(self.data + ['--' + self.boundary + '--', ''])

  # Guess the content type of a file given its name.
  def _get_content_type(self, filename):
    guessed_type = mimetypes.guess_type(filename)[0]
    return guessed_type if guessed_type != None else 'application/octet-stream'

  # Add a file's contents to this multipart data.
  def add_file(self, name, filename):
    try:
      # Read the data from the specified file.
      file = open(filename, 'rb')
      file_data = file.read()
      file.close()

      # Append the metadata and then the read file data. Finally, complete with a
      # closing boundary.
      self.data.append('--' + self.boundary)
      self.data.append('Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(name, filename))
      self.data.append('Content-Type: {0}'.format(self._get_content_type(filename)))
      self.data.append('')
      self.data.append(file_data)
    except IOError as error:
      # Log the IO error and exit with error.
      sys.stderr.write('IO error happened while reading '
        'file "{0}": {1}'.format(filename, str(error)))
      sys.exit(1)

  # Add a string value to this multipart data.
  def add_string(self, name, value):
    # Append the field metadata and then the value. Finally, complete with a
    # closing boundary.
    self.data.append('--' + self.boundary);
    self.data.append('Content-Disposition: form-data; name="{0}"'.format(name))
    self.data.append('')
    self.data.append(value)

# Factory method to create a multipart data object.
def create(boundary):
  return _MultipartData(boundary)
