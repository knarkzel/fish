{python3Packages ? (import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/e3583ad6e533a9d8dd78f90bfa93812d390ea187.tar.gz") {}).python3Packages}:
with python3Packages;
  buildPythonPackage {
    name = "fish";
    src = ./fish;

    format = "other";
    shellHook = ''
    export FLASK_APP=fish
    export FLASK_ENV=development
    '';
    propagatedBuildInputs = [flask exif folium];

    installPhase = ''
      runHook preInstall
      mkdir -p $out/${python.sitePackages}
      cp -r . $out/${python.sitePackages}/fish
      runHook postInstall
    '';
  }
