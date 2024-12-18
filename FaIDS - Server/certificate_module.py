import os
from OpenSSL import crypto
from logging_module import log
import uuid

def generate_self_signed_certificate(cert_path, key_path,country="US", state="California", locality="San Francisco",
                                     org="My Company", org_unit="My Organization", common_name="localhost"):
    """
    Generates a self-signed certificate and writes it to files.

    Args:
        country (str): Country Name (C)
        state (str): State or Province Name (ST)
        locality (str): Locality Name (L)
        org (str): Organization Name (O)
        org_unit (str): Organizational Unit Name (OU)
        common_name (str): Common Name (CN)

    Returns:
        tuple: Paths to the generated key and certificate files.
    """
    try:
        # Create a key pair
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 4096)

        # Create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = country
        cert.get_subject().ST = state
        cert.get_subject().L = locality
        cert.get_subject().O = org
        cert.get_subject().OU = org_unit
        cert.get_subject().CN = common_name
        cert.set_serial_number(int(uuid.uuid4().int >> 64))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)  # 10 years
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')
    except Exception as error:
        log(f"ERROR-CM-GSSC-00-01-01: {error}", 4)
        log("Unexpected error on generating self-signed certificate.", 1)
        return False
    
    try:
    
        with open(key_path, "wb") as key_file:
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        with open(cert_path, "wb") as cert_file:
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        return key_path, cert_path
    except Exception as error:
        log(f"ERROR-CM-GSSC-00-02-01: {error}", 4)
        log("Unexpected error on writing certificate to file.", 1)
        return False

def create_certificate(cert_path, key_path):
    """
    Prompts the user for certificate details and generates a self-signed certificate.

    Returns:
        tuple: Paths to the generated key and certificate files.
    """
    certificate_inputs = ["country", "state", "locality", "org", "org_unit", "common_name"]
    certificate_defaults = ["US", "California", "San Francisco", "My Company", "My Organization", "localhost"]
    certificate_values = []

    for i, input_name in enumerate(certificate_inputs):
        input_value = input(f"{input_name.capitalize().replace('_', ' ')} [{certificate_defaults[i]}]: ")
        # Use the provided input or fallback to the default value
        certificate_values.append(input_value if input_value else certificate_defaults[i])
    
    # Pass the collected values to the certificate generation function
    return generate_self_signed_certificate(cert_path, key_path,*certificate_values)

def has_certificate_expired(cert_path):
    with open(cert_path, "rb") as cert_file:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())
    return cert.has_expired()

def read_certificate(cert_path):
    with open(cert_path, "rb") as cert_file:
        cert_data = cert_file.read()

    # Load the certificate
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)

    # Print certificate details
    print("Subject:", cert.get_subject())
    print("Issuer:", cert.get_issuer())
    print("Serial Number:", cert.get_serial_number())
    print("Validity Period:")
    print("    Not Before:", cert.get_notBefore().decode("utf-8"))
    print("    Not After:", cert.get_notAfter().decode("utf-8"))
    print("Public Key Type:", cert.get_pubkey().type())

def certificate_handler(cert_dir="certificates"):
    os.makedirs(cert_dir, exist_ok=True)
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")

    try:
        if not (os.path.exists(cert_path) and os.path.exists(key_path)) or has_certificate_expired(cert_path):
            log("Certificate has expired or doesn't exist. Creating a new one.", 2)
            try:
                key_path, cert_path = create_certificate()
            except ValueError as error:
                key_path, cert_path = False, False
        if key_path and cert_path:
            log("Successfully loaded certificates.", 3)
            read_certificate(cert_path)
            return key_path, cert_path
        else:
            log("Certificate loading failed.", 1)
            return False
    except Exception as error:
        log(f"ERROR-CM-CH-00-01-01: {error}", 4)
        log("Unexpected error occured on applying certificate.", 1)
        return False
