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
import sys

# Read the persistent data from the specified file, which 
# should be formatted as a python dict.
def read_data(filename):
  try:
    # Open the specified file and get its contents.
    file = open(filename, 'rt')
    file_data = file.read()
    file.close()

    # Evaluate the file data directly, as it is formatted as a python dict.
    return eval(file_data, {}, {})
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while reading data '
      'from file "{0}" : {1}'.format(filename, str(error)))
    sys.exit(1)

# Write the specified data to the specified file, which will
# be formatted as a python dict.
def write_data(data, filename):
  try:
    # Calculate the space needed for the keys and create a format string
    # for each data item.
    key_width = max(len(repr(key)) for key in data.iterkeys())
    item_format = '{0:' + str(key_width) + '} : {1},'

    # Open the file and store each item inside it.
    file = open(filename, 'wt')
    file.write('{\n');
    for key, value in sorted(data.iteritems()):
      item_line = item_format.format(repr(key), repr(value))
      file.write('{0}\n'.format(item_line))
    file.write('}\n');
    file.close()
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while writing data file '
      'from "{0}" : {1}'.format(filename, str(error)))
    sys.exit(1)
