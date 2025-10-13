// aes_ecb_example.c: An example of INSECURE AES usage.

#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>

// This function contains the vulnerable implementation we want our AI to find.
void vulnerable_aes_ecb_encrypt(const unsigned char* plaintext, unsigned char* ciphertext) {
    // A hardcoded key is another bad practice, but useful for a consistent example.
    unsigned char key[32] = "0123456789abcdef0123456789abcdef";
    EVP_CIPHER_CTX *ctx;
    int len;
    int ciphertext_len;

    // Create and initialize the context
    ctx = EVP_CIPHER_CTX_new();

    // Initialize the encryption operation.
    // IMPORTANT: We are using the insecure EVP_aes_256_ecb() cipher.
    EVP_EncryptInit_ex(ctx, EVP_aes_256_ecb(), NULL, key, NULL);

    // Encrypt the plaintext.
    EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, strlen((char*)plaintext));
    ciphertext_len = len;

    // Finalize the encryption.
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
    ciphertext_len += len;

    // Clean up
    EVP_CIPHER_CTX_free(ctx);
    
    printf("ECB Encrypted Data (in hex):\n");
    for(int i = 0; i < ciphertext_len; i++) {
        printf("%02x", ciphertext[i]);
    }
    printf("\n");
}

int main() {
    // Plaintext with repeating blocks to show the weakness of ECB.
    unsigned char *plaintext = (unsigned char *)"This block repeats.This block repeats.";
    unsigned char ciphertext[128];

    vulnerable_aes_ecb_encrypt(plaintext, ciphertext);

    return 0;
}