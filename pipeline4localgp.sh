# pipeline file to consume one month of data from any of several different upstream datasets and prepare them for localGP; see variable 'upstream' for supported data upstreams,
# and README.md for broader comments on data download and preparation before this step.
# usage: bash pipeline4localgp.sh <directory contianing one month of upstream data> <year> <month> <runtag>

# set your run configuration here----------------------------------------------------------------

declare upstream='argonc' 			# 'argovis', 'wod' or 'argonc'
declare data_dir=$1				# where is the relevant upstream data?
declare year=$2					# year this data corresponds to
declare month=$3				# month this data corresponds to
declare runtag=$4                               # unique ID for this run
declare vartype='integration'                   # 'integration', 'interpolation', or 'none' (if no interpoltions or integrations needed)
declare variable='potential_temperature'        # 'absolute_salinity', 'potential_temperature', 'conservative_temperature', 'potential_density', 'mld'
declare level=10                                # dbar to interpolate to in interpolation mode
declare region='15,300'                         # integration dbar region, string CSV, in integration mode
declare pqc='1,2'                                   # qc to keep for pressure, can be single valued (0) or string CSV ('0,1')
declare tqc='1,2'                                   # qc to keep for temeprature
declare sqc='1,2'                               # qc to keep for salinity
declare wod_filetypes='PFL,MRB,CTD'		# WOD filetypes, wod only

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
if [[ $upstream == 'wod' ]]; then
    declare prep_id=$(sbatch --parsable wod.slurm $data_dir $year $month $wod_filetypes $pqc $tqc $sqc $selectionfile)
elif [[ $upstream == 'argovis' ]]; then
    declare prep_id=$(sbatch --parsable argovis.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
elif [[ $upstream == 'argonc' ]]; then
    declare prep_id=$(sbatch --parsable argonc.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
fi

varfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}.parquet
declare varcreation=$(sbatch --parsable --dependency=afterok:$prep_id variable_creation.slurm $selectionfile $variable ${varfile})

if [[ $vartype == 'interpolation' ]]; then
    interpfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_interpolated_${level}.parquet
    interp_downsampled=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_interpolated_${level}_downsampled.parquet
    interp_matlab=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_interpolated_${level}.mat
    declare interpolation=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable $interpfile)
    declare downsample=$(sbatch --parsable --dependency=afterok:$interpolation downsample.slurm $interpfile $interp_downsampled)
    sbatch --dependency=afterok:$downsample matlab4localgp.slurm $interp_downsampled $interp_matlab ${variable}_interpolation
elif [[ $vartype == 'integration' ]]; then
    region_tag=${region/,/_}
    integfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_integrated_${region_tag}.parquet
    integ_downsampled=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_integrated_${region_tag}_downsampled.parquet
    integ_matlab=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_integrated_${region_tag}.mat
    declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable $integfile)
    declare downsample=$(sbatch --parsable --dependency=afterok:$integration downsample.slurm $integfile $integ_downsampled)
    sbatch --dependency=afterok:$downsample matlab4localgp.slurm $integ_downsampled $integ_matlab ${variable}_integration
elif [[ $vartype == 'none' ]]; then
    var_downsampled=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_downsampled.parquet
    var_matlab=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}.mat
    declare downsample=$(sbatch --parsable --dependency=afterok:$varcreation downsample.slurm $varfile $var_downsampled)
    sbatch --dependency=afterok:$downsample matlab4localgp.slurm $var_downsampled $var_matlab ${variable}
fi
