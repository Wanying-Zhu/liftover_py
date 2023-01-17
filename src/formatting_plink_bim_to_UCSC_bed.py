# This code convert plink .bim file to UCSC BED file
# This is necessary for UCSC liftover program (convert between different genome assemblies)
# UCSC BED file has this format:
#       chrom     chromStart      chromEnd      SNP_id(Can be omitted)
#       chr3        12345           12346       rs1111(Can be omitted)

import pandas as pd
from process_args import process_args
import subprocess
import os

args = process_args()

def progress_bar(cur:int, total:int):
    '''
    Print progress bar
    '''
    percent = 100*cur/total
    progress = '=' * int(percent) + '>' + '-' * (99-int(percent))
    print(f'|{progress}| {percent:.2f}%', end='\r', flush=True)


def plink_bim_to_ucsc_bed(input_fn, output_fn):
    '''
    Convert plink .bim file to UCSC BED format
    '''
    # Get total number of lines of input file
    print('#Check number length of in put file')
    total = int(subprocess.run(f'wc -l {input_fn}'.split(), text=True, capture_output=True).stdout.split()[0])
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
        progress_bar(1, 1) # Print DONE progress bar

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

def txt_to_plink_bim(input_fn, output_fn):
    '''
    Convert general text file to pseudo plink .bim file. Columns should be arranged as below:
    - Chromosome code (either an integer, or 'X'/'Y'/'XY'/'MT'; '0' indicates unknown) or name
    - Variant identifier
    - Position in morgans or centimorgans (safe to use dummy value of '0')
    - Base-pair coordinate
    This pseudo .bim file will be deleted after conversion
    '''
    df = pd.read_csv(input_fn, sep='\t', header=None)
    idx_chr, idx_id, idx_pos = args.chr_id_pos.split(':') # get indices of columns
    idx_chr, idx_id, idx_pos = int(idx_chr), int(idx_id), int(idx_pos)

    # Check format of chromosome number
    # If chromosome number is not integer, strip the sting and only keep the number
    # Eg. Change CHR1 to 1
    #TODO:
    # WZ has not tested this feature out with corner cases.
    chr_val = df[idx_chr][0]
    try:
        chr_val = int(chr_val)
    except: # Need to use regular expression
        import re
        chr_val = re.findall(r'\d+$', chr_val)
        if len(chr_val)==0:
            print(f'#ERROR: Wrong format of chromosome number in original input file {args.input}')
            print('# - Valid formats are: CHR1, chr1 or 1')
            print(f'# - Current format is: {df[idx_chr][0]}')
            print('#END')
            exit()
        else:
            chr_text = df[idx_chr][0].split(chr_val)[0] # Get text portion in chromosome number for stripping
            df[idx_chr] = df[idx_chr].apply(lambda x: x.split(chr_text)[-1])

    # Fill rest columns with value of the first column
    df.iloc[:, [idx_chr, idx_id, 0, idx_pos, 0, 0]].to_csv(output_fn, sep='\t', index=False, header=False)

def ucsc_bed_to_text(input_fn, org_fn, output_fn):
    '''
    Convert UCSC BED format to original text file format
    Parameters:
    - input_fn: file in USCS BED format
    - org_fn: Original txt file (pre liftover)
    - output_fn
    Return:
    - Converted file is saved in output_fn
    '''
    idx_chr, idx_id, idx_pos = args.chr_id_pos.split(':')  # get indices of columns
    idx_chr, idx_id, idx_pos = int(idx_chr), int(idx_id), int(idx_pos)
    df_bed = pd.read_csv(input_fn, sep='\t', header=None)
    # BED file use chr1, chr2, ... in chromosome column, need to strip 'chr' portion for merging
    # 1st column in BED file is chromosome number
    # Some chromosome number is changed to after liftover
    df_bed[0] = df_bed[0].apply(lambda x: int(x.split('_')[0].split('chr')[-1]))
    df_org = pd.read_csv(org_fn, sep='\t', header=None)
    df_org.rename(columns={idx_pos:'-1'}) # Rename pos column to -1, so later we can replace it with liftovered values
    # Check if org file also needs conversion of chromosome numbers to integers
    org_chr_num = df_org[idx_chr][0]
    try:
        org_chr_num = int(org_chr_num)
    except: # If chromosome number is not numeric
        for chr_txt in ['chr', 'CHR']:
            if chr_txt in org_chr_num:
                df_org[idx_chr] = df_org[idx_chr].apply(lambda x: int(x.split(chr_txt)[-1]))
    #TODO
    # Might need to allow other text in the future

    # In BED format 1st column is chromosome number, 4nd column is ID
    df_bed.columns = [-1, -2, -3, -4] # Rename columns in df_bed so merge will not have columns with the same names
    df_merged = df_bed.merge(df_org, left_on=[-1, -4], right_on=[idx_chr, idx_id])
    df_merged_org = df_org.merge(df_merged[[idx_chr, idx_id]], on=[idx_chr, idx_id])
    df_merged_org[idx_pos] = df_merged[-2] # Replace position values by liftovered values
    df_merged_org.to_csv(output_fn, sep='\t', index=False, header=False)

def convert():
    print('\n#Convert input file to UCSC BED format for liftOver tool')
    # Prepare file names
    tmp_bed_fn = os.path.join(args.output_path, args.output.split('.')[0] + '.tmp.bed') # tmp BED file, created from input txt or plink bim file
    converted_bed = os.path.join(args.output_path,
                                 args.output.split('.')[0]) + '.converted.bed'  # Liftover converted BED file name
    unlifted = os.path.join(args.output_path, args.output.split('.')[0]) + '.unlifted.bed'  # File name of unlifted positions
    #TODO
    # Has not test plink bim as input
    if args.input.endswith('.bim'): # Process plink file
        plink_bim_to_ucsc_bed(os.path.join(args.output_path, args.input), tmp_bed_fn)
        # Run liftover
        # liftOver /data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/converted_UCSC_bed.bed hg38ToHg19.over.chain.gz output.bed unlifted.bed
        cmd = f'{args.liftover} {tmp_bed_fn} {args.chain_file} {converted_bed} {unlifted}'
        subprocess.run(f'rm {tmp_bed_fn}'.split()) # remove tmp file
        print(f'#Run liftover as:\n  {cmd}\n')
        subprocess.run(cmd.split())
        ucsc_bed_to_plink_bim(converted_bed,
                              os.path.join(args.output_path, args.input),
                              os.path.join(args.output_path, args.output))
    else:  # General text file as input, uses tab as delimiter, no header
        # tmp files might be removed later
        tmp_plink_fn = os.path.join(args.output_path, args.output.split('.')[0]+'.tmp.bim') # Convert text file to .bim format
        txt_to_plink_bim(args.input, tmp_plink_fn)
        plink_bim_to_ucsc_bed(tmp_plink_fn, tmp_bed_fn)
        # Run liftover
        # liftOver /data100t1/home/wanying/hla_analysis/data_and_doc/chr6_TopMed_imputed/converted_UCSC_bed.bed hg38ToHg19.over.chain.gz output.bed unlifted.bed
        cmd = f'{args.liftover} {tmp_bed_fn} {args.chain_file} {converted_bed} {unlifted}'
        print(f'#Run liftover as:\n  {cmd}\n')
        subprocess.run(cmd.split())
        subprocess.run(f'rm {tmp_plink_fn}'.split()) # Remove tmp files
        subprocess.run(f'rm {tmp_bed_fn}'.split())
        # Convert liftovered BED file back to original format
        ucsc_bed_to_text(converted_bed,
                         os.path.join(args.output_path, args.input),
                         os.path.join(args.output_path, args.output))
    print('\n#Done converting input file to UCSC BED format\n')

if __name__ == '__main__':
    convert()