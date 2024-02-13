# rris40DataViewer
Python source code for [RRIS40 dataset](https://koonyook.github.io/rris40/) playback with 2D marker projection.

## To run the code
1. If you already have a preferred python 3.7 environment, activate your environment and skip to step 3.
2. Install Anaconda, open Anaconda prompt, and create a new python environment with commmand.
```
conda create -n py37v python=3.7
```
Then, activate the environment.
```
conda activate py37v
```
3. Install openCV and numpy.
```
pip install opencv-python numpy
```
4. Modify viewer.py by changing these two lines of code
```
recordFolder=r'C:\rris40data\FT027g\2021-10-01-09-48-29'    #please edit this line to point to the extracted folder.
cameraIndex=2      #select a number (0-7)
```
5. Run it
```
python viewer.py
```
6. To quit, just press Esc.
