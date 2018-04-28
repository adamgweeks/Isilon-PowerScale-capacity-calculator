
# Python script to calc Isilon file space usage
# written by Adam.Weeks@dell.com
# unofficial and NOT supported by Dell Technologies/EMC/Isilon!

# example useage: python isilon_space_calc_py2.py /Users/user1/Documents/ -s 9 -p N+2
# see https://github.com/adamgweeks/Isilon-capacity-calculator
#
# for Python 2!


from datetime import datetime	# get script start time
startTime = datetime.now()		# script timed as this could take a while!	

#take in cmd line arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="source directory (will scan this dir and all subdirs from this point)")
parser.add_argument("--node_pool_size","-s", help="the node pool size (number of nodes)",type=int,required=True)
parser.add_argument("--protection","-p", help="data protection level, defaults to: N+2:1",default="N+2:1",required=True)
parser.add_argument("--units","-u", help="output data units (KB,MB,TB,PB,H), default=H (H=human/auto sizing)",default="H")
parser.add_argument("--verbose","-v", help="show individual file size comparisson",action="store_true")
parser.add_argument("--metadata_stuffer_size","-mss", help="specify the estimated additional metadata overhead (ADS etc)",type=int,default=3584)
parser.add_argument("--csv","-c", help="verbose output as CSV file",action="store_true")


# human filesizing function
def human_size(size_in_b):
		out_size=float()
		out_size=(size_in_b/(1024*1024*1024*1024*1024))
		if out_size>=1:
			#units="PB"
			output=[out_size,'PB']
			return(output)  
		else:
			out_size=(size_in_b/(1024*1024*1024*1024))
			if out_size>=1:
				#units="TB"
				output=[out_size,'TB']
				return(output)  
				#print "outsize is ",out_size,units
			else:
				out_size=(size_in_b/(1024*1024*1024))
				if out_size>=1:
					output=[out_size,'GB']
					return(output)  
				else:
					out_size=(size_in_b/(1024*1024))
					if out_size>=1:
						output=[out_size,'MB']
						return(output)  
					else:
						output=[size_in_b/1024,'KB']
						return(output)
					
#progress bar function
def progress(end_val, bar_length,prog):	
		percent = float(prog) / end_val
		hashes = '#' * int(round(percent * bar_length))
		spaces = ' ' * (bar_length - len(hashes))
		if(prog==end_val):
				sys.stdout.write("\rPercent: [{0}] Done!".format(hashes + spaces, int(round(percent * 100))))
				sys.stdout.write("({} of {} files)".format(prog,end_val))

		else:
				sys.stdout.write("\rPercent: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
				sys.stdout.write("({} of {} files)".format(prog,end_val))


		sys.stdout.flush()
	
#setup the vars needed for calculations        
args = parser.parse_args()
dirname=args.directory
protection_string=args.protection
node_pool_size=args.node_pool_size
meta_stuffer=args.metadata_stuffer_size
data_units=args.units
verbose=args.verbose
csv=args.csv
total_empty_files=0
total_small_files=0
total_partial_files=0
total_perfect_files=0
total_large_files=0
block_size=0
total_filesize_small_isilon=0
total_filesize_partial_isilon=0
total_filesize_perfect_isilon=0
total_filesize_large_isilon=0
total_filesize_small_orig=0
total_filesize_partial_orig=0
total_filesize_perfect_orig=0
total_filesize_large_orig=0
mbig_files=0
msmall_files=0

if csv==True:
	verbose=True

#translate output units into divisible number (from bytes to x units)
data_units=data_units.upper()
if data_units=="KB":
	odata_units=""
	data_divider=1024
elif data_units=="MB":
	odata_units=""
	data_divider=1024*1024
elif data_units=="GB":
	odata_units=""
	data_divider=1024*1024*1024
elif data_units=="TB":
	odata_units=""
	data_divider=1024*1024*1024*1024
elif data_units=="PB":
	odata_units=""
	data_divider=1024*1024*1024*1024*1024
elif data_units=="H":
	odata_units="H"
	data_divider=1                  
else :
	print("Data units size not recognised")
	exit()


#translate requested protection string into meaning for script
protection_string=protection_string.lower()
if protection_string=="n+1":
	requested_protection=1
	stripe_requested=True
elif protection_string=="n+2":
	requested_protection=2
	stripe_requested=True
elif protection_string=="n+3":
	requested_protection=3
	stripe_requested=True
elif protection_string=="n+4":
	requested_protection=4
	stripe_requested=True
elif protection_string=="n+2:1":
	requested_protection=2
	stripe_requested=True
	node_pool_size=(node_pool_size * 2) 
elif protection_string=="n+3:1":
	requested_protection=3
	stripe_requested=True
	node_pool_size=(node_pool_size * 3)
elif protection_string=="n+4:1":
	requested_protection=4
	stripe_requested=True
	node_pool_size=(node_pool_size * 4)
elif protection_string=="n+3:11":
	requested_protection=3
	stripe_requested=True
	node_pool_size=(node_pool_size * 2)
elif protection_string=="n+4:2":
	requested_protection=4
	stripe_requested=True
	node_pool_size=(node_pool_size * 2)                       
elif protection_string=="2x":
	requested_protection=2
	stripe_requested=False
elif protection_string=="n+1n":
	requested_protection=1
	stripe_requested=True
elif protection_string=="n+2n":
	requested_protection=2
	stripe_requested=True
elif protection_string=="n+3n":
	requested_protection=3
	stripe_requested=True
elif protection_string=="n+4n":
	requested_protection=4
	stripe_requested=True
elif protection_string=="n+2d:1n":
	requested_protection=2
	stripe_requested=True
	node_pool_size=(node_pool_size * 2) 
elif protection_string=="n+3d:1n":
	requested_protection=3
	stripe_requested=True
	node_pool_size=(node_pool_size * 3)
elif protection_string=="n+4d:1n":
	requested_protection=4
	stripe_requested=True
	node_pool_size=(node_pool_size * 4)
elif protection_string=="n+3d:1d1n":
	requested_protection=3
	stripe_requested=True
	node_pool_size=(node_pool_size * 2)
elif protection_string=="n+4d:2n":
	requested_protection=4
	stripe_requested=True
	node_pool_size=(node_pool_size * 2)                       
elif protection_string=="2x":
	requested_protection=2
	stripe_requested=False
elif protection_string=="3x":
	requested_protection=3
	stripe_requested=False
elif protection_string=="4x":
	requested_protection=4
	stripe_requested=False
elif protection_string=="5x":
	requested_protection=5
	stripe_requested=False
elif protection_string=="6x":
	requested_protection=6
	stripe_requested=False
elif protection_string=="7x":
	requested_protection=7
	stripe_requested=False
elif protection_string=="8x":
	requested_protection=8
	stripe_requested=False
else: 
	print("unrecognised protection type")  
	exit() 

#setup vars used later in script
total=0
filesizes=[]
filenames=[]
total_size=0
total_size=float(total_size)
total_original_size=0
total_original_size=float(total_original_size)
t_total=0

import os
import sys


#do some sanity checks on given arguments

#check if DIR exists
if os.path.isdir(dirname) is False:
	print("Error! directory:'",dirname,"' doesn't appear to exist.")
	exit()
#check if directory is readable
if os.access(dirname, os.R_OK):
	print("You are able to read the ",dirname," dir")	
else:
	print("Error! dir:",dirname," is not readable.")	
	exit()

#if the node pool size is greater than the max stripe size, limit it TO the maximum stripe size
if (node_pool_size - requested_protection)>16:
	node_pool_size=(16 + requested_protection)	

#check striping will work with the node pool size given    
if stripe_requested==True:    
	#valid_min_size=(requested_protection+1)+requested_protection #could have used easier logic (2 x RP + 1) but wanted to match more to the human logic used (Must be enough nodes for more DUs than FECs).
	valid_min_size=requested_protection*2 #Now the protection only needs to be equal DUs to FECs (in newer versions of OneFS, I believe it's 7.1 and higher)
	if node_pool_size<valid_min_size:
		print("Node pool is too small for requested protection to work!")
		exit()
	


i=0	#ready for progress function

polear=['/','|','\\','-']	#ready for showing the metadata read is still working!
polepos=0
if csv==False:
	print("Reading metadata...")
metaTime = datetime.now() #timing how long the metadata read took
files_to_process=0# for progress indicator, so we know the total number of files later
dirs_to_process=0 # for counting inodes (to indicate metadata size)

for root, dirs, files in os.walk(dirname):	#go and retrieve a list of all the files in the given DIR
	for dir in dirs:
		dirpath = os.path.join(root, dir)
		if os.path.isdir(dirpath):	# check this is a DIR (to count the inodes)
			dirs_to_process=dirs_to_process+1
		
	for filename in files:
		if csv==False:
			polepos=polepos+1
			if (polepos>3):
				polepos=0
			pole=polear[polepos]
			sys.stdout.write("\r{0}".format(pole))
			sys.stdout.flush()
		filepath = os.path.join(root, filename)
		if os.path.isfile(filepath):	# check this is a file (i.e. not a link)
			files_to_process=files_to_process+1 # used later for progress bar
			file_size=os.path.getsize(filepath)
			filesizes.append(file_size) # add to file size for this file to the list
			if(file_size>10485760):
				mbig_files=mbig_files+1 # if the file is over 10MB it will get an 8KB inode (rule of thumb from https://community.emc.com/thread/178281?start=15&tstart=0) 
			else:
				msmall_files=msmall_files+1
			#filesizes.append((os.stat(filepath).st_blocks * 512)) #new alternative sizing, to match disk blocks size on Isilon (and most disks/OS configs)
			if verbose==True:
				filenames.append(filename)
   
sys.stdout.write("\r") # clear line used for the 'moving line'
sys.stdout.flush()

# change to numbers to process (dirs+1) files as is:
dirmcount = dirs_to_process
#filemcount = files_to_process

if stripe_requested:
	dirmcount = dirmcount * (requested_protection + 2) # DIRs get an extra inode mirror by default
	mbig_files=mbig_files * (requested_protection + 1) # metadata is always mirrored, but we have to mirror again if it's striped (to match the striping protection level)
	msmall_files=msmall_files * (requested_protection + 1) # metadata is always mirrored, but we have to mirror again if it's striped (to match the striping protection level)

else:
	dirmcount = dirmcount * (requested_protection + 1)
	mbig_files=mbig_files * requested_protection # if data is mirrored we simply mirror the metadata
	msmall_files=msmall_files * requested_protection # if data is mirrored we simply mirror the metadata

metadata_size=(dirmcount * 8192)+(msmall_files * 512)+(mbig_files * 8192)+(meta_stuffer*(msmall_files+mbig_files+dirmcount))

#print "got msize:",metadata_size
#exit()
#metadata_size=(filemcount + dirmcount) * ibs_size	
total_size=total_size + metadata_size # tally up metadata size
if odata_units=="H":
		output=human_size(metadata_size)
		metadata_size=output[0]
		data_units=output[1]
else:
		metadata_size=metadata_size/data_divider	
		metadata_size=round(metadata_size,4) # (rounded to 3 decimal places for ease of reading)
print("Read metadata for ",dirs_to_process," DIRs and ",files_to_process," files in (H:M:S:ms):",datetime.now() - startTime) # show how long this took and how many files we have (really just for reference) 
output=human_size(meta_stuffer)
mss_h_size=output[0]
mss_h_units=output[1]
i=0 #for progress bar		

print("")
if csv==False:
	print("Calculating filesizes...")
if verbose==True:
	if csv==False:
		print("")
		print("Filename					| Original size (KB)  |  Isilon size (KB)")
	else:
		print("")
		print("")
		print("Isilon space calculator report for ",dirname,"with ", node_pool_size ," nodes using ",protection_string," protection")
		print("")
		print("")
		print("Filename,Original size (KB),Isilon size(KB)")
	
calcTime = datetime.now() # for timing how long the processing takes 
	
# go through each file in the list and we'll work out how much protection detail Isilon would add (for given cluster size and protection setting used)       
for file_size in filesizes:

	file_type=""
	
	i=i+1
	if verbose==False: 
		progress(files_to_process,40,i)# show progress bar
	#file_size=file_size/1024 # convert KB first
		# round up to ceiling 8kb (Isilon uses an 8KB filesystem block size, so we need to round up)
	
	if (block_size==0):
		testfs=file_size
		try:
			block_size=os.statvfs(dirname).f_frsize	#try to find the native FS block size using Unix stats command (will fail in Windows based OS)
		except AttributeError:  # if above command fails, let's try finding the native FS block size using Windows native DLL instead
			import ctypes

			sectorsPerCluster = ctypes.c_ulonglong(0)
			bytesPerSector = ctypes.c_ulonglong(0)
			rootPathName = ctypes.c_wchar_p(dirname)

			ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName,
    			ctypes.pointer(sectorsPerCluster),
    			ctypes.pointer(bytesPerSector),
   	 			None,
    			None,
			)
			spc=sectorsPerCluster.value
			bps=bytesPerSector.value
			block_size = spc * bps
	
	#Round all the filesize calculations (for the original data size) to the blocksize of the native filesystem (of the system this script is running on)
	#block_size=8192 # just for testing (to match oneFS block size)
	testfs=file_size

	if (file_size>0):	
		file_size=int(block_size * round(float(testfs)/block_size))
		if(file_size<testfs):
			file_size=testfs + block_size
	
		
#end of pre-rounding test

	total_original_size=file_size+total_original_size # totting up the total size of the original files
	osize=file_size # for verbose output
	if file_size==0:
		total_empty_files+=1 # increment the number of empty files
	else :
		remainder=0       
	# round up to ceiling 8kb (Isilon uses an 8KB filesystem block size, so we need to round up)		
		rounded_file_size=int(8192 * round(float(file_size)/8192))
		if(rounded_file_size<file_size):
			rounded_file_size=rounded_file_size + 8192
	# if mirroring protection was requested we simply need to multiply the rounded size (no need for complex stripe calc
		if stripe_requested==False:
				file_size=rounded_file_size * requested_protection
				remainder_size=0
	# if striping was requested we have to do a more complex calc			
		else:
				#check if the file is 'small' (i.e. less than, or equal to 128KB), if it is small it will be mirrored
				if rounded_file_size<=131072:
					total_small_files += 1 #increment the counter for small files
					T_requested_protection = requested_protection + 1
					file_size=rounded_file_size * T_requested_protection
					remainder_size=0
					file_type="small"
				else:

				# as file is larger than 128KB (and we've already checked for a mirroring request), we'll have to stripe the data		
						DU_count=float(rounded_file_size)/131072 # work out how many DUs (Data Units) will be needed
				#check if DU_count is integer (if not we have a partial DU)
						if (float(DU_count)).is_integer():
							overspill=0 # overspill is how much we need to remove from the end of the LAST DU, if it divides perfectly there will be no overspill to remove
						else:
						#we have a partial DU
							DU_count=int(DU_count)
							overspill=131072-(rounded_file_size - (int(DU_count)*131072)) # our last DU will not really be complete, so how much do we remove?  (the overspill value)


						actual_stripe_size=node_pool_size - requested_protection # get the stripe size (for DUs) available
						no_stripes=float(0)
						no_stripes=DU_count/float(actual_stripe_size)# how many stripes do we need (not necessarily an integer result)
						rounded_stripes=int(no_stripes)
						remainder_size=rounded_file_size - ((actual_stripe_size * rounded_stripes) * 131072)# data left over (from partial)

						#if (no_stripes<=1) and (no_stripes>0): #we don't have a full stripe here, so no need to calculate the full stripes size.
						if (no_stripes==1) and (remainder_size>0): # we have just over 1 stripe (one a bit at least!)
																total_large_files+= 1 # increment the counter for large files
																file_type="large"
																rounded_stripes=int(no_stripes) # round up the number of stripes by converting to an integer (we will handle the 'overspill' of writing a full stripe later)r
																rounded=False
																full_stripes_size=((actual_stripe_size * rounded_stripes) + (requested_protection * rounded_stripes)) * 131072 # how would the stripes be written (taking into account the node pool size and protection
						elif (no_stripes<1) and (no_stripes>0): # we have less than 1 complete stripe
																total_partial_files+=1 # increment the number of partial files
																file_type="partial"
																no_stripes=1
																full_stripes_size=0
																rounded=True
						elif (no_stripes==1) and (overspill==0) and (remainder_size==0): # we have a perfect stripe!
																total_perfect_files+=1 # increment the number of perfect stripe files
																file_type="perfect"
																rounded=False
					
						else: 		# we have more than 1 stripe

																total_large_files+= 1 #increment the counter for large files
																file_type="large"
																rounded_stripes=int(no_stripes) # round up the number of stripes by converting to an integer (we will handle the 'overspill' of writing a full stripe later)
																rounded=False
																full_stripes_size=((actual_stripe_size * rounded_stripes) + (requested_protection * rounded_stripes)) * 131072 # how would the stripes be written (taking into account the node pool size and protection)
						# check for overspill
						if(overspill>0):
							#remainder_size=0
							if rounded==True:
									remainder_size=rounded_file_size
							else:
									remainder_size=rounded_file_size - ((actual_stripe_size * rounded_stripes) * 131072)# data left over (from partial)
				#calculate the 'remainder' stripe that needs to be written
				#do we need to mirror the remainder?
						if (remainder_size<=131072) and (remainder_size>0):
							T_requested_protection = requested_protection + 1
							remainder_size=(remainder_size * T_requested_protection)
							file_size=remainder_size + full_stripes_size
						elif (remainder_size>131072) and (remainder_size>0):
				#remainder is big enough to form final stripe
							remainder_size=((remainder_size + (requested_protection * 131072)))
							file_size=remainder_size + full_stripes_size
						else :
				#we have a perfect stripe
							file_size=(actual_stripe_size + requested_protection) * 131072
			
	if verbose==True:
		filename=filenames[(i-1)]
		osize_s=str(((osize/1024)))
		file_size_s=str((file_size/1024))
		if csv==False:
			osize_s=osize_s.rjust(15)
			filename=filename.ljust(50)
			file_size_s=file_size_s.ljust(15)
			print(filename,":",osize_s," - ",file_size_s)
		else:
			print(filename,",",osize_s,",",file_size_s)			
	t_total=total_size
	total_size=(t_total+file_size)
	t_total=total_size
	if file_type=="small" :
		total_filesize_small_orig=total_filesize_small_orig + osize
		total_filesize_small_isilon=total_filesize_small_isilon + file_size
	elif file_type=="partial" :
		total_filesize_partial_orig=total_filesize_partial_orig + osize
		total_filesize_partial_isilon=total_filesize_partial_isilon + file_size
	elif file_type=="perfect" :
		total_filesize_perfect_orig=total_filesize_perfect_orig + osize
		total_filesize_perfect_isilon=total_filesize_perfect_isilon + file_size
	elif file_type=="large" :
		total_filesize_large_orig=total_filesize_large_orig + osize
		total_filesize_large_isilon=total_filesize_large_isilon + file_size


if i<=0:
	print("Error! Directory is empty, nothing to show!")
	exit()
	
# calc percentage difference
diff=((total_size / float(total_original_size))*100)-100
diff=round(diff,2) # (rounded to 2 decimal places for ease of reading)

if odata_units=="H":
		output=human_size(total_original_size)
		totemp=output[0]
		data_units=output[1]
else:	
		totemp=total_original_size/data_divider

totemp=round(totemp,2)

#show the results of all this (timings are more for reference as this could take hours/days!)
print("")
print("")
output=human_size(block_size)
block_size=output[0]
mdata_units=output[1]	
print("Original data size is: ",totemp,data_units," (given native block size of",block_size,mdata_units,").")

if odata_units=="H":
		output=float()
		total_size=float(total_size)
		output=human_size(total_size)
		total_size=output[0]
		data_units=output[1]
else:	
		#total_size=float(total_size)
		total_size=total_size/data_divider

#total_size=total_size+metadata_size	
total_size=round(total_size,2)
	
print("Isilon size is       : ", total_size,data_units)
print("A protection overhead of ",diff,"% - percentage of additional protection data")
print("")
print("Calculation time (H:M:S:ms):  ",datetime.now() - calcTime)  
print("")
print("Data breakdown:")
print("Metdata size for Isilon will be:",metadata_size,data_units,"(with a metadata stuffer size of ",mss_h_size,mss_h_units,"per file)")     
print("Empty files (0 bytes):",total_empty_files)
output=human_size(total_filesize_small_isilon)
total_size_isilon=round(float(output[0]),2)
data_units_isilon=output[1]
output=human_size(total_filesize_small_orig)
total_size_orig=round(float(output[0]),2)
data_units_orig=output[1]
print("Small files (128KB or less): ",total_small_files,"size orig:",total_size_orig,data_units_orig,"Isilon size:",total_size_isilon,data_units_isilon)
if total_perfect_files>0:
		output=human_size(total_filesize_perfect_isilon)
		total_size_isilon=round(float(output[0]),2)
		data_units_isilon=output[1]
		output=human_size(total_filesize_perfect_orig)
		total_size_orig=round(float(output[0]),2)
		data_units_orig=output[1]
		print("Perfect stripe (exactly 1 stripe) files:",total_perfect_files,"size orig:",total_size_orig,data_units_orig,"Isilon size:",total_size_isilon,data_units_isilon)
output=human_size(total_filesize_partial_isilon)
total_size_isilon=round(float(output[0]),2)
data_units_isilon=output[1]
output=human_size(total_filesize_partial_orig)
total_size_orig=round(float(output[0]),2)
data_units_orig=output[1]
print("Partial files (less than one complete stripe): ",total_partial_files,"size orig:",total_size_orig,data_units_orig,"Isilon size:",total_size_isilon,data_units_isilon)
output=human_size(total_filesize_large_isilon)
total_size_isilon=round(float(output[0]),2)
data_units_isilon=output[1]
output=human_size(total_filesize_large_orig)
total_size_orig=round(float(output[0]),2)
data_units_orig=output[1]
print("Large files (more than 1 full stripe): ",total_large_files,"size orig:",total_size_orig,data_units_orig,"Isilon size:",total_size_isilon,data_units_isilon)
print("Total :",files_to_process," files")
print("Total running time (H:M:S:ms):",datetime.now() - startTime)

  

 
