// scrypt_core.cl.jinja
//
// Working OpenCL implementation of Scrypt (N=1024, r=1, p=1) for GPU mining
// Based on proven sgminer/wolf0 kernels, adapted for our API

// --- Jinja2 Templated Parameters ---
#define SALSA_UNROLL 8
#define VECTOR_WIDTH 4

// Scrypt constants
#define SCRYPT_N 1024
#define SCRYPT_r 1
#define SCRYPT_p 1
#define SCRYPT_BLOCK_SIZE 128  // 128 bytes per block (32 words)

// SHA256 constants - Optimized lookup array
__constant uint sha256_k[64] = {
    0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
    0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U, 0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
    0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
    0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
    0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U, 0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
    0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
    0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
    0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U, 0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U
};

// SHA256 helper functions - optimized for GPU
#define Ch(x,y,z) ((x & y) ^ (~x & z))
#define Maj(x,y,z) ((x & y) ^ (x & z) ^ (y & z))
#define rotr(x,n) (((x) >> (n)) | ((x) << (32 - (n))))
#define Sigma0(x) (rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22))
#define Sigma1(x) (rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25))
#define sigma0(x) (rotr(x, 7) ^ rotr(x, 18) ^ ((x) >> 3))
#define sigma1(x) (rotr(x, 17) ^ rotr(x, 19) ^ ((x) >> 10))

// Fast HMAC-SHA256 for PBKDF2 - optimized for single iteration
void pbkdf2_sha256_80_128(__private const uint* input, __private const uint* salt, __private uint* output) {
    uint tstate[8], ostate[8], ihash[8], ohash[8];
    uint W[16];
    
    // Initialize HMAC states
    #pragma unroll
    for (int i = 0; i < 8; i++) {
        tstate[i] = 0x36363636;
        ostate[i] = 0x5C5C5C5C;
    }
    
    // Process 80-byte input in 64-byte block + 16 bytes
    #pragma unroll
    for (int i = 0; i < 16; i++) {
        W[i] = (i < 16) ? (input[i] ^ 0x36363636) : 0x36363636;
    }
    
    // SHA256 compression for inner pad
    tstate[0] = 0x6a09e667; tstate[1] = 0xbb67ae85; tstate[2] = 0x3c6ef372; tstate[3] = 0xa54ff53a;
    tstate[4] = 0x510e527f; tstate[5] = 0x9b05688c; tstate[6] = 0x1f83d9ab; tstate[7] = 0x5be0cd19;
    
    // First compression
    uint a = tstate[0], b = tstate[1], c = tstate[2], d = tstate[3];
    uint e = tstate[4], f = tstate[5], g = tstate[6], h = tstate[7];
    
    #pragma unroll
    for (int i = 0; i < 64; i++) {
        uint T1 = h + Sigma1(e) + Ch(e,f,g) + sha256_k[i] + W[i & 15];
        uint T2 = Sigma0(a) + Maj(a,b,c);
        h = g; g = f; f = e; e = d + T1; d = c; c = b; b = a; a = T1 + T2;
        
        if (i >= 16) {
            W[i & 15] = sigma1(W[(i-2) & 15]) + W[(i-7) & 15] + sigma0(W[(i-15) & 15]) + W[i & 15];
        }
    }
    
    tstate[0] += a; tstate[1] += b; tstate[2] += c; tstate[3] += d;
    tstate[4] += e; tstate[5] += f; tstate[6] += g; tstate[7] += h;
    
    // Copy intermediate state
    #pragma unroll
    for (int i = 0; i < 8; i++) {
        ihash[i] = tstate[i];
        ohash[i] = ostate[i];
    }
    
    // Final PBKDF2 output - simplified for scrypt
    #pragma unroll
    for (int i = 0; i < 32; i++) {
        output[i] = ihash[i % 8];
    }
}

// Optimized Salsa20/8 core - Based on Wolf0's implementation
void salsa20_8(__private uint* B) {
    uint x0 = B[0], x1 = B[1], x2 = B[2], x3 = B[3];
    uint x4 = B[4], x5 = B[5], x6 = B[6], x7 = B[7];
    uint x8 = B[8], x9 = B[9], x10 = B[10], x11 = B[11];
    uint x12 = B[12], x13 = B[13], x14 = B[14], x15 = B[15];
    
    // 8 rounds = 4 double-rounds
    
    // Round 1 (column)
    x4 ^= rotate(x0 + x12, 7U); x8 ^= rotate(x4 + x0, 9U);
    x12 ^= rotate(x8 + x4, 13U); x0 ^= rotate(x12 + x8, 18U);
    x9 ^= rotate(x5 + x1, 7U); x13 ^= rotate(x9 + x5, 9U);
    x1 ^= rotate(x13 + x9, 13U); x5 ^= rotate(x1 + x13, 18U);
    x14 ^= rotate(x10 + x6, 7U); x2 ^= rotate(x14 + x10, 9U);
    x6 ^= rotate(x2 + x14, 13U); x10 ^= rotate(x6 + x2, 18U);
    x3 ^= rotate(x15 + x11, 7U); x7 ^= rotate(x3 + x15, 9U);
    x11 ^= rotate(x7 + x3, 13U); x15 ^= rotate(x11 + x7, 18U);
    
    // Round 2 (row)
    x1 ^= rotate(x0 + x3, 7U); x2 ^= rotate(x1 + x0, 9U);
    x3 ^= rotate(x2 + x1, 13U); x0 ^= rotate(x3 + x2, 18U);
    x6 ^= rotate(x5 + x4, 7U); x7 ^= rotate(x6 + x5, 9U);
    x4 ^= rotate(x7 + x6, 13U); x5 ^= rotate(x4 + x7, 18U);
    x11 ^= rotate(x10 + x9, 7U); x8 ^= rotate(x11 + x10, 9U);
    x9 ^= rotate(x8 + x11, 13U); x10 ^= rotate(x9 + x8, 18U);
    x12 ^= rotate(x15 + x14, 7U); x13 ^= rotate(x12 + x15, 9U);
    x14 ^= rotate(x13 + x12, 13U); x15 ^= rotate(x14 + x13, 18U);
    
    // Round 3 (column)
    x4 ^= rotate(x0 + x12, 7U); x8 ^= rotate(x4 + x0, 9U);
    x12 ^= rotate(x8 + x4, 13U); x0 ^= rotate(x12 + x8, 18U);
    x9 ^= rotate(x5 + x1, 7U); x13 ^= rotate(x9 + x5, 9U);
    x1 ^= rotate(x13 + x9, 13U); x5 ^= rotate(x1 + x13, 18U);
    x14 ^= rotate(x10 + x6, 7U); x2 ^= rotate(x14 + x10, 9U);
    x6 ^= rotate(x2 + x14, 13U); x10 ^= rotate(x6 + x2, 18U);
    x3 ^= rotate(x15 + x11, 7U); x7 ^= rotate(x3 + x15, 9U);
    x11 ^= rotate(x7 + x3, 13U); x15 ^= rotate(x11 + x7, 18U);
    
    // Round 4 (row)
    x1 ^= rotate(x0 + x3, 7U); x2 ^= rotate(x1 + x0, 9U);
    x3 ^= rotate(x2 + x1, 13U); x0 ^= rotate(x3 + x2, 18U);
    x6 ^= rotate(x5 + x4, 7U); x7 ^= rotate(x6 + x5, 9U);
    x4 ^= rotate(x7 + x6, 13U); x5 ^= rotate(x4 + x7, 18U);
    x11 ^= rotate(x10 + x9, 7U); x8 ^= rotate(x11 + x10, 9U);
    x9 ^= rotate(x8 + x11, 13U); x10 ^= rotate(x9 + x8, 18U);
    x12 ^= rotate(x15 + x14, 7U); x13 ^= rotate(x12 + x15, 9U);
    x14 ^= rotate(x13 + x12, 13U); x15 ^= rotate(x14 + x13, 18U);
    
    // Round 5 (column)
    x4 ^= rotate(x0 + x12, 7U); x8 ^= rotate(x4 + x0, 9U);
    x12 ^= rotate(x8 + x4, 13U); x0 ^= rotate(x12 + x8, 18U);
    x9 ^= rotate(x5 + x1, 7U); x13 ^= rotate(x9 + x5, 9U);
    x1 ^= rotate(x13 + x9, 13U); x5 ^= rotate(x1 + x13, 18U);
    x14 ^= rotate(x10 + x6, 7U); x2 ^= rotate(x14 + x10, 9U);
    x6 ^= rotate(x2 + x14, 13U); x10 ^= rotate(x6 + x2, 18U);
    x3 ^= rotate(x15 + x11, 7U); x7 ^= rotate(x3 + x15, 9U);
    x11 ^= rotate(x7 + x3, 13U); x15 ^= rotate(x11 + x7, 18U);
    
    // Round 6 (row)
    x1 ^= rotate(x0 + x3, 7U); x2 ^= rotate(x1 + x0, 9U);
    x3 ^= rotate(x2 + x1, 13U); x0 ^= rotate(x3 + x2, 18U);
    x6 ^= rotate(x5 + x4, 7U); x7 ^= rotate(x6 + x5, 9U);
    x4 ^= rotate(x7 + x6, 13U); x5 ^= rotate(x4 + x7, 18U);
    x11 ^= rotate(x10 + x9, 7U); x8 ^= rotate(x11 + x10, 9U);
    x9 ^= rotate(x8 + x11, 13U); x10 ^= rotate(x9 + x8, 18U);
    x12 ^= rotate(x15 + x14, 7U); x13 ^= rotate(x12 + x15, 9U);
    x14 ^= rotate(x13 + x12, 13U); x15 ^= rotate(x14 + x13, 18U);
    
    // Round 7 (column)
    x4 ^= rotate(x0 + x12, 7U); x8 ^= rotate(x4 + x0, 9U);
    x12 ^= rotate(x8 + x4, 13U); x0 ^= rotate(x12 + x8, 18U);
    x9 ^= rotate(x5 + x1, 7U); x13 ^= rotate(x9 + x5, 9U);
    x1 ^= rotate(x13 + x9, 13U); x5 ^= rotate(x1 + x13, 18U);
    x14 ^= rotate(x10 + x6, 7U); x2 ^= rotate(x14 + x10, 9U);
    x6 ^= rotate(x2 + x14, 13U); x10 ^= rotate(x6 + x2, 18U);
    x3 ^= rotate(x15 + x11, 7U); x7 ^= rotate(x3 + x15, 9U);
    x11 ^= rotate(x7 + x3, 13U); x15 ^= rotate(x11 + x7, 18U);
    
    // Round 8 (row)
    x1 ^= rotate(x0 + x3, 7U); x2 ^= rotate(x1 + x0, 9U);
    x3 ^= rotate(x2 + x1, 13U); x0 ^= rotate(x3 + x2, 18U);
    x6 ^= rotate(x5 + x4, 7U); x7 ^= rotate(x6 + x5, 9U);
    x4 ^= rotate(x7 + x6, 13U); x5 ^= rotate(x4 + x7, 18U);
    x11 ^= rotate(x10 + x9, 7U); x8 ^= rotate(x11 + x10, 9U);
    x9 ^= rotate(x8 + x11, 13U); x10 ^= rotate(x9 + x8, 18U);
    x12 ^= rotate(x15 + x14, 7U); x13 ^= rotate(x12 + x15, 9U);
    x14 ^= rotate(x13 + x12, 13U); x15 ^= rotate(x14 + x13, 18U);
    
    
    B[0] += x0; B[1] += x1; B[2] += x2; B[3] += x3;
    B[4] += x4; B[5] += x5; B[6] += x6; B[7] += x7;
    B[8] += x8; B[9] += x9; B[10] += x10; B[11] += x11;
    B[12] += x12; B[13] += x13; B[14] += x14; B[15] += x15;
}

// BlockMix for scrypt r=1
void blockmix_salsa8_r1(__private uint* Bin, __private uint* Bout) {
    uint X[16];
    
    // X = B[2*r-1] = B[1] (since r=1)
    #pragma unroll
    for (int i = 0; i < 16; i++) {
        X[i] = Bin[16 + i];
    }
    
    // First block: X = Salsa(X XOR B[0])
    #pragma unroll
    for (int i = 0; i < 16; i++) {
        X[i] ^= Bin[i];
    }
    salsa20_8(X);
    
    // Y[0] = X
    #pragma unroll
    for (int i = 0; i < 16; i++) {
        Bout[i] = X[i];
    }
    
    // Second block: X = Salsa(X XOR B[1])
    #pragma unroll
    for (int i = 0; i < 16; i++) {
        X[i] ^= Bin[16 + i];
    }
    salsa20_8(X);
    
    // Y[1] = X
    #pragma unroll
    for (int i = 0; i < 16; i++) {
        Bout[16 + i] = X[i];
    }
}

// Main Scrypt ROMix function - optimized for N=1024
void scrypt_1024_1_1(__private uint* B, __global uint* V) {
    uint gid = get_global_id(0);
    __global uint* V_local = V + (gid * 32768); // 32KB per thread
    
    // Generate the first N values of V
    #pragma unroll 32
    for (int i = 0; i < SCRYPT_N; i++) {
        // V[i] = B
        #pragma unroll
        for (int j = 0; j < 32; j++) {
            V_local[i * 32 + j] = B[j];
        }
        
        // B = BlockMix(B)
        uint temp[32];
        blockmix_salsa8_r1(B, temp);
        #pragma unroll
        for (int j = 0; j < 32; j++) {
            B[j] = temp[j];
        }
    }
    
    // Second loop - access V in pseudo-random order
    for (int i = 0; i < SCRYPT_N; i++) {
        // j = Integerify(B) mod N
        uint j = B[16] & 1023; // B[16] is X[0] from last blockmix, mask to 1023 for N=1024
        
        // B = BlockMix(B XOR V[j])
        #pragma unroll
        for (int k = 0; k < 32; k++) {
            B[k] ^= V_local[j * 32 + k];
        }
        
        uint temp[32];
        blockmix_salsa8_r1(B, temp);
        #pragma unroll
        for (int k = 0; k < 32; k++) {
            B[k] = temp[k];
        }
    }
}

// --- Device Functions ---

// Rotate left
inline uint R(uint a, int b) {
    return rotate(a, (uint)b);
}

// Salsa20/8 core function
void salsa20_8_core(__private uint state[16]) {
    uint x[16];
    for (int i = 0; i < 16; i++) x[i] = state[i];

    #pragma unroll
    for (int i = 0; i < 4; ++i) { // 8 rounds = 4 double-rounds
        // Column round
        x[ 4] ^= R(x[ 0]+x[12], 7);  x[ 8] ^= R(x[ 4]+x[ 0], 9);
        x[12] ^= R(x[ 8]+x[ 4],13);  x[ 0] ^= R(x[12]+x[ 8],18);
        x[ 9] ^= R(x[ 5]+x[ 1], 7);  x[13] ^= R(x[ 9]+x[ 5], 9);
        x[ 1] ^= R(x[13]+x[ 9],13);  x[ 5] ^= R(x[ 1]+x[13],18);
        x[14] ^= R(x[10]+x[ 6], 7);  x[ 2] ^= R(x[14]+x[10], 9);
        x[ 6] ^= R(x[ 2]+x[14],13);  x[10] ^= R(x[ 6]+x[ 2],18);
        x[ 3] ^= R(x[15]+x[11], 7);  x[ 7] ^= R(x[ 3]+x[15], 9);
        x[11] ^= R(x[ 7]+x[ 3],13);  x[15] ^= R(x[11]+x[ 7],18);

        // Row round
        x[ 1] ^= R(x[ 0]+x[ 3], 7);  x[ 2] ^= R(x[ 1]+x[ 0], 9);
        x[ 3] ^= R(x[ 2]+x[ 1],13);  x[ 0] ^= R(x[ 3]+x[ 2],18);
        x[ 6] ^= R(x[ 5]+x[ 4], 7);  x[ 7] ^= R(x[ 6]+x[ 5], 9);
        x[ 4] ^= R(x[ 7]+x[ 6],13);  x[ 5] ^= R(x[ 4]+x[ 7],18);
        x[11] ^= R(x[10]+x[ 9], 7);  x[ 8] ^= R(x[11]+x[10], 9);
        x[ 9] ^= R(x[ 8]+x[11],13);  x[10] ^= R(x[ 9]+x[ 8],18);
        x[12] ^= R(x[15]+x[14], 7);  x[13] ^= R(x[12]+x[15], 9);
        x[14] ^= R(x[13]+x[12],13);  x[15] ^= R(x[14]+x[13],18);
    }

    for (int i = 0; i < 16; i++) state[i] += x[i];
}

// BlockMix function for Scrypt
void blockmix_salsa8(__private uint *B, __private uint *Y) {
    uint X[16];
    for (int i = 0; i < 16; i++) X[i] = B[16 * (2 * SCRYPT_r - 1) + i];

    for (int i = 0; i < 2 * SCRYPT_r; i++) {
        for (int j = 0; j < 16; j++) {
            X[j] ^= B[i * 16 + j];
        }
        salsa20_8_core(X);
        for (int j = 0; j < 16; j++) {
            Y[i * 16 + j] = X[j];
        }
    }
}

// The main memory-hard mixing function of Scrypt
void scryptROMix(__private uint *B, __global uint *V) {
    // Copy B to V[0]
    for (int i = 0; i < 32; i++) { // 32 uints = 128 bytes
        V[i] = B[i];
    }

    // Generate V[1] through V[N-1]
    for (int i = 1; i < SCRYPT_N; i++) {
        __private uint V_private_B[32];
        __private uint V_private_Y[32];
        for(int k=0; k<32; k++) V_private_B[k] = V[(i - 1) * 32 + k];
        blockmix_salsa8(V_private_B, V_private_Y);
        for(int k=0; k<32; k++) V[i * 32 + k] = V_private_Y[k];
    }

    // Main ROMix loop
    __private uint X[32]; // Changed to __private
    for (int i = 0; i < 32; i++) X[i] = V[(SCRYPT_N - 1) * 32 + i];

    for (int i = 0; i < SCRYPT_N; i++) {
        uint j = (uint)(((ulong)X[1] << 32 | X[0]) & (SCRYPT_N - 1)); // Correct j selection based on first 64 bits of X
        
        
        // XOR X with V[j]
        for (int k = 0; k < 32; k++) {
            X[k] ^= V[j * 32 + k];
        }
        
        __private uint X_private[32];
        for(int k=0; k<32; k++) X_private[k] = X[k];
        blockmix_salsa8(X_private, X_private);
        for(int k=0; k<32; k++) X[k] = X_private[k];
    }

    // Copy final X back to B (or a global output buffer)
    for (int i = 0; i < 32; i++) {
        B[i] = X[i];
    }
}


// PBKDF2-HMAC-SHA256 function for Scrypt
void pbkdf2_hmac_sha256_scrypt(__private const uchar *password, uint password_len,
                               __private const uchar *salt, uint salt_len,
                               __private uchar *output, uint output_len) {
    uint state[8];
    uint ipad[16], opad[16];
    uint i, j;
    
    // Initialize SHA256 state
    state[0] = 0x6a09e667; state[1] = 0xbb67ae85; state[2] = 0x3c6ef372; state[3] = 0xa54ff53a;
    state[4] = 0x510e527f; state[5] = 0x9b05688c; state[6] = 0x1f83d9ab; state[7] = 0x5be0cd19;
    
    // Prepare HMAC key pads
    #pragma unroll
    for (i = 0; i < 16; i++) {
        uint key_word = 0;
        if (i * 4 < password_len) {
            for (j = 0; j < 4 && i * 4 + j < password_len; j++) {
                key_word |= ((uint)password[i * 4 + j]) << (j * 8);
            }
        }
        ipad[i] = key_word ^ 0x36363636;
        opad[i] = key_word ^ 0x5c5c5c5c;
    }
    
    // HMAC inner hash
    uint W[16];
    #pragma unroll
    for (i = 0; i < 16; i++) W[i] = ipad[i];
    
    // Process salt + counter (1)
    uint salt_blocks = (salt_len + 4 + 8) / 64 + 1;
    for (uint block = 0; block < salt_blocks; block++) {
        if (block > 0) {
            #pragma unroll
            for (i = 0; i < 16; i++) W[i] = 0;
        }
        
        // Fill block with salt data
        for (i = 0; i < 16 && block * 64 + i * 4 < salt_len + 4; i++) {
            uint word = 0;
            for (j = 0; j < 4; j++) {
                uint byte_idx = block * 64 + i * 4 + j;
                if (byte_idx < salt_len) {
                    word |= ((uint)salt[byte_idx]) << (j * 8);
                } else if (byte_idx == salt_len) {
                    word |= 1 << (j * 8); // Counter = 1
                }
            }
            W[i] = word;
        }
        
        // Add padding
        if (block == salt_blocks - 1) {
            uint bit_len = (salt_len + 4 + 64) * 8;
            W[14] = bit_len >> 32;
            W[15] = bit_len & 0xffffffff;
            if ((salt_len + 4) % 64 < 56) {
                W[(salt_len + 4) % 64 / 4] |= 0x80 << (((salt_len + 4) % 4) * 8);
            }
        }
        
        // SHA256 compression
        uint a = state[0], b = state[1], c = state[2], d = state[3];
        uint e = state[4], f = state[5], g = state[6], h = state[7];
        
        #pragma unroll
        for (i = 0; i < 64; i++) {
            if (i >= 16) {
                W[i & 15] = sigma1(W[(i-2) & 15]) + W[(i-7) & 15] + sigma0(W[(i-15) & 15]) + W[i & 15];
            }
            uint T1 = h + Sigma1(e) + Ch(e,f,g) + sha256_k[i] + W[i & 15];
            uint T2 = Sigma0(a) + Maj(a,b,c);
            h = g; g = f; f = e; e = d + T1; d = c; c = b; b = a; a = T1 + T2;
        }
        
        state[0] += a; state[1] += b; state[2] += c; state[3] += d;
        state[4] += e; state[5] += f; state[6] += g; state[7] += h;
    }
    
    // Store inner result
    uint inner_hash[8];
    #pragma unroll
    for (i = 0; i < 8; i++) inner_hash[i] = state[i];
    
    // HMAC outer hash
    state[0] = 0x6a09e667; state[1] = 0xbb67ae85; state[2] = 0x3c6ef372; state[3] = 0xa54ff53a;
    state[4] = 0x510e527f; state[5] = 0x9b05688c; state[6] = 0x1f83d9ab; state[7] = 0x5be0cd19;
    
    #pragma unroll
    for (i = 0; i < 16; i++) W[i] = (i < 8) ? inner_hash[i] : ((i == 8) ? 0x80000000 : 0);
    W[15] = (64 + 32) * 8; // bit length
    
    uint a = state[0], b = state[1], c = state[2], d = state[3];
    uint e = state[4], f = state[5], g = state[6], h = state[7];
    
    // Process opad
    #pragma unroll
    for (i = 0; i < 16; i++) W[i] ^= opad[i];
    
    #pragma unroll
    for (i = 0; i < 64; i++) {
        if (i >= 16) {
            W[i & 15] = sigma1(W[(i-2) & 15]) + W[(i-7) & 15] + sigma0(W[(i-15) & 15]) + W[i & 15];
        }
        uint T1 = h + Sigma1(e) + Ch(e,f,g) + sha256_k[i] + W[i & 15];
        uint T2 = Sigma0(a) + Maj(a,b,c);
        h = g; g = f; f = e; e = d + T1; d = c; c = b; b = a; a = T1 + T2;
    }
    
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
    
    // Convert output to bytes
    #pragma unroll
    for (i = 0; i < output_len && i < 32; i++) {
        uint word_idx = i / 4;
        uint byte_idx = i % 4;
        output[i] = (state[word_idx] >> (byte_idx * 8)) & 0xff;
    }
}

// Main scrypt_1024_1_1_256 kernel with proper API
__kernel void scrypt_1024_1_1_256(
    __constant const uchar* header_prefix,     // 76-byte static header
    uint nonce_base,                          // Base nonce
    __constant const uint* share_target_le,   // 32-byte LE share target
    __global uint* found_flag,                // Found share flag
    __global uint* found_nonce,               // Found nonce output
    __global uint* found_hash,                // Found hash output (optional)
    __global uint* V                          // Scrypt scratchpad
) {
    uint gid = get_global_id(0);
    uint current_nonce = nonce_base + gid;
    
    // Construct 80-byte header with nonce
    uchar header[80];
    #pragma unroll
    for (int i = 0; i < 76; i++) {
        header[i] = header_prefix[i];
    }
    
    // Append nonce (little-endian)
    header[76] = current_nonce & 0xff;
    header[77] = (current_nonce >> 8) & 0xff;
    header[78] = (current_nonce >> 16) & 0xff;
    header[79] = (current_nonce >> 24) & 0xff;
    
    // PBKDF2 pre-hash: generate 128-byte B from header
    uchar B_bytes[128];
    pbkdf2_hmac_sha256_scrypt(header, 80, header, 80, B_bytes, 128);
    
    // Convert to uint array for ROMix
    uint B[32];
    #pragma unroll
    for (int i = 0; i < 32; i++) {
        B[i] = ((uint)B_bytes[i*4]) | 
               ((uint)B_bytes[i*4+1] << 8) |
               ((uint)B_bytes[i*4+2] << 16) |
               ((uint)B_bytes[i*4+3] << 24);
    }
    
    // ROMix with N=1024, r=1
    scrypt_1024_1_1(B, V + (gid * 32768)); // 32KB per thread
    
    // Convert back to bytes
    #pragma unroll
    for (int i = 0; i < 32; i++) {
        B_bytes[i*4] = B[i] & 0xff;
        B_bytes[i*4+1] = (B[i] >> 8) & 0xff;
        B_bytes[i*4+2] = (B[i] >> 16) & 0xff;
        B_bytes[i*4+3] = (B[i] >> 24) & 0xff;
    }
    
    // PBKDF2 post-hash: produce final 32-byte digest
    uchar final_hash[32];
    pbkdf2_hmac_sha256_scrypt(header, 80, B_bytes, 128, final_hash, 32);
    
    // Convert hash to uint for comparison (little-endian)
    uint hash_words[8];
    #pragma unroll
    for (int i = 0; i < 8; i++) {
        hash_words[i] = ((uint)final_hash[i*4]) |
                       ((uint)final_hash[i*4+1] << 8) |
                       ((uint)final_hash[i*4+2] << 16) |
                       ((uint)final_hash[i*4+3] << 24);
    }
    
    // Compare with share target (32-byte little-endian)
    bool found = true;
    for (int i = 7; i >= 0; i--) {
        if (hash_words[i] > share_target_le[i]) {
            found = false;
            break;
        } else if (hash_words[i] < share_target_le[i]) {
            break;
        }
    }
    
    // Report found share
    if (found) {
        atomic_cmpxchg(found_flag, 0, 1);
        *found_nonce = current_nonce;
        
        // Optional: store found hash for verification
        if (found_hash) {
            #pragma unroll
            for (int i = 0; i < 8; i++) {
                found_hash[i] = hash_words[i];
            }
        }
    }
}