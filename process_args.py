import argparse
import datetime
import os

def process_args():
    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    parser = argparse.ArgumentParser(f'################# Start liftover on {dt} #################\n')
    valid_args = ['--input', '--output', '--output_path', '--chain_file']
    arg_info = {'--input': 'Input file in UCSC BED format (.bed), or plink file (.bim), or text file with one position per line.',
                '--output': 'Output file name without suffix',
                '--output_path': 'Path to output file. Default is the same as input file',
                '--chain_file': 'Appropriate chain file to use'}
    for arg in valid_args:
        if arg == '--output_path':
            parser.add_argument(arg, help=arg_info[arg], default='./')
        else:
            parser.add_argument(arg, help=arg_info[arg])
    args = parser.parse_args()

    # Sanity checks
    # Check input and chain file
    if not os.path.isfile(args.input):
        print(f'#Error: Input file does not exist: {args.input}\nExit')
        exit()
    if not os.path.isfile(args.chain_file):
        print(f'#Error: Chain file does not exist: {args.input}\nExit')
        exit()

    # Check output file path
    if not os.path.isdir(args.output_path):
        print('#Output directory does not exist. Making one')
        os.mkdir(args.output_path)
    print('\n# Arguments used:')
    for arg in valid_args:
        print('# - ', eval('args.arg'))
    arg.output = os.path.join(args.output_path, args.output) # Add path to output file name
    return args
