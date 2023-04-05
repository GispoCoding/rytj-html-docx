
Install Jekyll: https://idroot.us/install-jekyll-ubuntu-22-04/
Install Python packages: pip install -r requirements.txt

Unless you cloned using --recurse-submodules
git submodule init
git submodule update
pushd ry-tietomallit/docs
jekyll build
popd

./convert.py

