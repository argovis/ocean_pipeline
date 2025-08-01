for year in {2004..2024}
do
    for month in {1..12}
    do
        mkdir -p ${year}_${month}
        month_padded=$(printf "%02d" "$month")
        next_month_padded=$(printf "%02d" $((month+1)))
        filename=${year}_${month}/${year}_${month_padded}.json
        if [[ $month -lt 12 ]]; then
            daterange="startDate=${year}-${month_padded}-01T00:00:00Z&endDate=${year}-${next_month_padded}-01T00:00:00Z"

        fi

        if [[ $month -eq 12 ]]; then
            daterange="startDate=${year}-${month_padded}-01T00:00:00Z&endDate=$((year+1))-01-01T00:00:00Z"
        fi
        curl -H "x-argokey: guest" "https://argovis-api.colorado.edu/argo?data=temperature,pressure,salinity,temperature_argoqc,pressure_argoqc,salinity_argoqc&${daterange}" -o $filename
        sleep 60
    done
done
