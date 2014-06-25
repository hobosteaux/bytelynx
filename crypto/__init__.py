from crypto.aesgcm import AESCrypto as AESCrypto
from crypto.diffiehellman import DHCrypto as DHCrypto

MODULES = {'bytelynx': DHCrypto,
           'aes-dht': AESCrypto,
           'aes-net': AESCrypto}
