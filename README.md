# Transportation Layers for Wildfire Containment Modeling
## Overview:
#### This repository contains a tool designed for wildfire researchers.  These tools facilitate the creation of transportation lines such as roads, railroads, and trails, aiding in the evaluation and improvement of wildfire treatment outcome modeling.
####*These scripts and its accompanying directory should be downloaded onto a local drive. The user can then open an ArcGIS Pro 3.X project and direct the ArcCatalog to the files. The accompanying ArcToolbox that uses the scripts can be found in the Tool folder.*

### Description: 
Description: This tool takes USGS transportation features, as well as USFS core road data, and processes them to remove duplicates. This includes a process to remove "nearly identical" roads (lines) that USGS and USFS roads layers contain.
USGS and USFS roads have different lines with slightly different vertices that represent the same road. This script removes exact duplicates, and then uses a (X) meter buffer (default in tool is currently 50) to remove these duplicates.
Often this buffered clip of USFS roads still leaves small sections of line that falls right outside of the buffer and therefor, a query identifies line segments in the clipped USFS roads layer that are smaller than 100m and deletes them.
Width for roads and trails will need to be updated by users in the script. For this script, the width was calculated using randomly sampled sections of line to calculate a rounded mean width.

### General Workflow:
Data Acquisition: The user needs to provide fire perimeter or other AOI polygon in the form of a feature class. 
The user will also need to download USFS road data locally which can be obtained here: https://data.fs.usda.gov/geodata/edw/datasets.php?xmlKeyword=roadcore
Additionally, the USGS Trails Rails and Roads line type feature class needs to be downloaded: https://apps.nationalmap.gov/downloader/      > Transportation > File Geodatabase
*Make sure these inputs use the same coordinate system
Processing: Once the tool has been downloaded and unzipped, using the ArcGIS Pro software, the user needs to have a map open, and link the tool's directory to the Catalog. Using Catalog, the user can then open the tool by opening the tool directory > roadrailtrail.atbx > Processing USGS USFS Transportation Lines For Containment Modeling
The user can now drag and drop the fire perimeter polygon feature(s), USGS Rail features, USGS Trail features, USGS Road features, and the USFS Road features. The user can leave the QAQC processing parameters at the default, or adjust them if needed.
After running, the output will be in the form of one feature class in the output.gdb

### Limitations:
ArcGIS Pro Version: Users must have ArcGIS Pro version 3 or higher. The tools are designed to work within the functionalities of this software version and may not be compatible with earlier versions.
File Directory Structure: Proper formatting and naming of the file directory are crucial. 
Users must ensure that the directory structure and file naming conventions are correctly set up as per the toolkit's requirements. This is essential for the smooth operation and integration of the different tools in the toolkit.

For more information regarding transportation infrastructure on containment effectiveness please refer to the following research article:
[Forest Roads and Operational Wildfire Response Planning](https://cfri.colostate.edu/wp-content/uploads/sites/22/2021/02/Thompson-Gannon-Caggiano-Forest-Roads-and-Operational-Wildfire-Response-Planning.pdf "Forest Roads and Operational Wildfire Response Planning")

### Contributions:
This toolkit represents an ongoing effort to enhance fire management strategies through data-driven analysis, and community contributions are vital for its continuous improvement. Please note that the creators of this toolkit are not professional coders, and therefore, errors may present themselves in the code.  We actively encourage the community to contribute towards optimizing and improving the code. If you have suggestions for enhancements, identify bugs, or find ways to streamline the processes to reduce unnecessary outputs, your input is greatly appreciated. Your expertise and insights are invaluable in refining this toolkit to better serve the needs of the wildfire research and management community. Please reach out with your contributions, feedback, or suggestions to Alexander Arkowitz at aarkowitz@gmail.com or alexander.arkowitz@colostate.edu or log an issue on GitHub.

### Author Information:
Alexander Arkowitz, Geospatial Wildfire Research Associate IV, Colorado State University. Contractor, USFS Rocky Mountain Research Station
Email: aarkowitz@gmail.com, alexander.arkowitz@colostate.edu
Leo Oniell, USFS
Email: christopher.oneill@usda.gov

### Acknowledgements:
Gratitude extends to Ben Gannon for his expertise in wildfire data processing methods.
