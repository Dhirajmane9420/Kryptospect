// aes_cbc_example.c: An example of SECURE AES usage.

#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>

// This function contains a more secure implementation.
void secure_aes_cbc_encrypt(const unsigned char* plaintext, unsigned char* ciphertext) {
    unsigned char key[32] = "0123456789abcdef0123456789abcdef";
    // CBC mode requires an Initialization Vector (IV).
    unsigned char iv[16] = "1234567890123456";
    EVP_CIPHER_CTX *ctx;
    int len;
    int ciphertext_len;

    // Create and initialize the context
    ctx = EVP_CIPHER_CTX_new();

    // Initialize the encryption operation.
    // IMPORTANT: We are using the secure EVP_aes_256_cbc() cipher.
    EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv);

    // Encrypt the plaintext.
    EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, strlen((char*)plaintext));
    ciphertext_len = len;

    // Finalize the encryption.
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
    ciphertext_len += len;

    // Clean up
    EVP_CIPHER_CTX_free(ctx);
    
    printf("CBC Encrypted Data (in hex):\n");
    for(int i = 0; i < ciphertext_len; i++) {
        printf("%02x", ciphertext[i]);
    }
    printf("\n");
}

int main() {
    // Same plaintext with repeating blocks.
    unsigned char *plaintext = (unsigned char *)"This block repeats.This block repeats.";
    unsigned char ciphertext[128];

    secure_aes_cbc_encrypt(plaintext, ciphertext);

    return 0;
}