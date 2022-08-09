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
    port = lib.mkOption {
      type = lib.types.int;
      description = "Port to run application on";
    };
    images = lib.mkOption {
      default = "/tmp";
      type = lib.types.path;
      description = "Where to store images";
    };
    georust = lib.mkOption {
      type = lib.types.string;
      description = "Link to georust service";
    };
    database = lib.mkOption {
      default = "/tmp/database.csv";
      type = lib.types.path;
      description = "Path to database.csv";
    };
  };
  
  config = lib.mkIf cfg.enable {
    systemd.services.fish = {
      wantedBy = ["multi-user.target"];
      serviceConfig = {
        Environment = "IMAGES=${cfg.images}";
        Environment = "GEORUST=${cfg.georust}";
        Environment = "DATABASE=${cfg.database}";
        ExecStart = "${appEnv}/bin/waitress-serve --port=${toString cfg.port} fish:app";
      };
    };
  };
}
