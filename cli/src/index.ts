#!/usr/bin/env node
import { mkdir, readFile, writeFile, cp, readdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import * as sea from "node:sea";

const DEFAULT_BACKEND_URL = "https://self-consciousness-backend.onrender.com";
const LEGACY_BACKEND_URLS = new Set([
  "",
  "http://127.0.0.1:8000",
  "http://localhost:8000",
  "https://127.0.0.1:8000",
  "https://localhost:8000",
]);

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

type Profile = {
  current_user_id: string;
  backend_base_url: string;
  users: Record<string, {
    user_id: string;
    workspace: Workspace;
    onboarding_mode: string;
    preference_payload: Record<string, JsonValue>;
    created_at: string;
  }>;
  updated_at: string;
};

type Workspace = {
  root: string;
  db_path: string;
  gameplay_drafts_dir: string;
  gameplay_cache_dir: string;
  automation_state_path: string;
  artifacts_dir: string;
  logs_dir: string;
};

type ArgMap = Record<string, string | boolean>;

const packageRoot = path.resolve(__dirname, "..");
const devShareRoot = path.resolve(packageRoot, "..");
const profilePath = path.join(os.homedir(), ".self-consciousness", "profile.json");
const embeddedSkillAssets = {
  "self-consciousness/SKILL.md": "skill:self-consciousness/SKILL.md",
  "gameplay-creator/SKILL.md": "skill:gameplay-creator/SKILL.md",
  "gameplay-creator/references/gameplay-spec.md": "skill:gameplay-creator/references/gameplay-spec.md",
  "gameplay-creator/scripts/create_gameplay_draft.py": "skill:gameplay-creator/scripts/create_gameplay_draft.py",
} as const;

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || hasFlag(argv, "--help") || hasFlag(argv, "-h")) {
    printHelp();
    return;
  }

  const [topic, subtopic, ...rest] = argv;

  if (topic === "install") {
    await cmdInstall(parseArgs([subtopic, ...rest]));
    return;
  }
  if (topic === "onboard") {
    await cmdOnboard(parseArgs([subtopic, ...rest]));
    return;
  }
  if (topic === "prefs" && subtopic === "set") {
    await cmdPrefsSet(parseArgs(rest));
    return;
  }
  if (topic === "gameplay") {
    const args = parseArgs(rest);
    if (subtopic === "list") {
      await cmdGameplayList(args);
      return;
    }
    if (subtopic === "recommend") {
      await cmdGameplayRecommend(args);
      return;
    }
    if (subtopic === "pull") {
      await cmdGameplayPull(args);
      return;
    }
    if (subtopic === "create") {
      await cmdGameplayCreate(args);
      return;
    }
    if (subtopic === "publish") {
      await cmdGameplayPublish(args);
      return;
    }
  }

  throw new Error(`Unknown command: ${argv.join(" ")}`);
}

function printHelp() {
  process.stdout.write(`selfcon

Commands:
  selfcon install --skills-dir <dir>
  selfcon onboard --user-id <id> [--backend-url <url>]
  selfcon prefs set [--user-id <id>] [--daily-sync on|off] [--daily-sync-time HH:MM]
                    [--recommendation-mode off|daily|always_loop]
                    [--passive-recommendation on|off]
                    [--interaction-style <text>] [--avoid-saying <text>]
                    [--challenge-tolerance <level>] [--playfulness <level>]
  selfcon gameplay list [--backend-url <url>]
  selfcon gameplay recommend [--backend-url <url>] [--trigger <kind>] [--desired-tags a,b]
                             [--user-goal-tags a,b] [--allow-one-shot on|off]
                             [--allow-loop on|off] [--available-tools a,b]
  selfcon gameplay pull --id <gameplay_id> [--user-id <id>] [--backend-url <url>]
  selfcon gameplay create --id <id> --name <name> --summary <summary>
                          [--user-id <id>] [--mode one_shot|loop|open]
                          [--tools a,b] [--tags a,b] [--metadata-json '{"x":1}']
                          [--markdown-file <path>] [--out <path>]
  selfcon gameplay publish --file <path> [--user-id <id>] [--backend-url <url>]
`);
}

function hasFlag(argv: string[], flag: string) {
  return argv.includes(flag);
}

function parseArgs(argv: string[]): ArgMap {
  const args: ArgMap = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
      continue;
    }
    args[key] = next;
    i += 1;
  }
  return args;
}

function requireString(args: ArgMap, key: string): string {
  const value = args[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`Missing required option --${key}`);
  }
  return value;
}

function optionalString(args: ArgMap, key: string): string {
  const value = args[key];
  return typeof value === "string" ? value : "";
}

function parseCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseToggle(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  if (normalized === "on" || normalized === "true" || normalized === "yes") return true;
  if (normalized === "off" || normalized === "false" || normalized === "no") return false;
  throw new Error(`Expected on/off style value, got: ${value}`);
}

function nowIso() {
  return new Date().toISOString();
}

function getUserRoot(userId: string) {
  return path.join(os.homedir(), ".self-consciousness", "users", userId);
}

function getWorkspace(userId: string): Workspace {
  const root = getUserRoot(userId);
  return {
    root,
    db_path: path.join(root, "consciousness.db"),
    gameplay_drafts_dir: path.join(root, "gameplay_drafts"),
    gameplay_cache_dir: path.join(root, "gameplay_cache"),
    automation_state_path: path.join(root, "automation_state.json"),
    artifacts_dir: path.join(root, "artifacts"),
    logs_dir: path.join(os.homedir(), ".self-consciousness", "logs"),
  };
}

async function ensureWorkspace(userId: string) {
  const workspace = getWorkspace(userId);
  await mkdir(workspace.root, { recursive: true });
  await mkdir(workspace.gameplay_drafts_dir, { recursive: true });
  await mkdir(workspace.gameplay_cache_dir, { recursive: true });
  await mkdir(workspace.artifacts_dir, { recursive: true });
  await mkdir(workspace.logs_dir, { recursive: true });
  if (!existsSync(workspace.automation_state_path)) {
    await writeFile(
      workspace.automation_state_path,
      JSON.stringify(defaultAutomationState(), null, 2) + "\n",
      "utf-8",
    );
  }
  return workspace;
}

function defaultAutomationState() {
  return {
    daily_sync_enabled: false,
    daily_sync_time: "",
    gameplay_recommendation_mode: "off",
    passive_gameplay_enabled: false,
    last_run_date: "",
    last_surface_date: "",
    last_action: "",
    cooldown_until: "",
    active_gameplay_id: "",
    active_gameplay_mode: "",
    active_gameplay_status: "idle",
    last_completed_gameplay_id: "",
    last_completion_trigger: "",
    recent_recommended_gameplay_ids: [],
    recent_dismissed_gameplay_ids: [],
    recent_completed_gameplay_ids: [],
    loop_paused: false,
    current_recommendation: {},
    updated_at: "",
  };
}

async function readProfile(): Promise<Profile> {
  if (!existsSync(profilePath)) {
    return {
      current_user_id: "",
      backend_base_url: DEFAULT_BACKEND_URL,
      users: {},
      updated_at: "",
    };
  }
  try {
    const parsed = JSON.parse(await readFile(profilePath, "utf-8")) as Partial<Profile>;
    return {
      current_user_id: parsed.current_user_id ?? "",
      backend_base_url: parsed.backend_base_url ?? DEFAULT_BACKEND_URL,
      users: parsed.users ?? {},
      updated_at: parsed.updated_at ?? "",
    };
  } catch {
    return {
      current_user_id: "",
      backend_base_url: DEFAULT_BACKEND_URL,
      users: {},
      updated_at: "",
    };
  }
}

async function writeProfile(profile: Profile) {
  await mkdir(path.dirname(profilePath), { recursive: true });
  profile.updated_at = nowIso();
  await writeFile(profilePath, JSON.stringify(profile, null, 2) + "\n", "utf-8");
}

async function upsertLocalUser(userId: string, options: {
  backendUrl?: string;
  onboardingMode?: string;
  preferencePayload?: Record<string, JsonValue>;
}) {
  const workspace = await ensureWorkspace(userId);
  const profile = await readProfile();
  const backendUrl = options.backendUrl && !LEGACY_BACKEND_URLS.has(options.backendUrl)
    ? options.backendUrl
    : profile.backend_base_url || DEFAULT_BACKEND_URL;
  profile.backend_base_url = backendUrl;
  profile.current_user_id = userId;
  const existing = profile.users[userId];
  profile.users[userId] = {
    user_id: userId,
    workspace,
    onboarding_mode: options.onboardingMode ?? existing?.onboarding_mode ?? "user_intent_first",
    preference_payload: options.preferencePayload ?? existing?.preference_payload ?? {},
    created_at: existing?.created_at ?? nowIso(),
  };
  await writeProfile(profile);
  return { profile, workspace };
}

function getBackendUrl(profile: Profile, override = "") {
  if (override && !LEGACY_BACKEND_URLS.has(override)) return override;
  if (!LEGACY_BACKEND_URLS.has(profile.backend_base_url)) return profile.backend_base_url;
  return DEFAULT_BACKEND_URL;
}

async function backendRequest(method: string, endpoint: string, body?: unknown, backendUrl = "") {
  const profile = await readProfile();
  const baseUrl = getBackendUrl(profile, backendUrl);
  const response = await fetch(`${baseUrl}${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${method} ${endpoint} failed: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function cmdInstall(args: ArgMap) {
  const skillsDir = requireString(args, "skills-dir");
  const backendUrl = optionalString(args, "backend-url") || DEFAULT_BACKEND_URL;
  const selfSkillDir = path.join(skillsDir, "self-consciousness");
  const gameplayCreatorDir = path.join(skillsDir, "gameplay-creator");
  await mkdir(selfSkillDir, { recursive: true });
  await mkdir(gameplayCreatorDir, { recursive: true });
  if (sea.isSea()) {
    await writeEmbeddedSkillFile("self-consciousness/SKILL.md", path.join(selfSkillDir, "SKILL.md"));
    await writeEmbeddedSkillFile("gameplay-creator/SKILL.md", path.join(gameplayCreatorDir, "SKILL.md"));
    await writeEmbeddedSkillFile(
      "gameplay-creator/references/gameplay-spec.md",
      path.join(gameplayCreatorDir, "references", "gameplay-spec.md"),
    );
    await writeEmbeddedSkillFile(
      "gameplay-creator/scripts/create_gameplay_draft.py",
      path.join(gameplayCreatorDir, "scripts", "create_gameplay_draft.py"),
    );
  } else {
    const selfSkillSource = path.join(devShareRoot, "SKILL.md");
    const gameplayCreatorSource = path.join(devShareRoot, "gameplay-creator");
    await cp(selfSkillSource, path.join(selfSkillDir, "SKILL.md"));
    await copyDir(gameplayCreatorSource, gameplayCreatorDir);
  }

  const profile = await readProfile();
  profile.backend_base_url = LEGACY_BACKEND_URLS.has(profile.backend_base_url) ? backendUrl : profile.backend_base_url;
  await writeProfile(profile);
  await mkdir(path.join(os.homedir(), ".self-consciousness"), { recursive: true });

  process.stdout.write(JSON.stringify({
    ok: true,
    cli: "selfcon",
    skills: [
      path.join(selfSkillDir, "SKILL.md"),
      gameplayCreatorDir,
    ],
    profile_path: profilePath,
    backend_base_url: profile.backend_base_url,
  }, null, 2) + "\n");
}

async function cmdOnboard(args: ArgMap) {
  const userId = requireString(args, "user-id");
  const backendUrl = optionalString(args, "backend-url");
  const register = await backendRequest(
    "POST",
    "/api/v1/onboarding/register",
    { user_id: userId, backend_base_url: getBackendUrl(await readProfile(), backendUrl) },
    backendUrl,
  );
  const { profile, workspace } = await upsertLocalUser(userId, {
    backendUrl: getBackendUrl(await readProfile(), backendUrl),
    onboardingMode: "user_intent_first",
  });
  process.stdout.write(JSON.stringify({
    ok: true,
    user_id: userId,
    credits: register.credits,
    workspace,
    backend_base_url: profile.backend_base_url,
    runtime_state: register.runtime_state ?? {},
  }, null, 2) + "\n");
}

async function cmdPrefsSet(args: ArgMap) {
  const profile = await readProfile();
  const userId = optionalString(args, "user-id") || profile.current_user_id;
  if (!userId) {
    throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
  }
  const payload: Record<string, JsonValue> = {};
  if (optionalString(args, "daily-sync")) payload.daily_sync_enabled = parseToggle(optionalString(args, "daily-sync"));
  if (optionalString(args, "daily-sync-time")) payload.daily_sync_time = optionalString(args, "daily-sync-time");
  if (optionalString(args, "recommendation-mode")) payload.gameplay_recommendation_mode = optionalString(args, "recommendation-mode");
  if (optionalString(args, "passive-recommendation")) payload.passive_gameplay_enabled = parseToggle(optionalString(args, "passive-recommendation"));
  if (optionalString(args, "interaction-style")) payload.interaction_preferred_style = optionalString(args, "interaction-style");
  if (optionalString(args, "avoid-saying")) payload.interaction_do_not_say = [optionalString(args, "avoid-saying")];
  if (optionalString(args, "challenge-tolerance")) payload.challenge_tolerance = optionalString(args, "challenge-tolerance");
  if (optionalString(args, "playfulness")) payload.playfulness_preference = optionalString(args, "playfulness");

  const saved = await backendRequest(
    "POST",
    "/api/v1/onboarding/preference",
    { user_id: userId, ...payload },
    optionalString(args, "backend-url"),
  );
  await upsertLocalUser(userId, {
    preferencePayload: saved.preference_payload ?? payload,
  });
  process.stdout.write(JSON.stringify(saved, null, 2) + "\n");
}

async function cmdGameplayList(args: ArgMap) {
  const response = await backendRequest("GET", "/api/v1/gameplays", undefined, optionalString(args, "backend-url"));
  process.stdout.write(JSON.stringify(response, null, 2) + "\n");
}

async function cmdGameplayRecommend(args: ArgMap) {
  const body: Record<string, JsonValue> = {};
  if (optionalString(args, "trigger")) body.trigger = optionalString(args, "trigger");
  if (optionalString(args, "desired-tags")) body.desired_tags = parseCsv(optionalString(args, "desired-tags"));
  if (optionalString(args, "user-goal-tags")) body.user_goal_tags = parseCsv(optionalString(args, "user-goal-tags"));
  if (optionalString(args, "available-tools")) body.available_tools = parseCsv(optionalString(args, "available-tools"));
  if (optionalString(args, "allow-one-shot")) body.allow_one_shot = parseToggle(optionalString(args, "allow-one-shot"));
  if (optionalString(args, "allow-loop")) body.allow_loop = parseToggle(optionalString(args, "allow-loop"));
  if (optionalString(args, "current-gameplay-id")) body.current_gameplay_id = optionalString(args, "current-gameplay-id");
  if (optionalString(args, "active-gameplay-mode")) body.active_gameplay_mode = optionalString(args, "active-gameplay-mode");
  if (optionalString(args, "last-completed-gameplay-id")) body.last_completed_gameplay_id = optionalString(args, "last-completed-gameplay-id");
  const response = await backendRequest("POST", "/api/v1/gameplays/recommend", body, optionalString(args, "backend-url"));
  process.stdout.write(JSON.stringify(response, null, 2) + "\n");
}

async function cmdGameplayPull(args: ArgMap) {
  const gameplayId = requireString(args, "id");
  const profile = await readProfile();
  const userId = optionalString(args, "user-id") || profile.current_user_id;
  if (!userId) {
    throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
  }
  const gameplay = await backendRequest("GET", `/api/v1/gameplays/${gameplayId}`, undefined, optionalString(args, "backend-url"));
  const workspace = await ensureWorkspace(userId);
  const targetPath = path.join(workspace.gameplay_cache_dir, `${gameplayId}.md`);
  await writeFile(targetPath, serializeGameplayMarkdown(gameplay), "utf-8");
  process.stdout.write(JSON.stringify({ ok: true, gameplay_id: gameplayId, cache_path: targetPath }, null, 2) + "\n");
}

async function cmdGameplayCreate(args: ArgMap) {
  const profile = await readProfile();
  const userId = optionalString(args, "user-id") || profile.current_user_id;
  if (!userId) {
    throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
  }
  const gameplayId = requireString(args, "id");
  const name = requireString(args, "name");
  const summary = requireString(args, "summary");
  const workspace = await ensureWorkspace(userId);
  const outputPath = optionalString(args, "out") || path.join(workspace.gameplay_drafts_dir, `${gameplayId}.md`);
  const mode = optionalString(args, "mode") || "open";
  const tools = optionalString(args, "tools") ? parseCsv(optionalString(args, "tools")) : [];
  const tags = optionalString(args, "tags") ? parseCsv(optionalString(args, "tags")) : [];
  const metadata = optionalString(args, "metadata-json")
    ? JSON.parse(optionalString(args, "metadata-json")) as Record<string, JsonValue>
    : {};
  const markdown = optionalString(args, "markdown-file")
    ? await readFile(optionalString(args, "markdown-file"), "utf-8")
    : synthesizeGameplayMarkdown({ id: gameplayId, name, summary, mode, tools, tags, metadata });

  const content = serializeGameplayMarkdown({
    id: gameplayId,
    name,
    name_zh: "",
    summary,
    mode,
    tools,
    tags,
    metadata,
    markdown,
    created_at: nowIso(),
  });
  await writeFile(outputPath, content, "utf-8");
  process.stdout.write(JSON.stringify({ ok: true, file: outputPath }, null, 2) + "\n");
}

async function cmdGameplayPublish(args: ArgMap) {
  const profile = await readProfile();
  const userId = optionalString(args, "user-id") || profile.current_user_id;
  if (!userId) {
    throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
  }
  const file = requireString(args, "file");
  const markdown = await readFile(file, "utf-8");
  const response = await backendRequest(
    "POST",
    "/api/v1/gameplays/contribute",
    { user_id: userId, markdown },
    optionalString(args, "backend-url"),
  );
  process.stdout.write(JSON.stringify(response, null, 2) + "\n");
}

async function copyDir(source: string, target: string) {
  await mkdir(target, { recursive: true });
  const entries = await readdir(source);
  for (const entry of entries) {
    const sourcePath = path.join(source, entry);
    const targetPath = path.join(target, entry);
    const sourceStat = await stat(sourcePath);
    if (sourceStat.isDirectory()) {
      await copyDir(sourcePath, targetPath);
    } else {
      await mkdir(path.dirname(targetPath), { recursive: true });
      await cp(sourcePath, targetPath);
    }
  }
}

async function writeEmbeddedSkillFile(relativePath: keyof typeof embeddedSkillAssets, targetPath: string) {
  const assetKey = embeddedSkillAssets[relativePath];
  const asset = sea.getAsset(assetKey);
  if (!asset) {
    throw new Error(`Missing embedded asset: ${relativePath}`);
  }
  await mkdir(path.dirname(targetPath), { recursive: true });
  await writeFile(targetPath, Buffer.from(asset));
}

function serializeGameplayMarkdown(data: {
  id: string;
  name: string;
  name_zh: string;
  summary: string;
  mode: string;
  tools: string[];
  tags: string[];
  metadata: Record<string, JsonValue>;
  markdown: string;
  created_at: string;
}) {
  const metadata: Record<string, JsonValue> = {
    id: data.id,
    name: data.name,
    name_zh: data.name_zh,
    summary: data.summary,
    mode: data.mode,
    tools: data.tools,
    tags: data.tags,
    created_at: data.created_at,
  };
  if (Object.keys(data.metadata).length > 0) {
    metadata.metadata = data.metadata;
  }
  return `---\n${JSON.stringify(metadata, null, 2)}\n---\n\n${data.markdown.trim()}\n`;
}

function synthesizeGameplayMarkdown(data: {
  id: string;
  name: string;
  summary: string;
  mode: string;
  tools: string[];
  tags: string[];
  metadata: Record<string, JsonValue>;
}) {
  const lines = [
    `# ${data.name}`,
    "",
    data.summary,
  ];
  if (data.mode) {
    lines.push("", "## Mode", "", `\`${data.mode}\``);
  }
  if (data.tools.length > 0) {
    lines.push("", "## Tools", "");
    for (const tool of data.tools) {
      lines.push(`- \`${tool}\``);
    }
  }
  if (Object.keys(data.metadata).length > 0) {
    lines.push("", "## Notes", "", "```json", JSON.stringify(data.metadata, null, 2), "```");
  }
  return `${lines.join("\n")}\n`;
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
