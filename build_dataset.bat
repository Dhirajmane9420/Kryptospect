@echo off
ECHO =========================================
ECHO Starting MULTI-ARCHITECTURE Build Process
ECHO =========================================

REM --- Define a list of optimization levels to compile with ---
set OP_LEVELS=-O0 -O1 -O2 -O3 -Os

REM --- Create the output directory if it doesn't exist ---
if not exist dataset mkdir dataset

ECHO.
ECHO [PHASE 1] Building Docker images...
ECHO   -> Building ARM32 compiler image...
docker build -t arm32-compiler -f Dockerfile.arm32 .
ECHO   -> Building MIPS64 compiler image...
docker build -t mips64-compiler -f Dockerfile.mips64 .

ECHO.
ECHO [PHASE 2] Compiling binaries...

REM --- ARM32 COMPILATION ---
ECHO.
ECHO [INFO] Compiling for ARM32...
FOR %%O IN (%OP_LEVELS%) DO (
    ECHO   -> Compiling aes_ecb_example.c with %%O
    docker run --rm -v "%cd%:/work" arm32-compiler gcc aes_ecb_example.c -o /work/dataset/ecb_arm32_%%O -static -lcrypto %%O
    ECHO   -> Compiling aes_cbc_example.c with %%O
    docker run --rm -v "%cd%:/work" arm32-compiler gcc aes_cbc_example.c -o /work/dataset/cbc_arm32_%%O -static -lcrypto %%O
)

REM --- MIPS64 COMPILATION ---
ECHO.
ECHO [INFO] Compiling for MIPS64...
FOR %%O IN (%OP_LEVELS%) DO (
    ECHO   -> Compiling aes_ecb_example.c with %%O
    docker run --rm -v "%cd%:/work" mips64-compiler gcc aes_ecb_example.c -o /work/dataset/ecb_mips64_%%O -static -lcrypto %%O
    ECHO   -> Compiling aes_cbc_example.c with %%O
    docker run --rm -v "%cd%:/work" mips64-compiler gcc aes_cbc_example.c -o /work/dataset/cbc_mips64_%%O -static -lcrypto %%O
)

ECHO.
ECHO =========================================
ECHO Build process finished.
ECHO Check the 'dataset' folder for all binaries.
ECHO =========================================