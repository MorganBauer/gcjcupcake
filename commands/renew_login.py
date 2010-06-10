#!/usr/bin/python2
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
import os, sys
from optparse import OptionParser
from gcj_cupcake import Constants as gcj_Constants
from gcj_cupcake import CodeJamLogin as gcj_CodeJamLogin

def main():
  # Create an option parser and use it to parse the supplied arguments.
  program_version = 'GCJ login agent by jbernadas, {0}'.format(gcj_Constants.VERSION)
  parser = OptionParser(usage = '%prog [options]', version = program_version)
  parser.add_option('-p', '--passwd', action = 'store', dest = 'password',
    help = 'Password used to login in the server, will be asked if not specified')
  options, args = parser.parse_args()

  # Check that the number of arguments is valid.
  if len(args) != 0:
    parser.print_usage()
    print '{0}: error: need no positional arguments'.format(os.path.basename(sys.argv[0]))
    sys.exit(1)

  # Login into the codejam servers.
  gcj_CodeJamLogin.login(options.password)

if __name__ == '__main__':
  main()
