# pipeline file to consume one month of data from any of several different upstream datasets and prepare them for localGP; see variable 'upstream' for supported data upstreams,
# and README.md for broader comments on data download and preparation before this step.
# usage: bash pipeline4localgp.sh <directory contianing one month of upstream data> <year> <month>

# set your run configuration here----------------------------------------------------------------

declare runtag='OP20260320'                               # unique ID for this run
declare variable='steric_hgt_anom'        # 'absolute_salinity', 'potential_temperature', 'conservative_temperature', 'potential_density', 'mld', 'dynamic_height_anom', 'steric_hgt_anom', 'thermosteric_hgt_anom_linar', 'halosteric_hgt_anom_linear', 'thermosteric_hgt_anom', 'halosteric_hgt_anom'
declare level=None                                # dbar to interpolate to if interpolation is desired; None otherwise
declare region='700,1850'                         # integration dbar region, string CSV, in integration mode
declare selectprofiles='false'                  # 'true' to run data selection step (slow), 'false' to use previously run data-selection step with the same runtag. Nominally should only need to run true once for a list of downstream variable computations.
## you probably don't need to touch the following
declare integration_mode='trapezoidal'             # integration method; currently only 'trapezoidal', or None if integration not desired
declare data_dir=$1				# where is the relevant upstream data?
declare year=$2					# year this data corresponds to
declare month=$3				# month this data corresponds to
declare pqc='1,2'                                   # qc to keep for pressure, can be single valued (0) or string CSV ('0,1')
declare tqc='1,2'                                   # qc to keep for temeprature
declare sqc='1,2'                               # qc to keep for salinity
declare wod_filetypes='PFL,MRB,CTD'		# WOD filetypes, wod only
declare upstream='argonc' 			# 'argovis', 'wod' or 'argonc' [wip, argonc only reliable one for now]
# don't touch below this line -------------------------------------------------------------------

# Input validation
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <directory contianing one month of upstream data> <year> <month>" >&2
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

# set up some file naming
qctag="p${pqc//,/}_t${tqc//,/}_s${sqc//,/}"
selectionfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_selected_profiles.parquet
if [[ "$region" -ne None ]]; then
    region_tag=${region/,/_}
    file_tag=${runtag}_${year}_${month}_${qctag}_${variable}_${region_tag}
elif [["$level" -ne None]]; then
    file_tag=${runtag}_${year}_${month}_${qctag}_${variable}_${level}
fi
varfile=${data_dir}/${file_tag}.parquet

# select profiles if needed, and compute physics
if [[ $selectprofiles == 'true' ]]; then
    if [[ $upstream == 'wod' ]]; then
        declare prep_id=$(sbatch --parsable wod.slurm $data_dir $year $month $wod_filetypes $pqc $tqc $sqc $selectionfile)
    elif [[ $upstream == 'argovis' ]]; then
        declare prep_id=$(sbatch --parsable argovis.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
    elif [[ $upstream == 'argonc' ]]; then
        declare prep_id=$(sbatch --parsable argonc.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
    fi

    declare varcreation=$(sbatch --parsable --dependency=afterok:$prep_id variable_creation.slurm $selectionfile $varfile $variable $integration_mode $region $level)
else
    declare varcreation=$(sbatch --parsable variable_creation.slurm $selectionfile $varfile $variable $integration_mode $region $level)
fi

# postprocessing: downsample as needed and turn into the matlab localgp expects
downsampled=${data_dir}/${file_tag}_downsampled.parquet
matlab=${data_dir}/${file_tag}.mat
declare downsample=$(sbatch --parsable --dependency=afterok:$varcreation downsample.slurm $varfile $downsampled)
sbatch --dependency=afterok:$downsample matlab4localgp.slurm $downsampled $matlab ${variable}


