{python3Packages ? (import <nixpkgs> {}).python3Packages}:
with python3Packages;
  buildPythonPackage {
    name = "fish";
    src = ./fish;

    propagatedBuildInputs = [flask];

    installPhase = ''
      runHook preInstall

      mkdir -p $out/${python.sitePackages}
      cp -r . $out/${python.sitePackages}/fish

      runHook postInstall
    '';

    shellHook = "export FLASK_APP=fish";

    format = "other";
  }
