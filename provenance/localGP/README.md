# localGP input run records

Production candidate runs have critical provenance data recorded here.

## OP20250808* series

Argonc -> localGP runs from the following environment:

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250808
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250814* series

Almost identical to OP20250808* except realtime data is never accepted.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250814
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250825* series

Similar to OP20250814*, with corrections for temperature units (all temperatures in celsius when used for calculating downstream variables, converted to kelvin for temperature integrals only)

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250825
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
 - data origin: https://www.seanoe.org/data/00311/42182/#116315

## OP20250825b* series

Allows realtime data like OP20250808* while managing temperature units like OP20250825*.

 - python env: https://github.com/argovis/ocean_pipeline/blob/main/provenance/environments/python-dev-env.txt
 - ocean-pipeline
   - tag: https://github.com/argovis/ocean_pipeline/releases/tag/OP20250825b
 - localGP
   - tag: https://github.com/argovis/localGP/releases/tag/OP20250808
 - data origin: https://www.seanoe.org/data/00311/42182/#116315
