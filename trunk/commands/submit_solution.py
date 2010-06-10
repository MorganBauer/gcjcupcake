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
from gcj_cupcake import OutputSubmitter as gcj_OutputSubmitter

def main():
  # Create an option parser and use it to parse the supplied arguments.
  program_version = 'GCJ solution submitter by jbernadas, {0}'.format(gcj_Constants.VERSION)
  parser = OptionParser(usage = '%prog [options] problem input id', version = program_version)
  parser.add_option('-l', '--login', action = 'store_true', dest = 'renew_login',
    help = 'Ignore the stored cookie and login again into the server')
  parser.add_option('-p', '--passwd', action = 'store', dest = 'password',
    help = 'Password used to login in the server, will be asked if not specified')
  parser.add_option('-d', '--data-directory', action = 'store', dest = 'data_directory',
    help = 'Directory with the I/O files and main source files [default: ./source]')
  parser.add_option('-o', '--output-name', action = 'store', dest = 'output_name',
    help = 'Name of the file with the solution\'s output')
  parser.add_option('-s', '--source-name', action = 'store', dest = 'source_name',
    help = 'Name of the file with the solution\'s main source code')
  parser.add_option('-a', '--add-source', action = 'append', dest = 'extra_sources',
    help = 'Add EXTRA_SOURCE to the submitted source files', metavar = 'EXTRA_SOURCE')
  parser.add_option('-z', '--zip-sources', action = 'store_true', dest = 'zip_sources',
    help = 'Put the source files into a zip file before submitting')
  parser.add_option('--ignore-zip', action = 'store_true', dest = 'ignore_zip',
    help = 'Ignore source zip files not specified directly using the -s option')
  parser.add_option('--ignore-default-source', action = 'store_true', dest = 'ignore_def_source',
    help = 'Ignore source zip files not specified directly using the -s option')
  parser.add_option('--gzip-content', action = 'store_true', dest = 'gzip_content',
    help = 'Send the output and sources using gzip encoding (faster)')
  parser.add_option('--plain-content', action = 'store_false', dest = 'gzip_content',
    help = 'Send the output and sources using plain encoding (slower)')
  parser.set_defaults(renew_login = False, gzip_content = True, zip_sources = False,
                      ignore_zip = False, ignore_def_source = False)
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
    # Get the get submit middleware token used to send the files.
    submit_output_token = middleware_tokens['SubmitAnswer']
  except KeyError as error:
    # Print error message and exit with error code.
    print 'Cannot find "SubmitAnswer" token in configuration file: {0}'.format(str(error))
    sys.exit(1)

  # Calculate the problem index and check if it is inside the range.
  problem_index = ord(problem_letter) - ord('A')
  if problem_index < 0 or problem_index >= len(problem_ids):
    # Print error message and exit with error code.
    print 'Cannot find problem {0}, there are only {1} problem(s).'.format(
      problem_letter, len(problem_ids))
    sys.exit(1)

  # Get the problem id, its name and the input id from the maps.
  problem_id = problem_ids[problem_index]
  problem_name = problem_names[problem_index]
  input_id = input_ids[input_type]

  # Get the data directory from the options, if not defined, get it from the
  # configuration, using './source' as the default value if not found. In the
  # same way, get the output filename format and the main source code filename
  # format.
  data_directory = options.data_directory or current_config.get('data_directory', './source')
  output_name_format = options.output_name or current_config.get('output_name_format', '{problem}-{input}-{id}.out')
  source_name_format = options.source_name or current_config.get('source_name_format')

  # There is no sensible default for the main source, so exit with error if no
  # value is found and it wasn't ignored.
  if not options.ignore_def_source and not source_name_format:
    # Print error message and exit.
    print 'No format found for the default source file name. Either pass it using ' \
      '--source-name, specify "source_name_format" in the configuration file or ' \
      'ignore it passing --ignore-default-source.'
    sys.exit(1)

  try:
    # Generate the output file name using the specified format and then return.
    output_basename = output_name_format.format(
      problem = problem_letter, input = input_type, id = id)
    output_filename = os.path.normpath(os.path.join(data_directory, output_basename))
  except KeyError as error:
    # Print error message and exit.
    print 'Invalid output name format "{0}", {1} is an invalid key, only use ' \
      '"problem", "input" and "id".'.format(input_name_format, str(error))
    sys.exit(1)

  # Create the list with all the source files and add the default source file
  # if it was requested.
  source_names = []
  if not options.ignore_def_source:
    try:
      # Generate the source file name using the specified format and append it
      # to the source list.
      def_source_basename = source_name_format.format(
        problem = problem_letter, input = input_type, id = id)
      def_source_filename = os.path.normpath(os.path.join(data_directory, def_source_basename))
      source_names.append(def_source_filename)
    except KeyError as error:
      # Print error message and exit.
      print 'Invalid output name format "{0}", {1} is an invalid key, only use ' \
        '"problem", "input" and "id".'.format(input_name_format, str(error))
      sys.exit(1)

  # Append any extra source file to the source list, normalizing their paths
  # for the current operative system.
  if options.extra_sources:
    source_names.extend([os.path.normpath(source) for source in options.extra_sources])

  # Print message indicating that an output is going to be submitted.
  print '-' * 79
  print '{0} output for "{1} - {2}" at "{3}"'.format(
    string.capitalize(input_type), problem_letter, problem_name, output_filename)
  print '-' * 79

  # Renew the cookie if the user requested a new login.
  if options.renew_login:
    cookie = gcj_CodeJamLogin.login(options.password)

  # Create the output submitter and send the files.
  output_submitter = gcj_OutputSubmitter.create(
    host, cookie, submit_output_token, contest_id, problem_id)
  output_submitter.submit(input_id, output_filename, source_names,
    gzip_body = options.gzip_content, zip_sources = options.zip_sources,
    add_ignored_zips = not options.ignore_zip)

if __name__ == '__main__':
  main()
