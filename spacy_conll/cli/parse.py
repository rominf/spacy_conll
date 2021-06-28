import os
from argparse import Namespace
from locale import getpreferredencoding
from pathlib import Path
from sys import stdout
from tempfile import NamedTemporaryFile

from spacy_conll import init_parser
from spacy_conll.parser import ConllParser


def parse(args: Namespace):
    if not args.input_str and not args.input_file:
        raise ValueError("'input_str' or 'input_file' must be given")
    elif args.input_file:
        input_f = args.input_file
        delete_inp = False
    else:
        input_fh = NamedTemporaryFile(encoding=args.input_encoding, mode="w", delete=False)
        input_f = input_fh.name
        input_fh.write(args.input_str+"\n")
        input_fh.close()
        delete_inp = True

    nlp = init_parser(args.model_or_lang,
                      args.parser,
                      is_tokenized=args.is_tokenized,
                      disable_sbd=args.disable_sbd)

    parser = ConllParser(nlp, is_tokenized=args.is_tokenized)
    conll_str = parser.parse_as_conll(input_f,
                                      args.input_encoding,
                                      args.n_process,
                                      args.include_headers,
                                      args.no_force_counting)

    fhout = Path(args.output_file).open("w", encoding=args.output_encoding) if args.output_file is not None else stdout
    fhout.write(conll_str)

    if fhout is not stdout and args.verbose:
        # end='' to avoid adding yet another newline
        print(conll_str, end="")

    # Clean-up
    if delete_inp:
        os.unlink(input_f)


def main():
    import argparse
    cparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Parse an input string or input file to CoNLL-U format using a spaCy-wrapped parser.",
    )

    # Input arguments
    cparser.add_argument(
        "-f",
        "--input_file",
        default=None,
        help="Path to file with sentences to parse. Has precedence over 'input_str'.",
    )
    cparser.add_argument(
        "-a",
        "--input_encoding",
        default=getpreferredencoding(),
        help="Encoding of the input file. Default value is system default.",
    )
    cparser.add_argument("-b", "--input_str", default=None, help="Input string to parse.")

    # Output arguments
    cparser.add_argument(
        "-o",
        "--output_file",
        default=None,
        help="Path to output file. If not specified, the output will be printed on standard output.",
    )
    cparser.add_argument(
        "-c",
        "--output_encoding",
        default=getpreferredencoding(),
        help="Encoding of the output file. Default value is system default.",
    )

    # Model/pipeline arguments
    cparser.add_argument(
        "model_or_lang",
        help="Model or language to use. SpaCy models must be pre-installed, stanza and udpipe models will be"
             " downloaded automatically",
    )
    cparser.add_argument(
        "parser",
        choices=["spacy", "stanza", "udpipe"],
        help="Which parser to use. Parsers other than 'spacy' need to be installed separately."
        " For 'stanza' you need 'spacy-stanza', and for 'udpipe' the 'spacy-udpipe' library is"
        " required.",
    )
    cparser.add_argument(
        "-s",
        "--disable_sbd",
        default=False,
        action="store_true",
        help="Whether to disable spaCy automatic sentence boundary detection. In practice, disabling means that"
        " every line will be parsed as one sentence, regardless of its actual content. When 'is_tokenized' is enabled,"
        " 'disable_sbd' is enabled automatically (see 'is_tokenized')."
        " Only works when using 'spacy' as 'parser'.",
    )
    cparser.add_argument(
        "-t",
        "--is_tokenized",
        default=False,
        action="store_true",
        help="Whether your text has already been tokenized (space-seperated). Setting this"
        " option has as an important consequence that no sentence splitting at all will be done except splitting"
        " on new lines. So if your input is a file, and you want to use pretokenised text, make sure that each line"
        " contains exactly one sentence.",
    )

    # Additional arguments
    cparser.add_argument(
        "-d",
        "--include_headers",
        default=False,
        action="store_true",
        help="Whether to  include headers before the output of every sentence. These headers include the"
        " sentence text and the sentence ID as per the CoNLL format.",
    )
    cparser.add_argument(
        "-e",
        "--no_force_counting",
        default=False,
        action="store_true",
        help="Whether to  disable force counting the 'sent_id', starting from 1 and increasing for each"
        " sentence. Instead, 'sent_id' will depend on how spaCy returns the sentences."
        " Must have 'include_headers' enabled.",
    )
    cparser.add_argument(
        "-j",
        "--n_process",
        type=int,
        default=1,
        help="Number of processes to use in nlp.pipe(). -1 will use as many cores as available. Might not work for a"
             " 'parser' other than 'spacy'.",
    )
    cparser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="Whether to always print the output to stdout, regardless of 'output_file'.",
    )

    cargs = cparser.parse_args()
    parse(cargs)


if __name__ == "__main__":
    main()
