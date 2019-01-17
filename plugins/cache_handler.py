#!/usr/bin/python

import errno
import os
import sys
from urlparse import urlparse, ParseResult, parse_qs

_kTag = 'CACHE_H'


def make_dirs(path):
    # Helper to make dirs recursively
    # http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def normalize_parsed_url(parsed_url):
    path = parsed_url.path
    result = ParseResult(
        scheme=parsed_url.scheme,
        netloc=parsed_url.netloc,
        path=path.rstrip('/'),
        params='',
        query=parsed_url.query,
        fragment=parsed_url.fragment)
    return result


def split_path(path):
    split_path = path.split('/')
    dirname = None
    filename = None
    if len(split_path) > 1:
        last_fragment = split_path[-1]
        if '.' not in last_fragment:
            filename = ''
            dirname = path
        else:
            filename = last_fragment
            dirname = '/'.join(split_path[:-1])
    else:
        filename = ''
        dirname = path
    return (dirname, filename)


def get_hashed_filepath(stub, method, parsed_url, params={}):
    #  hash_template = '{method}:{stub}{param_str}'
    hash_template = '{stub}{param_str}'
    param_str = ''
    if not stub:
        stub = 'index.html'
    if params:
        param_str = '&'.join(['{}={}'.format(k, v) for k, v in params.items()])
    elif method == 'GET' and parsed_url.query:
        param_str = parsed_url.query
    if param_str:
        param_str = '?' + param_str
    return hash_template.format(method=method, stub=stub, param_str=param_str)


class ProxyHandler:

    #
    # `logger' stands for logging object instance, `params' will be
    # a dictonary of input paramerers for the script. Having passed to the
    # program a string like:
    #
    # $ ./proxy2 -p "plugins/my_plugin.py",argument1="test",argument2,argument3=test2
    #
    def __init__(self, logger, params, proxyOptions):
        self.logger = logger
        self.proxyOptions = proxyOptions
        self.cacheDir = proxyOptions['cachedir']
        logger.info('%s Initing cache proxy handler...' % _kTag)
        logger.info('%s \tcache dir: %s' % (_kTag, self.cacheDir))
        if len(params) > 1:
            logger.info('%s \tParams: %s' % str(params))
            if params['cachedir'] is not None:
                self.cacheDir = params['cachedir']
                logger.info('%s \tovewritten cache dir: %s' % (_kTag, self.cacheDir))

        if not os.path.isdir(self.cacheDir):
            make_dirs(self.cacheDir)

    def request_handler(self, req, req_body):
        pass

    def response_handler(self, req, req_body, res, res_body):
        try:
            self.logger.dbg('%s %s %s...' % (_kTag, req.command, req.path))

            parsed_url = normalize_parsed_url(urlparse(req.path))
            self.logger.dbg('%s %s' % (_kTag, parsed_url))

            cachepath = '{}{}'.format(parsed_url.netloc, parsed_url.path)
            dirpath, filepath_stub = split_path(cachepath)
            self.logger.info('%s dir: %s' % (_kTag, dirpath))
            self.logger.dbg('%s stub: %s' % (_kTag, filepath_stub))

            filepath = get_hashed_filepath(filepath_stub, req.command, parsed_url)
            self.logger.info('%s file: %s' % (_kTag, filepath))

            cache_file = os.path.join(self.cacheDir, dirpath, filepath)
            self.logger.dbg('%s cache: %s' % (_kTag, cache_file))

            # make dirs before you write to file
            dirname, _filename = split_path(cache_file)
            self.logger.dbg('%s making dirs %s...' % (_kTag, dirname))
            make_dirs(dirname)
            self.logger.dbg('%s %s %s %s' % (_kTag, res.status, res.reason, res_body[:60]))
            file_obj = open(cache_file, 'wb+')
            file_obj.writelines(res_body)
            file_obj.close()
        except:
            pass

        return res_body
