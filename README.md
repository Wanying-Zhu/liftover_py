# Liftover_py
This is a python wrapper of UCSC liftover tool.
Commandline tool liftover_py can take PLINK .bim file or other text input, run liftover and return converted output follow the original format.

## Prerequisites
1. LiftOver must be installed/downloaded. Check [LiftOver executable](https://genome.ucsc.edu/goldenPath/help/hgTracksHelp.html#Liftover) on UCSC genome browser website.
2. Input file can be PLINK .bim or general text file, must uses tab as delimiters
3. Now only commandline version of liftover_py is avaialable.

## Example code
```bash
# --chr_id_pos is not needed if input file is PLINK .bim format
python formatting_plink_bim_to_UCSC_bed.py \
--input input_file \
--output output_file \
--output_path ./inputs \
--chain_file hg19ToHg38.over.chain.gz \
--liftover ./liftOver \
--chr_id_pos 0:1:2
```