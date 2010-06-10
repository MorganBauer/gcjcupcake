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
import gzip, random, os, sys
from zipfile import ZipFile, ZIP_DEFLATED

# Unzip the specified data using a temporary file and the gzip library.
# After the data is unzipped, the temporary file is erased, so no special
# cleanup is necessary.
def unzip_data(zipped_data):
  try:
    # Write the zipped data into a temporary file (using a random name
    # to prevent collisions).
    zip_filename = 'tempZipFile_{0}.gz'.format(random.randrange(0, 2**31 - 1))
    zip_file = open(zip_filename, 'wb')
    zip_file.write(zipped_data)
    zip_file.close()
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while writing zipped '
      'data to "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

  try:
    # Open the file using gzip and get the unzipped contents.
    unzipped_file = gzip.open(zip_filename, 'rb')
    unzipped_data = unzipped_file.read()
    unzipped_file.close()
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while reading unzipped '
      'data from "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

  try:
    # Remove the temporary zipped file.
    os.remove(zip_filename)
  except OSError as error:
    # Log the OS error and exit with error.
    sys.stderr.write('OS error happened while removing zipped '
      'data at "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

  # Return the unzipped string.
  return unzipped_data

# Zip the specified data using a temporary file and the gzip library.
# After the data is zipped, the temporary file is erased, so no special
# cleanup is necessary.
def zip_data(unzipped_data):
  try:
    # Compress the data and write it to a temporary file (using a random name
    # to prevent collisions).
    zip_filename = 'tempZipFile_{0}.gz'.format(random.randrange(0, 2**31 - 1))
    compress_file = gzip.open(zip_filename, 'wb')
    compress_file.write(unzipped_data)
    compress_file.close()
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while compressing '
      'data into "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

  try:
    # Open the file normally and get the zipped contents.
    zipped_file = open(zip_filename, 'rb')
    zipped_data = zipped_file.read()
    zipped_file.close()
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while reading unzipped '
      'data from "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

  try:
    # Remove the temporary zipped file.
    os.remove(zip_filename)
  except OSError as error:
    # Log the OS error and exit with error.
    sys.stderr.write('OS error happened while removing zipped '
      'data at "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

  # Return the zipped string.
  return zipped_data

# Create a zip file with the specified source files.
def make_zip_file(source_files, zip_filename, ignore_exts = []):
  try:
    # Open the destination zip file and initialize the ignored files set.
    zip_file = ZipFile(zip_filename, 'w', ZIP_DEFLATED)
    ignored_files = set()

    # Put all specified sources in the zip file, ignoring files with the
    # specified extensions.
    for source_filename in source_files:
      # If the source is a directory, walk over it, adding each file inside it.
      if os.path.isdir(source_filename):
        # Walk over the specified directory.
        for dirpath, dirnames, filenames in os.walk(source_filename):
          # Create the directory inside the zip file and process all
          # files in the current directory.
          zip_file.write(dirpath)
          for filename in filenames:
            # Create the base filename and check if it extension is not in the
            # extenstions ignore list. Otherwise, add it to the ignored files set.
            base_filename = os.path.join(dirpath, filename)
            if os.path.splitext(filename)[1] not in ignore_exts:
              zip_file.write(base_filename)
            else:
              ignored_files.update([base_filename])
      else:
        # Add a file to the zip if and only if it extension is not in the ignore list.
        # Otherwise, add it to the ignored files set.
        if os.path.splitext(source_filename)[1] not in ignore_exts:
          zip_file.write(source_filename)
        else:
          ignored_files.update([source_filename])

    # Close the zip file and return the ignored files set.
    zip_file.close()
    return ignored_files
  except OSError as error:
    # Log the OS error and exit with error.
    sys.stderr.write('OS error happened while creating zip '
      'file "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)
  except IOError as error:
    # Log the IO error and exit with error.
    sys.stderr.write('IO error happened while creating zip '
      'file "{0}": {1}'.format(zip_filename, str(error)))
    sys.exit(1)

####################################################################################################