{python3Packages ? (import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/e3583ad6e533a9d8dd78f90bfa93812d390ea187.tar.gz") {}).python3Packages}:
with python3Packages;
  buildPythonPackage {
    name = "fish";
    src = ./src;

    format = "other";
    shellHook = ''
    export FLASK_APP=src
    export FLASK_ENV=development
    alias run="pgrep georust || georust &
pgrep python | xargs kill -9 2>/dev/null
python -m flask run"
    '';
    propagatedBuildInputs = [flask exif folium pillow sqlitedict requests timeago];

    installPhase = ''
      runHook preInstall
      mkdir -p $out/${python.sitePackages}
      cp -r . $out/${python.sitePackages}/fish
      runHook postInstall
    '';
  }
