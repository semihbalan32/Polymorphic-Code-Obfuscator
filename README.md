# Polymorphic-Code-Obfuscator
hide your code 
📦 Install Dependencies

Copy

bash
pip install astor

🔧 How to Use
1. Make the script executable

Copy
bash
chmod +x pyobfuscate.py

2. Run from CLI

Copy
bash
# Basic usage
python pyobfuscate.py license.py

# Specify output file
python pyobfuscate.py license.py license_obfuscated.py

# Force overwrite
python pyobfuscate.py license.py -o

# Show debug info
python pyobfuscate.py license.py --debug

📝 Output Example

Copy
bash
$ python pyobfuscate.py example.py
Obfuscated code saved to: example.obfuscated.py
The obfuscated file will contain:

Random variable names
Encrypted strings with XOR decryption
Dead code blocks
A decrypt() function at the top
