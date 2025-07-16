# DQM Global module template generator

This project creates the DQM global template used for positioning the modules in the [HGCal DQM](https://gitlab.cern.ch/hgcal-dpg/hgcal-comm).

It consists of a python script which reads a ModMap from [HGCal Integrations ModMap](https://gitlab.cern.ch/hgcal-integration/hgcal_modmap.git) project, and generates a ROOT file which is used in the DQM for HGCal.

The input files are organized in the Gemoetry subdirectory by version (note the file name also reflects the version), and the output files are generated in the outputs subdirectory organized by version as well. 

## Instalation
```bash
git clone https://github.com/MijaToka/DQM_Global_Module_Template.git
```
## Instructions
To run the code, go into the root direcory of the repository and run:
```bash
python3 HGCalModMapTemplateGen.py [-h] [--version VERSION] [--layer_preview]
```
### Python dependencies
- ROOT
- NumPy
- Pandas
