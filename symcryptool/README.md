# About This Tool

This tool is designed to securely encrypt and decrypt files using a custom encryption key. 
It’s perfect for protecting sensitive information and ensuring that only authorized users can access it. 
Here’s a quick rundown of what it can do:

- Generate Keys: Create unique encryption keys for securing your files
- Encrypt Files: Secure any file by converting it into an encrypted version with the .enc extension, keeping the original file intact
- Decrypt Files: Restore encrypted files to their original state using the correct key
- User-Friendly Commands: Easily specify files, keys, and actions (encrypt or decrypt)



# Warnings and Considerations

- Key Management:
Always store your encryption keys securely - Losing the key means you won’t be able to decrypt your files.
Avoid sharing your key over insecure channels.

- File Compatibility:
The tool won’t encrypt files that already have the .enc extension and won’t decrypt files without it. Double-check file types before running commands.

- Overwrite Risks:
The tool generates new files for both encryption and decryption. However, if a file with the same name already exists in the directory, it may be overwritten.

- Sensitive Data:
Be cautious when encrypting critical system files or files necessary for running other applications. Missteps could lead to inaccessible or corrupted files.

- Encryption Security:
This tool uses the cryptography library's Fernet module, which provides strong symmetric encryption. However, always follow best practices for key rotation and data management.
