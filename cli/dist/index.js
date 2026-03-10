#!/usr/bin/env node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const promises_1 = require("node:fs/promises");
const node_fs_1 = require("node:fs");
const node_os_1 = __importDefault(require("node:os"));
const node_path_1 = __importDefault(require("node:path"));
const sea = __importStar(require("node:sea"));
const DEFAULT_BACKEND_URL = "https://self-consciousness-backend.onrender.com";
const LEGACY_BACKEND_URLS = new Set([
    "",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://127.0.0.1:8000",
    "https://localhost:8000",
]);
const packageRoot = node_path_1.default.resolve(__dirname, "..");
const devShareRoot = node_path_1.default.resolve(packageRoot, "..");
const profilePath = node_path_1.default.join(node_os_1.default.homedir(), ".self-consciousness", "profile.json");
const embeddedSkillAssets = {
    "self-consciousness/SKILL.md": "skill:self-consciousness/SKILL.md",
    "gameplay-creator/SKILL.md": "skill:gameplay-creator/SKILL.md",
    "gameplay-creator/references/gameplay-spec.md": "skill:gameplay-creator/references/gameplay-spec.md",
    "gameplay-creator/scripts/create_gameplay_draft.py": "skill:gameplay-creator/scripts/create_gameplay_draft.py",
};
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
function hasFlag(argv, flag) {
    return argv.includes(flag);
}
function parseArgs(argv) {
    const args = {};
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
function requireString(args, key) {
    const value = args[key];
    if (typeof value !== "string" || value.trim() === "") {
        throw new Error(`Missing required option --${key}`);
    }
    return value;
}
function optionalString(args, key) {
    const value = args[key];
    return typeof value === "string" ? value : "";
}
function parseCsv(value) {
    return value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
}
function parseToggle(value) {
    const normalized = value.trim().toLowerCase();
    if (normalized === "on" || normalized === "true" || normalized === "yes")
        return true;
    if (normalized === "off" || normalized === "false" || normalized === "no")
        return false;
    throw new Error(`Expected on/off style value, got: ${value}`);
}
function nowIso() {
    return new Date().toISOString();
}
function getUserRoot(userId) {
    return node_path_1.default.join(node_os_1.default.homedir(), ".self-consciousness", "users", userId);
}
function getWorkspace(userId) {
    const root = getUserRoot(userId);
    return {
        root,
        db_path: node_path_1.default.join(root, "consciousness.db"),
        gameplay_drafts_dir: node_path_1.default.join(root, "gameplay_drafts"),
        gameplay_cache_dir: node_path_1.default.join(root, "gameplay_cache"),
        automation_state_path: node_path_1.default.join(root, "automation_state.json"),
        artifacts_dir: node_path_1.default.join(root, "artifacts"),
        logs_dir: node_path_1.default.join(node_os_1.default.homedir(), ".self-consciousness", "logs"),
    };
}
async function ensureWorkspace(userId) {
    const workspace = getWorkspace(userId);
    await (0, promises_1.mkdir)(workspace.root, { recursive: true });
    await (0, promises_1.mkdir)(workspace.gameplay_drafts_dir, { recursive: true });
    await (0, promises_1.mkdir)(workspace.gameplay_cache_dir, { recursive: true });
    await (0, promises_1.mkdir)(workspace.artifacts_dir, { recursive: true });
    await (0, promises_1.mkdir)(workspace.logs_dir, { recursive: true });
    if (!(0, node_fs_1.existsSync)(workspace.automation_state_path)) {
        await (0, promises_1.writeFile)(workspace.automation_state_path, JSON.stringify(defaultAutomationState(), null, 2) + "\n", "utf-8");
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
async function readProfile() {
    if (!(0, node_fs_1.existsSync)(profilePath)) {
        return {
            current_user_id: "",
            backend_base_url: DEFAULT_BACKEND_URL,
            users: {},
            updated_at: "",
        };
    }
    try {
        const parsed = JSON.parse(await (0, promises_1.readFile)(profilePath, "utf-8"));
        return {
            current_user_id: parsed.current_user_id ?? "",
            backend_base_url: parsed.backend_base_url ?? DEFAULT_BACKEND_URL,
            users: parsed.users ?? {},
            updated_at: parsed.updated_at ?? "",
        };
    }
    catch {
        return {
            current_user_id: "",
            backend_base_url: DEFAULT_BACKEND_URL,
            users: {},
            updated_at: "",
        };
    }
}
async function writeProfile(profile) {
    await (0, promises_1.mkdir)(node_path_1.default.dirname(profilePath), { recursive: true });
    profile.updated_at = nowIso();
    await (0, promises_1.writeFile)(profilePath, JSON.stringify(profile, null, 2) + "\n", "utf-8");
}
async function upsertLocalUser(userId, options) {
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
function getBackendUrl(profile, override = "") {
    if (override && !LEGACY_BACKEND_URLS.has(override))
        return override;
    if (!LEGACY_BACKEND_URLS.has(profile.backend_base_url))
        return profile.backend_base_url;
    return DEFAULT_BACKEND_URL;
}
async function backendRequest(method, endpoint, body, backendUrl = "") {
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
async function cmdInstall(args) {
    const skillsDir = requireString(args, "skills-dir");
    const backendUrl = optionalString(args, "backend-url") || DEFAULT_BACKEND_URL;
    const selfSkillDir = node_path_1.default.join(skillsDir, "self-consciousness");
    const gameplayCreatorDir = node_path_1.default.join(skillsDir, "gameplay-creator");
    await (0, promises_1.mkdir)(selfSkillDir, { recursive: true });
    await (0, promises_1.mkdir)(gameplayCreatorDir, { recursive: true });
    if (sea.isSea()) {
        await writeEmbeddedSkillFile("self-consciousness/SKILL.md", node_path_1.default.join(selfSkillDir, "SKILL.md"));
        await writeEmbeddedSkillFile("gameplay-creator/SKILL.md", node_path_1.default.join(gameplayCreatorDir, "SKILL.md"));
        await writeEmbeddedSkillFile("gameplay-creator/references/gameplay-spec.md", node_path_1.default.join(gameplayCreatorDir, "references", "gameplay-spec.md"));
        await writeEmbeddedSkillFile("gameplay-creator/scripts/create_gameplay_draft.py", node_path_1.default.join(gameplayCreatorDir, "scripts", "create_gameplay_draft.py"));
    }
    else {
        const selfSkillSource = node_path_1.default.join(devShareRoot, "SKILL.md");
        const gameplayCreatorSource = node_path_1.default.join(devShareRoot, "gameplay-creator");
        await (0, promises_1.cp)(selfSkillSource, node_path_1.default.join(selfSkillDir, "SKILL.md"));
        await copyDir(gameplayCreatorSource, gameplayCreatorDir);
    }
    const profile = await readProfile();
    profile.backend_base_url = LEGACY_BACKEND_URLS.has(profile.backend_base_url) ? backendUrl : profile.backend_base_url;
    await writeProfile(profile);
    await (0, promises_1.mkdir)(node_path_1.default.join(node_os_1.default.homedir(), ".self-consciousness"), { recursive: true });
    process.stdout.write(JSON.stringify({
        ok: true,
        cli: "selfcon",
        skills: [
            node_path_1.default.join(selfSkillDir, "SKILL.md"),
            gameplayCreatorDir,
        ],
        profile_path: profilePath,
        backend_base_url: profile.backend_base_url,
    }, null, 2) + "\n");
}
async function cmdOnboard(args) {
    const userId = requireString(args, "user-id");
    const backendUrl = optionalString(args, "backend-url");
    const register = await backendRequest("POST", "/api/v1/onboarding/register", { user_id: userId, backend_base_url: getBackendUrl(await readProfile(), backendUrl) }, backendUrl);
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
async function cmdPrefsSet(args) {
    const profile = await readProfile();
    const userId = optionalString(args, "user-id") || profile.current_user_id;
    if (!userId) {
        throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
    }
    const payload = {};
    if (optionalString(args, "daily-sync"))
        payload.daily_sync_enabled = parseToggle(optionalString(args, "daily-sync"));
    if (optionalString(args, "daily-sync-time"))
        payload.daily_sync_time = optionalString(args, "daily-sync-time");
    if (optionalString(args, "recommendation-mode"))
        payload.gameplay_recommendation_mode = optionalString(args, "recommendation-mode");
    if (optionalString(args, "passive-recommendation"))
        payload.passive_gameplay_enabled = parseToggle(optionalString(args, "passive-recommendation"));
    if (optionalString(args, "interaction-style"))
        payload.interaction_preferred_style = optionalString(args, "interaction-style");
    if (optionalString(args, "avoid-saying"))
        payload.interaction_do_not_say = [optionalString(args, "avoid-saying")];
    if (optionalString(args, "challenge-tolerance"))
        payload.challenge_tolerance = optionalString(args, "challenge-tolerance");
    if (optionalString(args, "playfulness"))
        payload.playfulness_preference = optionalString(args, "playfulness");
    const saved = await backendRequest("POST", "/api/v1/onboarding/preference", { user_id: userId, ...payload }, optionalString(args, "backend-url"));
    await upsertLocalUser(userId, {
        preferencePayload: saved.preference_payload ?? payload,
    });
    process.stdout.write(JSON.stringify(saved, null, 2) + "\n");
}
async function cmdGameplayList(args) {
    const response = await backendRequest("GET", "/api/v1/gameplays", undefined, optionalString(args, "backend-url"));
    process.stdout.write(JSON.stringify(response, null, 2) + "\n");
}
async function cmdGameplayRecommend(args) {
    const body = {};
    if (optionalString(args, "trigger"))
        body.trigger = optionalString(args, "trigger");
    if (optionalString(args, "desired-tags"))
        body.desired_tags = parseCsv(optionalString(args, "desired-tags"));
    if (optionalString(args, "user-goal-tags"))
        body.user_goal_tags = parseCsv(optionalString(args, "user-goal-tags"));
    if (optionalString(args, "available-tools"))
        body.available_tools = parseCsv(optionalString(args, "available-tools"));
    if (optionalString(args, "allow-one-shot"))
        body.allow_one_shot = parseToggle(optionalString(args, "allow-one-shot"));
    if (optionalString(args, "allow-loop"))
        body.allow_loop = parseToggle(optionalString(args, "allow-loop"));
    if (optionalString(args, "current-gameplay-id"))
        body.current_gameplay_id = optionalString(args, "current-gameplay-id");
    if (optionalString(args, "active-gameplay-mode"))
        body.active_gameplay_mode = optionalString(args, "active-gameplay-mode");
    if (optionalString(args, "last-completed-gameplay-id"))
        body.last_completed_gameplay_id = optionalString(args, "last-completed-gameplay-id");
    const response = await backendRequest("POST", "/api/v1/gameplays/recommend", body, optionalString(args, "backend-url"));
    process.stdout.write(JSON.stringify(response, null, 2) + "\n");
}
async function cmdGameplayPull(args) {
    const gameplayId = requireString(args, "id");
    const profile = await readProfile();
    const userId = optionalString(args, "user-id") || profile.current_user_id;
    if (!userId) {
        throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
    }
    const gameplay = await backendRequest("GET", `/api/v1/gameplays/${gameplayId}`, undefined, optionalString(args, "backend-url"));
    const workspace = await ensureWorkspace(userId);
    const targetPath = node_path_1.default.join(workspace.gameplay_cache_dir, `${gameplayId}.md`);
    await (0, promises_1.writeFile)(targetPath, serializeGameplayMarkdown(gameplay), "utf-8");
    process.stdout.write(JSON.stringify({ ok: true, gameplay_id: gameplayId, cache_path: targetPath }, null, 2) + "\n");
}
async function cmdGameplayCreate(args) {
    const profile = await readProfile();
    const userId = optionalString(args, "user-id") || profile.current_user_id;
    if (!userId) {
        throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
    }
    const gameplayId = requireString(args, "id");
    const name = requireString(args, "name");
    const summary = requireString(args, "summary");
    const workspace = await ensureWorkspace(userId);
    const outputPath = optionalString(args, "out") || node_path_1.default.join(workspace.gameplay_drafts_dir, `${gameplayId}.md`);
    const mode = optionalString(args, "mode") || "open";
    const tools = optionalString(args, "tools") ? parseCsv(optionalString(args, "tools")) : [];
    const tags = optionalString(args, "tags") ? parseCsv(optionalString(args, "tags")) : [];
    const metadata = optionalString(args, "metadata-json")
        ? JSON.parse(optionalString(args, "metadata-json"))
        : {};
    const markdown = optionalString(args, "markdown-file")
        ? await (0, promises_1.readFile)(optionalString(args, "markdown-file"), "utf-8")
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
    await (0, promises_1.writeFile)(outputPath, content, "utf-8");
    process.stdout.write(JSON.stringify({ ok: true, file: outputPath }, null, 2) + "\n");
}
async function cmdGameplayPublish(args) {
    const profile = await readProfile();
    const userId = optionalString(args, "user-id") || profile.current_user_id;
    if (!userId) {
        throw new Error("Missing user id. Use --user-id or run selfcon onboard first.");
    }
    const file = requireString(args, "file");
    const markdown = await (0, promises_1.readFile)(file, "utf-8");
    const response = await backendRequest("POST", "/api/v1/gameplays/contribute", { user_id: userId, markdown }, optionalString(args, "backend-url"));
    process.stdout.write(JSON.stringify(response, null, 2) + "\n");
}
async function copyDir(source, target) {
    await (0, promises_1.mkdir)(target, { recursive: true });
    const entries = await (0, promises_1.readdir)(source);
    for (const entry of entries) {
        const sourcePath = node_path_1.default.join(source, entry);
        const targetPath = node_path_1.default.join(target, entry);
        const sourceStat = await (0, promises_1.stat)(sourcePath);
        if (sourceStat.isDirectory()) {
            await copyDir(sourcePath, targetPath);
        }
        else {
            await (0, promises_1.mkdir)(node_path_1.default.dirname(targetPath), { recursive: true });
            await (0, promises_1.cp)(sourcePath, targetPath);
        }
    }
}
async function writeEmbeddedSkillFile(relativePath, targetPath) {
    const assetKey = embeddedSkillAssets[relativePath];
    const asset = sea.getAsset(assetKey);
    if (!asset) {
        throw new Error(`Missing embedded asset: ${relativePath}`);
    }
    await (0, promises_1.mkdir)(node_path_1.default.dirname(targetPath), { recursive: true });
    await (0, promises_1.writeFile)(targetPath, Buffer.from(asset));
}
function serializeGameplayMarkdown(data) {
    const metadata = {
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
function synthesizeGameplayMarkdown(data) {
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
