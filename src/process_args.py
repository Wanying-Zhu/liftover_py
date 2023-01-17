import argparse
import datetime
import os

def process_args():
    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    parser = argparse.ArgumentParser(f'\n################# Start liftover on {dt} #################\n')
    valid_args = ['--input', '--output', '--output_path', '--chain_file', '--liftover', '--chr_id_pos']
    arg_info = {'--input': 'Input file in UCSC BED format (.bed), or plink file (.bim), or text file with one position per line.',
                '--output': 'Output file name without suffix',
                '--output_path': 'Path to output file. Default is the same as input file',
                '--chain_file': 'Appropriate chain file to use',
                '--liftover': 'Path to liftover tool',
                '--chr_id_pos':'index of chromosome number, SNP id, position, separated by ":". for example: 1:3:5'}
    for arg in valid_args:
        if arg == '--output_path':
            parser.add_argument(arg, help=arg_info[arg], default='./')
        elif arg == '--liftover': # For WZ's use only
            parser.add_argument(arg, help=arg_info[arg], default='/data100t1/home/wanying/downloaded_tools/liftover/liftOver')
        elif arg == '--chain_file': # For WZ's use only, B37 to B38
            parser.add_argument(arg, help=arg_info[arg],
                                default='/data100t1/home/wanying/downloaded_tools/liftover/hg19ToHg38.over.chain.gz')
        else:
            parser.add_argument(arg, help=arg_info[arg])
    args = parser.parse_args()
    print('\n# Arguments used:')
    for arg in valid_args:
        print(f'# {arg}:', eval(f'args.{arg[2:]}'))

    # Sanity checks
    # Check input and chain file
    if not os.path.isfile(args.input):
        print(f'#Error: Input file does not exist: {args.input}\nExit')
        exit()
    if not os.path.isfile(args.chain_file):
        print(f'#Error: Chain file does not exist: {args.chain_file}\nExit')
        exit()

    # Check output file path
    if not os.path.isdir(args.output_path):
        print('#Output directory does not exist. Making one')
        os.mkdir(args.output_path)

    # args.output = os.path.join(args.output_path, args.output) # Add path to output file name
    return args
