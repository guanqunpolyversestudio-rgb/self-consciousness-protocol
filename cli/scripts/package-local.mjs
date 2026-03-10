#!/usr/bin/env node
import { mkdir, rm, cp, writeFile, readFile } from "node:fs/promises";
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
  await rm(outputRoot, { recursive: true, force: true });
  await mkdir(path.join(versionDir, "dist"), { recursive: true });
  await mkdir(path.join(versionDir, "share", "skills", "self-consciousness"), { recursive: true });
  await mkdir(path.join(versionDir, "share", "skills", "gameplay-creator", "references"), { recursive: true });
  await mkdir(path.join(versionDir, "share", "skills", "gameplay-creator", "scripts"), { recursive: true });

  const distIndex = path.join(cliRoot, "dist", "index.js");
  if (!existsSync(distIndex)) {
    throw new Error("Missing dist/index.js. Run npm run build first.");
  }

  await cp(distIndex, path.join(versionDir, "dist", "index.js"));
  await cp(path.join(repoRoot, "SKILL.md"), path.join(versionDir, "share", "skills", "self-consciousness", "SKILL.md"));
  await cp(
    path.join(repoRoot, "gameplay-creator", "SKILL.md"),
    path.join(versionDir, "share", "skills", "gameplay-creator", "SKILL.md"),
  );
  await cp(
    path.join(repoRoot, "gameplay-creator", "references", "gameplay-spec.md"),
    path.join(versionDir, "share", "skills", "gameplay-creator", "references", "gameplay-spec.md"),
  );
  await cp(
    path.join(repoRoot, "gameplay-creator", "scripts", "create_gameplay_draft.py"),
    path.join(versionDir, "share", "skills", "gameplay-creator", "scripts", "create_gameplay_draft.py"),
  );

  const launcher = `#!/usr/bin/env bash
set -euo pipefail
exec node "$(cd "$(dirname "$0")" && pwd)/dist/index.js" "$@"
`;
  await writeFile(path.join(versionDir, "selfcon"), launcher, { mode: 0o755 });

  const tarball = path.join(outputRoot, `selfcon-cli-package.tar.gz`);
  await execFileAsync("tar", ["-czf", tarball, "-C", outputRoot, "selfcon"]);
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
