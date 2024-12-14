import os
import argparse
from cryptography.fernet import Fernet

parser = argparse.ArgumentParser(description=r"""

_________                                   __                .__   
\_   ___ \_______ ___.__.______           _/  |_  ____   ____ |  |  
/    \  \/\_  __ <   |  |\____ \   ______ \   __\/  _ \ /  _ \|  |  
\     \____|  | \/\___  ||  |_> > /_____/  |  | (  <_> |  <_> )  |__
 \______  /|__|   / ____||   __/           |__|  \____/ \____/|____/
        \/        \/     |__|                                       


Usage:
                    py SCRIPT.py -f FILE -k KEY -e/d

Flags:
-c  --create_key    Create a new encryption key and save it as a new file.

-f  --files         Specify the file you want to encrypt or decrypt.
                    Note: Does not encrypt .enc files and only decrypts .enc files.

-e  --encrypt       Use -e to encrypt the specified file with the selected key file.
                    Note: An encrypted copy with the extension The fileAME.EXTENSION.enc will be created in the current directory.

-d  --decrypt       Use -d to decrypt the specified file with the selected key file.
                    Note: A decrypted copy with the The fileame decrypted_The fileAME.EXTENSION will be created in the current directory.

-k  --key           Specify the key file you want to use for encryption or decryption.

                                 
Examples of correct usage:
Create a new key:    py cryptool.py -c new_key.key

Encrypt a file:      py cryptool.py -f testfile.txt -k test.key -e

Decrypt a file:      py cryptool.py -f testfile.txt.enc -k test.key -d""", 
epilog="See information above", formatter_class=argparse.RawDescriptionHelpFormatter)   

def generate_key_mode(name_key_in_gkm):
    newkey = Fernet.generate_key()
    with open(name_key_in_gkm, "wb") as key_file:
        key_file.write(newkey)

def encrypt_and_store_info(file, key):
    with open(key, "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)

    with open(file, "rb") as file_to_encrypt:                      
        content = file_to_encrypt.read()
        cipher_content = cipher_suite.encrypt(content)
        
        encrypted_file = file + ".enc"
        with open(encrypted_file, "wb") as file_to_encrypt:
            file_to_encrypt.write(cipher_content)

def decrypt_and_store_info(file, key):
    with open(key, "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)

    with open(file, "rb") as file_to_decrypt:                      
        content = file_to_decrypt.read()
        cipher_content = cipher_suite.decrypt(content)
        
        decrypted_file = "decrypted_" + file.replace(".enc", "")
        with open(decrypted_file, "wb") as file_to_decrypt:
            file_to_decrypt.write(cipher_content)

def main():

    parser.add_argument("-c", "--create_key", metavar="Create new key", help="Create a new encryption key")
    parser.add_argument("-f", "--file", metavar="Choose: File", type=str, help="Choose file to encrypt or decrypt") 
    parser.add_argument("-k", "--key", metavar="Choose: Key", type=str, help="Choose key-file to encrypt or decrypt file") 

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-e", "--encrypt", action="store_true", help="Choose for encryption")
    group.add_argument("-d", "--decrypt", action="store_true", help="Choose for decryption")

    args = parser.parse_args()

    if len(os.sys.argv) == 1:
        parser.print_help()
        return

    if args.create_key:
        if not os.path.exists(args.create_key):
            generate_key_mode(args.create_key)
            print(f"Key {args.create_key} created.")
        else:
            print(f"Key {args.create_key} already exists.")

    if (args.file and args.key) and not (args.encrypt or args.decrypt):
        print("Error: You need to specify the encryption mode '-e' or '-d'.")
        return

    if args.file and (args.decrypt or args.encrypt):
        if not os.path.exists(args.file):
            print(f"File {args.file} does not exist.")
            return
        excisting_file = args.file
    else:
        print("Error: Choose a file. Choose '-f' and file.")
        return

    if args.key and (args.decrypt or args.encrypt):
        if not os.path.exists(args.key):
            print(f"Keyfile {args.key}finns ej.")
            return
        excisting_key = args.key
    else:
        print("Error: Key file missing. Choose '-k' and key-file.")
        return
             

    if args.encrypt:
        if excisting_file.endswith(".enc"):
            print(f"The file {excisting_file} is already encrypted.")
        else:
            encrypt_and_store_info(excisting_file, excisting_key)
            print(f"The file {excisting_file} is encrypted.")
        
    if  args.decrypt:
        if not excisting_file.endswith(".enc"):
            print(f"The file {excisting_file} is already decrypted.")
        else:
            decrypt_and_store_info(excisting_file, excisting_key)
            print(f"The file {excisting_file} is decrypted.")


if __name__ == "__main__":
    main()
