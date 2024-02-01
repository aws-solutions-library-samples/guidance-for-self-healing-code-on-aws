set -e
rm -rf .build
mkdir -p .build
cd .build

# Create virtualenv and activate
echo "Creating virtualenv"
python3 -m venv log-driven-bug-fixer-build
python --version
source log-driven-bug-fixer-build/bin/activate

# Install Python dependencies
mkdir -p package
echo "Installing Python dependencies into deployment package"
pip install -q -r ../src/requirements.txt -t package --upgrade
rm -rf package/numpy* package/pydantic*
pip install --platform manylinux2014_x86_64 --target package --python-version 3.11 --only-binary=:all: numpy pydantic
deactivate

# Copy source code
echo "Copying source code into deployment package"
rsync -av --exclude '__pycache__/' ../src/ package/
