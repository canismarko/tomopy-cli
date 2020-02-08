#!/usr/bin/env python
# coding=utf-8
"""
This experiment showcases the concept of commands in Sacred.
By just using the ``@ex.command`` decorator we can add additional commands to
the command-line interface of the experiment::

  $ ./05_my_commands.py greet
  WARNING - my_commands - No observers have been added to this run
  INFO - my_commands - Running command 'greet'
  INFO - my_commands - Started
  Hello John! Nice to greet you!
  INFO - my_commands - Completed after 0:00:00

::

  $ ./05_my_commands.py shout
  WARNING - my_commands - No observers have been added to this run
  INFO - my_commands - Running command 'shout'
  INFO - my_commands - Started
  WHAZZZUUUUUUUUUUP!!!????
  INFO - my_commands - Completed after 0:00:00

Of course we can also use ``with`` and other flags with those commands::

  $ ./05_my_commands.py greet with name='Jane' -l WARNING
  WARNING - my_commands - No observers have been added to this run
  Hello Jane! Nice to greet you!

In fact, the main function is also just a command::

  $ ./05_my_commands.py main
  WARNING - my_commands - No observers have been added to this run
  INFO - my_commands - Running command 'main'
  INFO - my_commands - Started
  This is just the main command. Try greet or shout.
  INFO - my_commands - Completed after 0:00:00

Commands also appear in the help text, and you can get additional information
about all commands using ``./05_my_commands.py help [command]``.
"""
import os
import re
import sys
import argparse
import logging
import time
import pathlib
from datetime import datetime

from tomopy_cli import config, __version__
from tomopy_cli import log
from tomopy_cli import recon
from tomopy_cli import find_center
from tomopy_cli import file_io
from tomopy_cli import post

from sacred import Experiment

ex = Experiment("tomopy-cli")


@ex.config
def cfg():

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', **config.SECTIONS['general']['config'])
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))

    tomo_params = config.RECON_PARAMS
    find_center_params = config.RECON_PARAMS
    convert_params = config.CONVERT_PARAMS

    cmd_parsers = [
        ('init',        init,            (),                             "Create configuration file"),
        ('rec',         rec,            tomo_params,                    "Run tomographic reconstruction"),
        ('status',      status,         tomo_params,                    "Show the tomographic reconstruction status"),
        ('segment',     segment,        tomo_params,                    "Run segmentation on reconstured data"),
        ('find_center', find_center,    find_center_params,             "Find rotation axis location for all hdf files in a directory"),
        ('convert',     convert,        convert_params,                 "Convert pre-2015 (proj, dark, white) hdf files in a single data exchange h5 file"),
    ]

    subparsers = parser.add_subparsers(title="Commands", metavar='')

    for cmd, func, sections, text in cmd_parsers:
        cmd_params = config.Params(sections=sections)
        cmd_parser = subparsers.add_parser(cmd, help=text, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cmd_parser = cmd_params.add_arguments(cmd_parser)
        cmd_parser.set_defaults(_func=func)

    args = config.parse_known_args(parser, subparser=True)


@ex.command
def init(args):

    if not os.path.exists(str(args.config)):
        config.write(args.config)
    else:
        log.error("{0} already exists".format(args.config))


@ex.command
def status(args):

    config.log_values(args)


@ex.command
def find_center(args):

    if (str(args.file_format) in {'dx', 'aps2bm', 'aps7bm', 'aps32id'}):
        log.warning('find center start')
        find_center.find_rotation_axis(args)
        log.warning('find center end')

        # update tomopy.conf
        sections = config.RECON_PARAMS
        config.write(args.config, args=args, sections=sections)
    else:
        log.error("  *** %s is not a supported file format" % args.file_format)
        exit()


@ex.command
def segment(args):

    log.warning('segmentation start')
    post.segment(args)
    log.warning('segmentation end')

    # update tomopy.conf
    sections = config.RECON_PARAMS
    config.write(args.config, args=args, sections=sections)


@ex.command
def convert(args):

    log.warning('convert start')
    file_io.convert(args)
    log.warning('convert end')

    
@ex.command
def rec(args):

    log.warning('reconstruction start')

    if (str(args.file_format) in {'dx', 'aps2bm', 'aps7bm', 'aps32id'}):
        if os.path.isfile(args.file_name):    
            log.info("reconstructing a single file: %s" % args.file_name)   
            recon.rec(args)
            config.update_config(args)
        elif os.path.isdir(args.file_name):
            # Add a trailing slash if missing
            top = os.path.join(args.file_name, '')

            h5_file_list = list(filter(lambda x: x.endswith(('.h5', '.hdf')), os.listdir(top)))
            if (h5_file_list):
                h5_file_list.sort()
                log.info("found: %s" % h5_file_list) 
                # look for pre-calculated rotation axis positions.
                jfname = top + args.rotation_axis_file
                if(os.path.exists(jfname)):
                    log.warning("  *** try to use pre-calculated rotation centers from %s file" % jfname)   
                    dictionary = file_io.read_rot_centers(args)
                    # log.warning("reconstructing a folder containing %d files" % len(dictionary))   
                    index = 0
                    for key in dictionary:
                        dict2 = dictionary[key]
                        for h5fname in dict2:
                            args.rotation_axis = dict2[h5fname]
                            fname = top + h5fname
                            args.file_name = fname
                            log.warning("  *** file %d/%d; ord(%s);  %s center: %f" % (index, len(dictionary)-1, key, args.file_name, args.rotation_axis))
                            index += 1
                            recon.rec(args)
                            config.update_config(args)
                    log.warning('reconstruction end')
                else:
                    log.warning("  *** no pre-calculated rotation centers from %s file" % jfname)   
                    index=0
                    for fname in h5_file_list:
                        args.file_name = top + fname
                        log.warning("  *** file %d/%d;  %s" % (index, len(h5_file_list), fname))
                        index += 1
                        recon.rec(args)
                        config.update_config(args)
                    log.warning('reconstruction end')
            else:
                log.error("directory %s does not contain any file" % args.file_name)
        else:
            log.error("directory or File Name does not exist: %s" % args.file_name)
    else:
        # add here support for other file formats
        log.error("  *** %s is not a supported file format" % args.file_format)
        log.error("supported data formats are: %s, %s, %s, %s" % ('dx', 'aps2bm', 'aps7bm', 'aps32id'))


@ex.automain
def main():
    print("This is just the main command. Try greet or shout.")
