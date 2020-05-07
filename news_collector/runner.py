#used to debug from vs code.
#otherwise just use 'scrapy crawl news' from commandline

import os
from scrapy.cmdline import execute
import subprocess

os.chdir(os.path.dirname(os.path.realpath(__file__)))

try:
    output_filename = "out.json"
    subprocess.check_call(['rm', output_filename])
    #execute(["rm", output_filename] )
    execute(
        [
            'scrapy',
            'crawl',
            'spiegel',
            "-t", "json",
            '-o',
            output_filename,
            '--logfile',
            'spiegel.log',
            '--loglevel',
            'WARNING'
        ]
    )
except SystemExit:
    pass