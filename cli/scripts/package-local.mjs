#!/usr/bin/env node
import { mkdir, rm, writeFile, readFile, chmod } from "node:fs/promises";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cliRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(cliRoot, "..");
const seaFuse = "NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2";

async function main() {
  const packageJson = JSON.parse(await readFile(path.join(cliRoot, "package.json"), "utf-8"));
  const version = packageJson.version;
  const platform = normalizePlatform(os.platform());
  const arch = normalizeArch(os.arch());
  if (!platform || !arch) {
    throw new Error(`Unsupported platform or architecture: ${os.platform()} ${os.arch()}`);
  }

  const outputRoot = path.join(repoRoot, "artifacts", `${version}-${platform}-${arch}`);
  const versionDir = path.join(outputRoot, "selfcon");
  const binaryPath = path.join(versionDir, "selfcon");
  const blobPath = path.join(outputRoot, "sea-prep.blob");
  await rm(outputRoot, { recursive: true, force: true });
  await mkdir(versionDir, { recursive: true });

  const distIndex = path.join(cliRoot, "dist", "index.js");
  if (!existsSync(distIndex)) {
    throw new Error("Missing dist/index.js. Run npm run build first.");
  }

  const seaConfigPath = path.join(outputRoot, "sea-config.json");
  const seaConfig = {
    main: distIndex,
    output: blobPath,
    mainFormat: "module",
    disableExperimentalSEAWarning: true,
    useSnapshot: false,
    useCodeCache: false,
    assets: {
      "skill:self-consciousness/SKILL.md": path.join(repoRoot, "SKILL.md"),
      "skill:gameplay-creator/SKILL.md": path.join(repoRoot, "gameplay-creator", "SKILL.md"),
      "skill:gameplay-creator/references/gameplay-spec.md": path.join(repoRoot, "gameplay-creator", "references", "gameplay-spec.md"),
      "skill:gameplay-creator/scripts/create_gameplay_draft.py": path.join(repoRoot, "gameplay-creator", "scripts", "create_gameplay_draft.py"),
    },
  };
  await writeFile(seaConfigPath, JSON.stringify(seaConfig, null, 2) + "\n", "utf-8");
  await execFileAsync(process.execPath, ["--experimental-sea-config", seaConfigPath]);
  await execFileAsync("cp", [process.execPath, binaryPath]);
  if (platform === "darwin") {
    try {
      await execFileAsync("codesign", ["--remove-signature", binaryPath]);
    } catch {
      // Some local Node builds are not signed. Keep going.
    }
  }
  const postjectPath = path.join(cliRoot, "node_modules", ".bin", "postject");
  const postjectArgs = [
    binaryPath,
    "NODE_SEA_BLOB",
    blobPath,
    "--sentinel-fuse",
    seaFuse,
  ];
  if (platform === "darwin") {
    postjectArgs.push("--macho-segment-name", "NODE_SEA");
  }
  await execFileAsync(postjectPath, postjectArgs);
  await chmod(binaryPath, 0o755);
  if (platform === "darwin") {
    await execFileAsync("codesign", ["--sign", "-", "--force", binaryPath]);
  }

  const tarball = path.join(outputRoot, `selfcon-${version}-${platform}-${arch}.tar.gz`);
  await execFileAsync("tar", ["-czf", tarball, "-C", versionDir, "selfcon"]);
  process.stdout.write(`${tarball}\n`);
}

function normalizePlatform(value) {
  if (value === "darwin") return "darwin";
  if (value === "linux") return "linux";
  return "";
}

function normalizeArch(value) {
  if (value === "arm64") return "arm64";
  if (value === "x64") return "x64";
  return "";
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
