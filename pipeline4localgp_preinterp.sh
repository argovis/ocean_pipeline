# pipeline file to consume one month of data from any of several different upstream datasets and prepare them for localGP; see variable 'upstream' for supported data upstreams,
# and README.md for broader comments on data download and preparation before this step.
# usage: bash pipeline4localgp.sh <directory contianing one month of upstream data> <year> <month>

# set your run configuration here----------------------------------------------------------------

declare upstream='argonc' 			# 'argovis', 'wod' or 'argonc' [wip, argonc only reliable one for now]
declare data_dir=$1				# where is the relevant upstream data?
declare year=$2					# year this data corresponds to
declare month=$3				# month this data corresponds to
declare runtag='OPdev'                               # unique ID for this run
declare vartype='none'                   # 'integration', 'interpolation', or 'none' (if no interpoltions or integrations needed)
declare variable='steric_hgt_anom'        # 'absolute_salinity', 'potential_temperature', 'conservative_temperature', 'potential_density', 'mld', 'dynamic_height_anom'
declare preinterps='temperature,salinity' # variables to preinterpolate, string CSV
declare pscale=10000                       # scale factor to multiply pressures by before integration (10000 == dbar->Pa)
declare region='700,1850'                         # integration dbar region, string CSV, in integration mode
declare pqc='1,2'                                   # qc to keep for pressure, can be single valued (0) or string CSV ('0,1')
declare tqc='1,2'                                   # qc to keep for temeprature
declare sqc='1,2'                               # qc to keep for salinity
declare wod_filetypes='PFL,MRB,CTD'		# WOD filetypes, wod only
declare selectprofiles='true'                  # 'true' to run data selection step (slow), 'false' to use previously run data-selection step with the same runtag. Nominally should only need to run true once for a list of 'region' values.

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

region_tag=${region/,/_}
qctag="p${pqc//,/}_t${tqc//,/}_s${sqc//,/}"
selectionfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_selected_profiles.parquet
preinterpolationfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_preinterpolation_${region_tag}.parquet
if [[ $selectprofiles == 'true' ]]; then
    if [[ $upstream == 'wod' ]]; then
        declare prep_id=$(sbatch --parsable wod.slurm $data_dir $year $month $wod_filetypes $pqc $tqc $sqc $selectionfile)
    elif [[ $upstream == 'argovis' ]]; then
        declare prep_id=$(sbatch --parsable argovis.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
    elif [[ $upstream == 'argonc' ]]; then
        declare prep_id=$(sbatch --parsable argonc.slurm $data_dir $year $month $selectionfile $pqc $tqc $sqc)
    fi
    declare preinterpolation=$(sbatch --parsable --dependency=afterok:$prep_id interpolate.slurm $selectionfile $preinterpolationfile $preinterps $region )
else
    declare preinterpolation=$(sbatch --parsable interpolate.slurm $selectionfile $preinterpolationfile $preinterps $region )
fi

# KM: preinterp will be followed by an integration, probably - generalize iff needed.
varfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_${region_tag}.parquet
integfile=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_integrated_${region_tag}.parquet
downsampled=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_integrated_${region_tag}_downsampled.parquet
matlab=${data_dir}/${runtag}_${year}_${month}_${qctag}_${variable}_integrated_${region_tag}.mat
declare varcreation=$(sbatch --parsable --dependency=afterok:$preinterpolation variable_creation.slurm $preinterpolationfile $variable ${varfile} ${region})
declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile None $variable $integfile $pscale) # KM: None for region to skip interpolation and directly integrate
declare downsample=$(sbatch --parsable --dependency=afterok:$integration downsample.slurm $integfile $downsampled)
sbatch --dependency=afterok:$downsample matlab4localgp.slurm $downsampled $matlab ${variable}_integration


