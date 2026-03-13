/**
 * PM2 Ecosystem Config — CoPaw
 *
 * Start:   pm2 start ecosystem.config.cjs
 * Stop:    pm2 stop copaw
 * Logs:    pm2 logs copaw
 * Save:    pm2 save   (persist across reboots)
 * Startup: pm2 startup (generate system service)
 *
 * CoPaw must be installed first:
 *   bash scripts/install.sh --from-source /workspace/test-deploy/CoPaw
 *
 * The venv binary is used directly so this config works regardless of
 * whether ~/.copaw/bin is on PATH.
 */

const os = require("os");
const path = require("path");

const COPAW_HOME = process.env.COPAW_HOME || path.join(os.homedir(), ".copaw");
const COPAW_BIN = path.join(COPAW_HOME, "venv", "bin", "copaw");

module.exports = {
  apps: [
    {
      name: "copaw",
      script: COPAW_BIN,
      args: "app --host 0.0.0.0 --port 8600",
      interpreter: "none",

      // Restart policy
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,

      // Environment
      env: {
        COPAW_HOME: COPAW_HOME,
      },

      // Logging — written alongside copaw's own logs
      out_file: path.join(COPAW_HOME, "pm2-out.log"),
      error_file: path.join(COPAW_HOME, "pm2-err.log"),
      merge_logs: true,
      time: true,
    },
  ],
};
