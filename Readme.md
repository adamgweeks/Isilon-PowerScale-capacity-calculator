# Isilon/PowerScale Capacity calculator
(note PowerScale is the re-branding of Isilon in 2020 for naming consistency across Dell products)

# NOW with GEN 6 Node Pool Support!
Gen 6 forms Disk Pools (which OneFS uses to create failure domains and can restrict stripe widths) differently from previous generations of nodes.  The calculator now has the --gen6 option to adjust the stripe width accordingly!  for more info see: [Isilon Additional Info](http://isilon-additional.info).

Isilon has a unique approach to data protection protecting individual files, rather than protecting complete disks (as in RAID).

This file level protection allows for great flexibility when storing large quantities of data but has the drawback of being tough
to calculate.  If you were to use RAID 5 (4+1) and you asked what the overhead for this protection is, it would be simple (1/5 - 20% of your disk 
capacity would be used for protection.  On an Isilon system this would not be so simple and we'd need more information for calculating the overhead 
and therefore the raw capacity needed;

* What is the protection type? (2x,3x,4x,5x,6x,7x,8x,n+1,n+2,n+3,n+4,n+2:1,n+3:1,n+4:1,n+3:11,n+4:2)
* What is the size of the node pool? (group of identical nodes)
* how big is each individual file?
* How many files/directories are there? (each needs metadata)
* Are these GEN 6 or previous in the Node Pool?

Because the files are processed individually we'd need to use this information to calculate the resulting size of each file.

This script simply needs to be run on the host that can see the data to be migrated.  You supply it with the details needed to
calculate the eventual capacity and it will run through each file and calculate the resulting Isilon capacity (including metadata).

## Usage:

Firstly you need the Python shell to run the script.  Python is available for many platforms (Windows, Linux, Unix, OSX/MacOS and others)
[download Python](https://www.python.org/downloads/)

Note: There are 2 major current releases for Python, 2 & 3.  Please use appropriate script for your Python version (if you get this wrong you'll just get some error messages).
  Use `python --version` to check).

Then run the script using the following syntax:

`python isilon_capacity_calc_py2.py <source directory> -s <size of nodepool> -p <protection type>`

for example:

`python isilon_capacity_calc_py2.py /Users/weeksa/Documents/ -s 9 -p n+2:1`

Outputs:

```
Reading metadata...
Read metadata for  8019  files in (H:M:S:ms): 0:00:00.446705

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  26 GB
Isilon size is       :  29 GB
A protection overhead of  11.54 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.147969
Total running time (H:M:S:ms): 0:00:00.594736
```


Additional options:

`[-v (for verbose file list printed) | -c (for csv formatted verbose output) | -u output data units (KB,MB,TB,PB,H), default=H (H=human/auto sizing)]`

verbose mode will give you a list of individual files on screeen, CSV is meant for creating a .CSV file (can be opened in a spreadsheet for ease of reading)
note with CSV output you have to direct the output of the command into a file, like so:

`python3.6 isilon_capacity_calc_py3.py <source directory> -s <size of nodepool> -p <protection type> -u <data measurement units> -c > myfiles.csv`


## As this script is still in testing...

For testing results (Isilon vs script) see the [results_comparison_table.md](results_comparison_table.md) file; it does show that there are small differences (possibly a difference in rounding). 
For a detailed CSV output from the script (N+2 protection with a 5 node node pool) [click here...](https://github.com/adamgweeks/Isilon-capacity-calculator/blob/master/five_nodes_N%2B2%2Bprotection_sample.csv).


If you see any inaccuracies, or bugs please report to: [Issues](https://github.com/adamgweeks/Isilon-capacity-calculator/issues)

## Working test comparison

From a real Isilon cluster Node pool was 3 X200s.

- du -shA 
-- Shows size of directory *without including* protection data (A for Apparent data size)
- du -sh
-- Shows the size of the dir *including* protection data
- isi set -rRp '<protection><dir>' 
-- Changes the protection level of the data on the fly

### On Isilon test cluster:
![alt tag](./screenshot.png)
### Using script:

```
Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p n+1 -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.031035
Metdata size for Isilon will be: 2 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  618.76 MB
A protection overhead of  51.82 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002610
Total running time (H:M:S:ms): 0:00:00.033695

Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p n+2:1 -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.029415
Metdata size for Isilon will be: 4 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  629.47 MB
A protection overhead of  54.45 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002730
Total running time (H:M:S:ms): 0:00:00.032199

Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p n+3:1 -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.037244
Metdata size for Isilon will be: 5 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  638.88 MB
A protection overhead of  56.76 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002612
Total running time (H:M:S:ms): 0:00:00.039911

Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p n+4:1 -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.028041
Metdata size for Isilon will be: 6 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  650.72 MB
A protection overhead of  59.66 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002625
Total running time (H:M:S:ms): 0:00:00.030718

Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p 2x -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.030803
Metdata size for Isilon will be: 2 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  818.54 MB
A protection overhead of  100.84 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002243
Total running time (H:M:S:ms): 0:00:00.033099

Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p 3x -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.028204
Metdata size for Isilon will be: 4 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  1.2 GB
A protection overhead of  201.25 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002244
Total running time (H:M:S:ms): 0:00:00.030507

Linux1:isilon_capacity_calculator weeksa$ python isilon_capacity_calc_py2.py   ~/Desktop/isilon\ script\ test\ dir/ -p n+2:1 -s 3
You are able to read the  /Users/weeksa/Desktop/isilon script test dir/  dir
Reading metadata...
Read metadata for  11  DIRs and  161  files in (H:M:S:ms): 0:00:00.027710
Metdata size for Isilon will be: 4 MB

Calculating filesizes...
Percent: [########################################] Done!

Original data size is:  407.0 MB
Isilon size is       :  629.47 MB
A protection overhead of  54.45 % - percentage of additional protection data

Calculation time (H:M:S:ms):   0:00:00.002673
Total running time (H:M:S:ms): 0:00:00.030437
```
Please note that this script is **completely unsupported by Dell Technologies/EMC/Isilon** and should be considered as in a beta state/
experimental.  Although written in good faith there are of course **no guarantees** the results will be accurate.

If you discover any issues, have any feature suggestions please contact me at 
tweeksy@gmail.com or post a comment to [Issues](https://github.com/adamgweeks/Isilon-capacity-calculator/issues)
  
