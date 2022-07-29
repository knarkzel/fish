{
  lib,
  pkgs,
  config,
  ...
}: let
  cfg = config.services.fish;
  appEnv = pkgs.python3.withPackages (pkgs: with pkgs; [waitress (callPackage ./default.nix {})]);
in {
  options.services.fish = {
    enable = lib.mkEnableOption "fish";
  };

  config = lib.mkIf cfg.enable {
    systemd.services.fish = {
      wantedBy = ["multi-user.target"];
      serviceConfig = {
        ExecStart = "${appEnv}/bin/waitress-serve fish:app";
      };
    };
  };
}
