#!/usr/bin/env python3

import os
import sys
import argparse

from dtrackauditor.auditor import Auditor

DTRACK_SERVER = os.environ.get('DTRACK_SERVER')
DTRACK_API_KEY = os.environ.get('DTRACK_API_KEY')

DEFAULT_VERSION = '1.0.0'
DEFAULT_FILENAME = '../bom.xml'
DEFAULT_SHOWDETAILS = 'FALSE'

DEFAULT_TRIGGER = 1

def parse_cmd_args():
    parser = argparse.ArgumentParser(description='Dtrackauditor script for manual or in CI use',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-u', '--url', type=str,
                        help=' * url of dependencytrack host. eg. http://dtrack.abc.local:8080. OR set env $DTRACK_SERVER')
    parser.add_argument('-k', '--apikey', type=str,
                        help=' * api key of dependencytrack host. eg. adfadfe343g. OR set env $DTRACK_API_KEY')
    parser.add_argument('-p', '--project', type=str,
                        help=' * project name to be used in dependencytrack.eg: mywebapp. *')
    parser.add_argument('-v', '--version', type=str,
                        help=' * version of project in dependencytrack. eg. 1.0.0. *')
    parser.add_argument('-f', '--filename', type=str,
                        help='file path of sbom. eg. target/bom.xml, mybom.xml')
    parser.add_argument('-r', '--rules', type=str,
                        help='rules to evaluate')
    parser.add_argument('-a', '--auto', action="store_true",
                        help='auto creates project with version if not found in the dtrack server.'
                             ' sync and fail the job if any mentioned issues are found to be higher than default or set'
                             'count value.'),
    parser.add_argument('-l', '--showdetails', type=str,
                        help='displays vulnerabilities details in the stdout based on severity selected. Use with Auto mode.'
                             ' eg values: true or false or all. Default is False.')
    parser.add_argument('-w', '--wait', action="store_true",
                        help='wait for uploaded bom to be processed on dependencytrack host.')
    parser.add_argument('-c', '--getversion', nargs='?', const=1, type=int, help='get version of dependencytrack host. Useful to do a quick '
                                                            'connection test.')
    args = parser.parse_args()

    if args.url is None:
        args.url = DTRACK_SERVER
    if not isinstance(args.url, str) or len(args.url) == 0:
        print('DependencyTrack server URL is required. Set env $DTRACK_SERVER or use --url.eg: http://dtrack.my.local')
        sys.exit(1)
    if args.apikey is None:
        args.apikey = DTRACK_API_KEY
    if not isinstance(args.apikey, str) or len(args.apikey) == 0:
        print('DependencyTrack api key is required. Set Env $DTRACK_API_KEY or use --apikey.')
        sys.exit(1)
    if args.rules is None:
        args.rules = []
    else:
        args.rules = list(map(lambda r: r.strip(), args.rules.split(',')))
    if args.version is None:
        args.version = DEFAULT_VERSION
    if args.filename is None:
        args.filename = DEFAULT_FILENAME
    if args.showdetails is None:
        args.showdetails = DEFAULT_SHOWDETAILS
    return args

def main():
    args = parse_cmd_args()
    dt_server = args.url.strip()
    if dt_server[-1] == '/':
        dt_server = dt_server[:-1]
    dt_api_key = args.apikey.strip()
    filename = args.filename.strip()
    show_details = args.showdetails.strip().upper()

    if args.getversion:
        Auditor.get_dependencytrack_version(dt_server, dt_api_key)
        sys.exit(0)

    if show_details not in ['TRUE', 'FALSE', 'ALL']:
        print('Issue with an option --showdetails. Please check the accepted values.')
        sys.exit(1)
    if args.project is None or \
       len(args.project) == 0 or \
       args.version is None or \
       len(args.version) == 0:
        print('Project Name (-p) and Version (-v) are required. Check help --help.')
        sys.exit(1)

    project_name = args.project.strip()
    version = args.version.strip()

    print('Provided project name and version: ', project_name, version)
    if args.auto:
        print('Auto mode ON')
        Auditor.read_upload_bom(dt_server, dt_api_key, project_name, version, filename, True, wait=args.wait)
        project_uuid = Auditor.get_project_with_version_id(dt_server, dt_api_key, project_name, version)
        if project_uuid:
            Auditor.check_policy_violations(dt_server, dt_api_key, project_uuid)
            Auditor.check_vulnerabilities(dt_server, dt_api_key, project_uuid, args.rules, show_details)
    else:
        Auditor.read_upload_bom(dt_server, dt_api_key, project_name, version, filename, False, wait=args.wait)

if __name__ == '__main__':
   main()
