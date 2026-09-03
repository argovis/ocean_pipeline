# user entrypoint for running ocean_pipeline over a complete dataset
# usage: set your run parameters in pipeline4localgp.sh and here, then bash launch_localgp_pipelines.sh

# config ---------------------------
runtag=OP20260901
variable=potential_temperature
startyear=2004 # inclusive
endyear=2025   # inclusive
sorteddir=/scratch/alpine/wimi7695/argo_doi_2026/sorted # whatever $target_dir/sorted was when you ran dl_sort.sh
rundir=/scratch/alpine/wimi7695/localGP_results
localgpdir=/pl/active/giglio/localGP/localGP # a blank copy of the localGP repo, https://github.com/argovis/localGP, with MasksInput populated and an empty MonthlyInput dir.
# end config -----------------------

## copy localGP repo for each layer
mkdir -p ${rundir}/${variable}/${runtag}
for level in '15_20' '15_300' '300_700' '700_1000' '700_1850' '1800_1850'; do
    mkdir ${rundir}/${variable}/${runtag}/${level}
    cp -r ${localgpdir}/. ${rundir}/${variable}/${runtag}/${level}/.
    mkdir ${rundir}/${variable}/${runtag}/${level}/MonthlyInput/${startyear}_${endyear}
done

## launch pipelines
for ((year=startyear; year<=endyear; year++)); do
    for month in {1..12}; do
        monthstring=$(printf "%02d" "$month")
        prep_id=$(bash pipeline4localgp.sh ${sorteddir}/${year}_${monthstring} $year $month ${rundir}/${variable}/${runtag}/${level}/MonthlyInput/${startyear}_${endyear} $runtag $variable "${level//_/,}" 0xDEADBEEF true)
        for level in '15_20' '15_300' '300_700' '700_1000' '700_1850' '1800_1850'; do
            bash pipeline4localgp.sh ${sorteddir}/${year}_${monthstring} $year $month ${rundir}/${variable}/${runtag}/${level}/MonthlyInput/${startyear}_${endyear} $runtag $variable "${level//_/,}" $prep_id false
        done
    done
done
