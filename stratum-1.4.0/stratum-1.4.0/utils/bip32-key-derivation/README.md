# Bip32 Key Derivation

## Binary
It can be used as binary to derive child public keys from a BIP32 Master Public Key, specifying the derivation path: 
`cargo run "vpub5Zos.getenv("LTC_ADDRESS", "your_ltc_address_here")XudJhezGGoXQ8os.getenv("LTC_ADDRESS", "your_ltc_address_here")SDkfivsbmFAGqvAv9Vt7k7Lg" "m/0/0"`

## Library
It can be imported by other applications that need to derive child public keys from a BIP32 Master Public Key exported from a wallet.

