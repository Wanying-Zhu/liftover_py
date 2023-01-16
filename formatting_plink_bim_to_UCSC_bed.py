# This code convert plink .bim file to UCSC BED file
# This is necessary for UCSC liftover program (convert between different genome assemblies)
# UCSC BED file has this format:
#       chrom     chromStart      chromEnd      SNP_id(Can be omitted)
#       chr3        12345           12346       rs1111(Can be omitted)

import pandas as pd
from process_args import process_args
import subprocess

def progress_bar(cur:int, total:int):
    '''
    Print progress bar
    '''
    percent = 100*cur/total
    progress = '=' * int(percent) + '>' + '-' * (99-int(percent))
    print(f'\r|{progress}| {percent:.2f}%', end='', flush=True)


def plink_bim_to_ucsc_bed(input_fn, output_fn):
    '''
    Convert plink .bim file to UCSC BED format
    '''
    # Get total number of lines of input file
    print('#Check number length of in put file')
    total = int(subprocess.run(f'wc -l {input_fn}'.split(), text=True).stdout.split()[0])
    print(f'# - input file has {total} entries')
    output_fh = open(output_fn, 'w')
    with open(input_fn, 'r') as input_fh:
        line = input_fh.readline().strip()
        count = 0
        while line != '':
            lst_tmp = line.split()
            chromosome = 'chr' + lst_tmp[0]
            start_pos = lst_tmp[3]
            end_pos = int(start_pos) + 1

            # Add SNP id (lst_tmp[1]) so that UCSC BED file can be converted back to plink bim file later
            output_line = chromosome+'\t'+start_pos+'\t'+str(end_pos)+'\t'+lst_tmp[1]+'\n'
            output_fh.write(output_line)

            count = count + 1
            if count%5000 == 0:
                progress_bar(count, total)   # Keep console busy
            line = input_fh.readline().strip()
        print('\n#Done')


def ucsc_bed_to_plink_bim(input_bed_fn, input_bim_fn, output_fn):
    '''
    Convert UCSC BED file back to plink bim file, based on SNP id and old plink .bim file
    (This bed file should be processed by liftover already)
    Parameters:
      - input_bed_fn: UCSC BED file, it is the converted result from Liftover program
      - input_bim_fn: The original plink bim file
      - output_fn: output file name
    '''
    print('\n#Read in plink .bim files ...')
    df_bed = pd.read_csv(input_bed_fn, sep='\t', dtype='str', header=None)
    df_bim = pd.read_csv(input_bim_fn, sep='\t', dtype='str', header=None)
    df_bed.columns = ['chr', 'start', 'end', 'SNP']
    df_bim.columns = ['chr', 'SNP', 'pos', 'coordinate', 'ALT', 'REF']

    print('#Converting ...')
    df_merge = df_bim.merge(df_bed, left_on='SNP', right_on='SNP')
    df_merge.dropna(axis=0, inplace=True)

    output_columns = ['chr_x','SNP', 'pos', 'start','ALT','REF']
    df_merge[output_columns].to_csv(output_fn, sep='\t', header=None, index=False)
    print('#Done')


def run_liftover():
    args = process_args() # Parse user input args
    if args.input.endswith('.bim'): # Process plink file
        plink_bim_to_ucsc_bed(args.input, args.output+'.bed')
        ucsc_bed_to_plink_bim(args.output+'.bed', args.input, args.output)
    else: # General text file as input
        txt_to_bed()

# Change input and output file names as needed
input_fn = '/data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/chr6_merged_raw.bim'
output_fn = '/data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/converted_UCSC_bed.bed'

# plink_bim_to_ucsc_bed(input_fn, output_fn)  # Convert plink .bim file to UCSC BED format
# Use this after processing
# liftOver /data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/converted_UCSC_bed.bed hg38ToHg19.over.chain.gz output.bed unlifted.bed

input_bed_fn = '/data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/output.bed'
input_bim_fn = '/data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/chr6_merged_raw.bim'
output_fn = '/data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/chr6_merged_raw_converted_hg19.bim'
ucsc_bed_to_plink_bim(input_bed_fn, input_bim_fn, output_fn)