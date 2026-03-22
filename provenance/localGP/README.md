# localGP input run records

Production candidate runs have critical provenance data recorded here.

## OP20250808* series

Argonc -> localGP runs from the following environment:

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250808
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250814* series

Almost identical to OP20250808* except realtime data is never accepted.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250814
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250825* series

Similar to OP20250814*, with corrections for temperature units (all temperatures in celsius when used for calculating downstream variables, converted to kelvin for temperature integrals only)

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250825
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250825b* series

Allows realtime data like OP20250808* while managing temperature units like OP20250825*.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250825b
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250826* series

Allows realtime data, adds dynamic sea level anomaly

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250826
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250826b* series

Rejects realtime data, adds dynamic sea level anomaly

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250826b
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250829* series

Rejects realtime data, maps localGP input longitudes onto [20,380)

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250829
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250829b* series

Accepts realtime data, maps localGP input longitudes onto [20,380)

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250829b 
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250912* series

Rejects realtime data, updates JULD QC to allow 1,8

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250912
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250912b* series

Accepts realtime data, updates JULD QC to allow 1,8

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250912
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20251125 series

Accepts realtime data, includes downsampling correction made for the derivedvar project, includes operational updates to localGP

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20251017
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20251125
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20251126 series

Minor opertional corrections versus OP20251125.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20251126
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20251126
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20251216 series

As OP20251126 but uses the December 2025 Argo DOI data and tags some parpool management corrections in localGP

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20251126
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20251216
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://www.seanoe.org/data/00311/42182#124450

## OP20260110 series

First tag on 2026 Argo DOI; also includes some improved audit logging for ocean-pipeline, with no major changes to localGP.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20260110
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20251216
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://doi.org/10.17882/42182#125185

## OP20260110b series

As OP20260110 but excluding realtime data.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20260110
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20251216
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://doi.org/10.17882/42182#125185

## OP20260127 series

Allows QC 2 for pressure, temperature, salinity, JULD QC and location QC; allows realtime data for the last 5 years

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20260127
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20251216
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://doi.org/10.17882/42182#125185

## OP20260310 series

Compared to OP20260127: Keep JULD QC 1,2,8, position QC 1,2, and TSp QC 1,2; keep best of DAR as available regardless of age; allow maximum 200 dbar gaps between interpolated and in situ data; and downsample on 0.25 degree x 1 week bins. 

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20260310
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20260310
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://doi.org/10.17882/42182#125185

## OP20260320 series

Compared to previous: Implements steric sea height anomaly estimators from https://ecco-v4-python-tutorial.readthedocs.io/Steric_height.html in ocean pipeline, and iterates on archiving strategy in localGP (record inputs, but only record condsim whitenoise once per tag per level).

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20260320
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20260320
   - input masks: https://github.com/argovis/localGP_masks/releases/tag/OP20260110
 - data origin: https://doi.org/10.17882/42182#125185
