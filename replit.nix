# ScryptMineOS Enterprise Edition - Nix Environment
# Provides all dependencies for cloud development

{ pkgs }: {
  deps = [
    # Python and core dependencies
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    
    # Cryptography dependencies
    pkgs.python311Packages.cryptography
    pkgs.python311Packages.pycryptodome
    pkgs.openssl
    pkgs.libffi
    
    # Networking and async
    pkgs.python311Packages.aiohttp
    pkgs.python311Packages.asyncio
    pkgs.python311Packages.websockets
    
    # Data processing
    pkgs.python311Packages.numpy
    pkgs.python311Packages.pandas
    pkgs.python311Packages.requests
    
    # Monitoring and metrics
    pkgs.python311Packages.prometheus-client
    
    # Database
    pkgs.python311Packages.pymongo
    pkgs.mongodb
    
    # Development tools
    pkgs.git
    pkgs.curl
    pkgs.wget
    pkgs.htop
    pkgs.tree
    
    # Build tools
    pkgs.gcc
    pkgs.gnumake
    pkgs.cmake
    
    # OpenCL for GPU mining
    pkgs.opencl-headers
    pkgs.ocl-icd
    
    # System utilities
    pkgs.procps
    pkgs.psmisc
    pkgs.lsof
  ];

  env = {
    # Python environment
    PYTHONPATH = "$PYTHONPATH:$PWD";
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
      pkgs.xorg.libX11
    ];
    
    # OpenCL environment
    OPENCL_VENDOR_PATH = "${pkgs.ocl-icd}/etc/OpenCL/vendors";
    
    # Enterprise configuration
    ENVIRONMENT = "replit";
    REPLIT_MODE = "true";
    LOG_LEVEL = "INFO";
    
    # Default ports
    API_PORT = "8080";
    METRICS_PORT = "9090";
    HEALTH_CHECK_PORT = "8081";
  };
}
