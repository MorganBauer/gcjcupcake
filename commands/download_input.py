#!/usr/bin/python2
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
import re, os, string, sys
from optparse import OptionParser
from gcj_cupcake import Constants as gcj_Constants
from gcj_cupcake import DataManager as gcj_DataManager
from gcj_cupcake import CodeJamLogin as gcj_CodeJamLogin
from gcj_cupcake import InputDownloader as gcj_InputDownloader

def main():
  # Create an option parser and use it to parse the supplied arguments.
  program_version = 'GCJ input downloader by jbernadas, {0}'.format(gcj_Constants.VERSION)
  parser = OptionParser(usage = '%prog [options] problem input id', version = program_version)
  parser.add_option('-l', '--login', action = 'store_true', dest = 'renew_cookie',
    help = 'Ignore the stored cookie and login again into the server')
  parser.add_option('-p', '--passwd', action = 'store', dest = 'password',
    help = 'Password used to login in the server, will be asked if not specified')
  parser.add_option('-d', '--data-directory', action = 'store', dest = 'data_directory',
    help = 'Directory with the I/O files and main source files')
  parser.add_option('-i', '--input-name', action = 'store', dest = 'input_name',
    help = 'Name of the file where the input should be written')
  parser.set_defaults(renew_cookie = False)
  options, args = parser.parse_args()

  # Check that the number of arguments is valid.
  if len(args) != 3:
    parser.print_usage()
    print '{0}: error: need 3 positional arguments'.format(os.path.basename(sys.argv[0]))
    sys.exit(1)

  # Check that the problem idenfier is valid.
  problem_letter = args[0]
  if len(problem_letter) != 1 or not problem_letter.isupper():
    parser.print_usage()
    print '{0}: error: invalid problem {1}, must be one uppercase letter'.format(
      os.path.basename(sys.argv[0]), problem_letter)
    sys.exit(1)

  # Check that the input type is valid.
  input_ids = {'small' : '0', 'large' : '1'}
  input_type = args[1].lower()
  if input_type not in input_ids:
    parser.print_usage()
    print '{0}: error: invalid input type {1}, must be either "small" or "large"'.format(
      os.path.basename(sys.argv[0]), input_type)
    sys.exit(1)

  # Check that the submit id is a valid identifier.
  id = args[2]
  if not re.match('^\w+$', id):
    parser.print_usage()
    print '{0}: error: invalid id {1}, can only have numbers, letters and underscores'.format(
      os.path.basename(sys.argv[0]), id)
    sys.exit(1)

  try:
    # Read configuration information from the config file.  
    current_config = gcj_DataManager.read_data(gcj_Constants.CURRENT_CONFIG_FILE)
    host = current_config['host']
    user = current_config['user']
    middleware_tokens = current_config['middleware_tokens']
    cookie = current_config['cookie']
    contest_id = current_config['contest_id']
    problem_ids = current_config['problem_id']
    problem_names = current_config['problem_name']
  except KeyError as error:
    # Print error message and exit with error code.
    print 'Cannot find all required data in configuration file: {0}'.format(str(error))
    sys.exit(1)

  try:
    # Get the get input middleware token used to request the file.
    download_input_token = middleware_tokens['GetInputFile']
  except KeyError as error:
    # Print error message and exit with error code.
    print 'Cannot find "GetInputFile" token in configuration file: {0}'.format(str(error))
    sys.exit(1)

  # Calculate the problem index and check if it is inside the range.
  problem_index = ord(problem_letter) - ord('A')
  if problem_index < 0 or problem_index >= len(problem_ids):
    # Print error message and exit with error code.
    print '{0}: error: cannot find problem {1}, there are only {2} problem(s).'.format(
      os.path.basename(sys.argv[0]), problem_letter, len(problem_ids))
    sys.exit(1)

  # Get the problem id, its name and the input id from the maps.
  problem_id = problem_ids[problem_index]
  problem_name = problem_names[problem_index]
  input_id = input_ids[input_type]

  # Get the data directory from the options, if not defined, get it from the
  # configuration, using './source' as the default value if not found. In the
  # same way, get the input filename format.
  data_directory = options.data_directory or current_config.get('data_directory', './source')
  input_name_format = options.input_name or current_config.get('input_name_format', '{problem}-{input}-{id}.in')

  try:
    # Generate the input file name using the specified format and then return.
    input_basename = input_name_format.format(
      problem = problem_letter, input = input_type, id = id)
    input_filename = os.path.normpath(os.path.join(data_directory, input_basename))
  except KeyError as error:
    # Print error message and exit.
    print 'Invalid input name format "{0}", {1} is an invalid key, only use ' \
      '"problem", "input" and "id".'.format(input_name_format, str(error))
    sys.exit(1)

  # Print message indicating that an input is going to be downloaded.
  print '-' * 79
  print '{0} input for "{1} - {2}" at "{3}"'.format(
    string.capitalize(input_type), problem_letter, problem_name, input_filename)
  print '-' * 79

  # Renew the cookie if the user requested a new login.
  if options.renew_cookie:
    cookie = gcj_CodeJamLogin.login(options.password)

  # Create the input downloader and request the file.
  input_downloader = gcj_InputDownloader.create(
    host, cookie, download_input_token, contest_id, problem_id)
  input_downloader.download(input_id, input_filename)

if __name__ == '__main__':
  main()
