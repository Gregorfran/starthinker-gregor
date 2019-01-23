###########################################################################
#
#  Copyright 2018 Google Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

"""Command line to schedule recipe execution.

This script is meant to run persistently ( in a screen session ).  Once an hour, 
it will read a directory and check each *.json recipe for a schedule.  If the
recipe has a task to run during the current time zone adjusted hour, it is executed.

To add a schedule to any recipe include the following JSON.

  {
    "setup": {
      "timezone": "America/Los_Angeles",
      "day": [ "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" ],
      "hour": [ "3", "18" ]
    }
  }

To execute each task at a different hour add the following JSON to each task.  Each hour
must match at least one in the the setup section.  Tasks with no hours specified execute
every hour in setup section.

  {
    "tasks": [
      "sample_task": {
        "hour":[3]
       }
    ]
  }

To start a scheduled cron from the command line: 

python cron/run.py [path to recipe directory] [see optional arguments below]

To execute all recipes in a directory once run:

python cron/run.py [path to recipe directory] [see optional arguments below] --force

Arguments

  path - run all json files in the specified path
  --project / -p - cloud id of project
  --user / -u - path to user credentials json file, defaults to GOOGLE_APPLICATION_CREDENTIALS
  --service / -s - path to service credentials json file
  --client / -c' - path to client credentials json file
  --verbose / -v - print all the steps as they happen.
  --force / -f - execute all scripts once then exit.
  --remote / -r - execute scripts remotely, requires pub/sub ( not set up yet )

Each recipe can run under different credentials, specify project, client, user, and service 
values in the JSON for each recipe. See /util/project/README.md.

CAUTION

This script triggers the all/run.py script if the schedule matches the current hour.
This script does NOT check if the last job finished, potentially causing overruns.

"""

import sys
import subprocess
import argparse

from glob import glob
from time import sleep

from starthinker.setup import EXECUTE_PATH
from starthinker.util.project import get_project, is_scheduled

ONE_HOUR_AND_ONE_SECOND = (60 * 60) + 1 # ensures no repeat in a single hour but never runs over in 24 hours

if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('path', help='run all json files in the specified path', action="store")

  parser.add_argument('--project', '-p', help='cloud id of project, defaults to None', default=None)
  parser.add_argument('--user', '-u', help='path to user credentials json file, defaults to GOOGLE_APPLICATION_CREDENTIALS', default=None)
  parser.add_argument('--service', '-s', help='path to service credentials json file, defaults None', default=None)
  parser.add_argument('--client', '-c', help='path to client credentials json file, defaults None', default=None)

  parser.add_argument('--verbose', '-v', help='print all the steps as they happen.', action='store_true')
  parser.add_argument('--force', '-f', help='execute all scripts once then exit.', action='store_true')
  #parser.add_argument('--remote', '-r', help='execute the scripts remotely, equires pub/sub setup.', action='store_true')

  args = parser.parse_args()

  try:

    while True:
      for filepath in glob('%s*.json' % args.path):
        if args.verbose: print 'PROJECT:', filepath

        project = get_project(filepath)

        if args.force or is_scheduled(project):

          command = 'python %s/run.py %s %s' % (script, filepath, ' '.join(sys.argv[2:]))

          if args.verbose: print 'COMMAND:', command

          subprocess.Popen(command, shell=True, cwd=EXECUTE_PATH)

      if args.force: break
      if args.verbose: print 'SLEEP:', ONE_HOUR_AND_ONE_SECOND
      sleep(ONE_HOUR_AND_ONE_SECOND)

  except KeyboardInterrupt:
    exit()
