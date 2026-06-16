{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python311
    ruff
  ];

  # pip-installed binary wheels (pyzmq, pulled in by ipykernel) dlopen
  # libstdc++.so.6, which is not on NixOS's default loader path, so the Jupyter
  # kernel fails to start. Put the C++ runtime on LD_LIBRARY_PATH. Launch your
  # editor from this directory (direnv loads this shell) so the kernel inherits it.
  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib ]}:''${LD_LIBRARY_PATH:-}"
  '';
}
