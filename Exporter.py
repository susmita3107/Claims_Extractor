# -*- coding: utf-8 -*-
import getopt
import sys

sys.path.append('claim_extractor')

from claim_extractor import claimextractor as ce
from claim_extractor import Configuration




def main(argv):
    """
    The main function that handles command-line arguments and initiates the claim extraction process.

    :param argv: A list of command-line arguments provided by the user.
    :type argv: List[str]
    """
    options = {}
    criteria = Configuration()
    criteria.setOutput("output_got.csv")    
    criteria.setOutputDev("output_dev.csv")
    criteria.setOutputDev("output_sample.csv")

    if len(argv) == 0:
        print('You must pass some parameters. Use \"-h\" to help.')
        return

    if len(argv) == 1 and argv[0] == '-h':
        f = open('exporter_help_text.txt', 'r')
        print(f.read())
        f.close()
        return

    try:
        opts, args = getopt.getopt(argv, "", ("website=", "maxclaims=", "annotation-api="))

        for opt, arg in opts:
            if opt == '--website':
                criteria.website = arg
            if opt == '--maxclaims':
                criteria.maxClaims = int(arg)
                if criteria.website != "":
                    criteria.setOutputDev("samples/output_dev_" + criteria.website + ".csv")
                    criteria.setOutputSample("samples/output_sample_" + criteria.website + ".csv")
            if opt == '--annotation-api':
                criteria.annotator_uri = arg

    except:
        print('Arguments parser error, try -h')
        exit()

    ce.get_claims(criteria)
    #print(criteria.output)
    print(('Done. Output file generated "%s".' % criteria.output))


if __name__ == '__main__':
    main(sys.argv[1:])
