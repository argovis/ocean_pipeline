# pipeline file to consume one month of data from argonc and produce a corresponding matlab file for a generic study over a selection of variables
# and README.md for broader comments on data download and preparation before this step.
# usage: bash pipeline4derivedvar.sh <directory contianing one month of upstream data> <year> <month> <runtag>

# set your run configuration here----------------------------------------------------------------

declare data_dir=$1				# where is the relevant upstream data?
declare year=$2					# year this data corresponds to
declare month=$3				# month this data corresponds to
declare runtag=$4                               # unique ID for this run
declare variable='potential_density,potential_temperature,absolute_salinity,conservative_temperature'        # 'absolute_salinity', 'potential_temperature', 'conservative_temperature', 'potential_density', 'mld'
declare pqc=1                                   # qc to keep for pressure, can be single valued (0) or string CSV ('0,1')
declare tqc=1                                   # qc to keep for temeprature
declare sqc=1                               # qc to keep for salinity

# don't touch below this line -------------------------------------------------------------------

# Input validation
if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <directory contianing one month of upstream data> <year> <month> <runtag>" >&2
  exit 1
fi
if [ ! -e "$data_dir" ]; then
  echo "Error: Path '$data_dir' does not exist." >&2
  exit 1
fi
if ! [[ "$year" =~ ^-?[0-9]+$ ]]; then
  echo "Error: '$year' is not a valid year, YYYY." >&2
  exit 1
fi
if ! [[ "$month" =~ ^-?[0-9]+$ ]]; then
  echo "Error: '$month' is not a valid month, 1-12." >&2
  exit 1
fi
if [ -z "$runtag" ]; then
  echo "Error: string argument is empty." >&2
  exit 1
fi

# data prep
qctag="p${pqc//,/}_t${tqc//,/}_s${sqc//,/}"
selectionfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_selected_profiles.parquet
declare prep_id=$(sbatch --parsable derivedvar.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
varfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_derived_vars.parquet
declare varcreation=$(sbatch --parsable --dependency=afterok:$prep_id variable_creation.slurm $selectionfile $variable ${varfile})
downsampled=${data_dir}/${runtag}_${year}_${month}_${qctag}_derived_vars_downsampled.parquet
declare downsample=$(sbatch --parsable --dependency=afterok:$varcreation downsample.slurm $varfile $downsampled)
matlab=${data_dir}/${runtag}_${year}_${month}_${qctag}_derived_vars.mat
sbatch --dependency=afterok:$downsample matlab4derivedvar.slurm $downsampled $matlab

