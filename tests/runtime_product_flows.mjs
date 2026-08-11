import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const moduleRoot = process.env.PGLITE_MODULE_PATH;
if (!moduleRoot) {
  throw new Error("PGLITE_MODULE_PATH must point to the @electric-sql/pglite package directory");
}
const { PGlite } = await import(pathToFileURL(path.join(moduleRoot, "dist", "index.js")).href);
const { uuid_ossp } = await import(
  pathToFileURL(path.join(moduleRoot, "dist", "contrib", "uuid_ossp.js")).href
);

const workflow = async (relativePath) =>
  JSON.parse(await readFile(path.join(root, relativePath), "utf8"));
const wf01 = await workflow("n8n/workflows/registration/WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json");
const wf03 = await workflow("n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json");
const wf05 = await workflow("n8n/workflows/catalog/WF_05_PROFILE_CATALOG_RANKING_DEV.json");
const node = (wf, name) => {
  const found = wf.nodes.find((candidate) => candidate.name === name);
  assert.ok(found, `missing node: ${name}`);
  return found;
};

const normalizeCode = node(wf01, "Normalize Telegram Event").parameters.jsCode;
const normalize = new Function("$json", normalizeCode);
const registrationSql = node(wf01, "Register or Resolve Telegram User").parameters.query;
const stateSql = node(wf01, "Apply Role and Onboarding Event").parameters.query;
const reloadSql = node(wf01, "Reload Role State").parameters.query;
const loadWomanSql = node(wf03, "Load WOMAN Draft Session").parameters.query;
const persistWomanSql = node(wf03, "Persist WOMAN Extraction").parameters.query;
const savePhotoSql = node(wf03, "Save WOMAN Photo").parameters.query;
const catalogSql = node(wf05, "Query Ranked WOMAN Catalog").parameters.query;

const db = new PGlite({ extensions: { uuid_ossp } });
await db.waitReady;
for (const file of [
  "database/migrations/001_users_and_telegram_accounts_schema.sql",
  "database/migrations/002_profiles_schema.sql",
  "database/migrations/003_moderation_schema.sql",
  "database/migrations/004_catalog_schema.sql",
  "database/migrations/008_audit_events_schema.sql",
  "database/migrations/009_woman_profile_tz02_schema.sql",
  "database/migrations/010_man_search_context_preferences_schema.sql",
]) {
  await db.exec(await readFile(path.join(root, file), "utf8"));
}

const results = [];
async function test(number, name, fn) {
  try {
    const details = await fn();
    results.push({ number, name, status: "PASS", details });
    console.log(`PASS ${String(number).padStart(2, "0")} ${name} — ${details}`);
  } catch (error) {
    results.push({ number, name, status: "FAIL", details: error.message });
    console.error(`FAIL ${String(number).padStart(2, "0")} ${name} — ${error.stack || error.message}`);
  }
}

const message = (telegramId, text, firstName = "") => ({
  message: {
    message_id: Number(telegramId) % 100000,
    text,
    from: { id: telegramId, first_name: firstName, username: `u${telegramId}` },
    chat: { id: telegramId },
  },
});
const callback = (telegramId, data, firstName = "") => ({
  callback_query: {
    id: `cb-${telegramId}-${data}`,
    data,
    from: { id: telegramId, first_name: firstName, username: `u${telegramId}` },
    message: { message_id: 1, chat: { id: telegramId } },
  },
});
const photo = (telegramId, fileId, firstName = "") => ({
  message: {
    message_id: Number(telegramId) % 100000,
    photo: [{ file_id: `${fileId}-small` }, { file_id: fileId }],
    from: { id: telegramId, first_name: firstName, username: `u${telegramId}` },
    chat: { id: telegramId },
  },
});

async function runUpdate(update) {
  const event = normalize(update)[0].json;
  const registered = (
    await db.query(registrationSql, [
      event.telegram_id,
      event.username,
      event.action,
      event.telegram_first_name,
      event.text,
    ])
  ).rows[0];
  assert.ok(registered?.user_id, "registration did not return canonical user_id");
  const state = (
    await db.query(stateSql, [
      registered.user_id,
      registered.action,
      registered.first_name,
      registered.answer,
    ])
  ).rows[0];
  const reloaded = (
    await db.query(reloadSql, [state.user_id, state.action, state.role_decision])
  ).rows[0];
  return { event, registered, state, reloaded };
}

const count = async (table, where = "TRUE", values = []) =>
  Number((await db.query(`SELECT count(*)::int count FROM ${table} WHERE ${where}`, values)).rows[0].count);
const rows = async (sql, values = []) => (await db.query(sql, values)).rows;

const manTelegramId = 910000001;
let manUserId;
let manState;
const womanTelegramId = 910000002;
let womanUserId;
let womanProfileId;
let womanSessionId;

await test(1, "new Telegram user", async () => {
  const beforeUsers = await count("users");
  const beforeAccounts = await count("telegram_accounts");
  const result = await runUpdate(message(manTelegramId, "/start", "Дмитрий"));
  manUserId = result.registered.user_id;
  assert.equal(result.event.action, "START");
  assert.equal(await count("users"), beforeUsers + 1);
  assert.equal(await count("telegram_accounts"), beforeAccounts + 1);
  const user = (await rows("SELECT role FROM users WHERE id=$1::uuid", [manUserId]))[0];
  assert.equal(user.role, null);
  return `user_id=${manUserId}; role=NULL; users/accounts +1`;
});

await test(2, "repeated and concurrent /start idempotency", async () => {
  const repeated = await runUpdate(message(manTelegramId, "/start payload", "Дмитрий"));
  assert.equal(repeated.registered.user_id, manUserId);
  assert.equal(await count("telegram_accounts", "telegram_id=$1::bigint", [manTelegramId]), 1);
  assert.equal(await count("users", "id=$1::uuid", [manUserId]), 1);
  const concurrentTelegramId = 910000099;
  const [a, b] = await Promise.all([
    runUpdate(message(concurrentTelegramId, "/start", "Параллельный")),
    runUpdate(message(concurrentTelegramId, "/start@bot payload", "Параллельный")),
  ]);
  assert.equal(a.registered.user_id, b.registered.user_id);
  assert.equal(await count("telegram_accounts", "telegram_id=$1::bigint", [concurrentTelegramId]), 1);
  const orphans = await count("users", "NOT EXISTS (SELECT 1 FROM telegram_accounts ta WHERE ta.user_id=users.id)");
  assert.equal(orphans, 0);
  return "same user_id; no duplicate account/user; no orphan user under concurrent registration";
});

await test(3, "ROLE_MAN creates exactly one context", async () => {
  const result = await runUpdate(callback(manTelegramId, "role:man", "Дмитрий"));
  manState = result.reloaded;
  assert.equal(result.state.role_decision, "ACCEPTED");
  assert.equal(result.reloaded.role, "man");
  assert.equal(await count("male_search_context", "user_id=$1::uuid", [manUserId]), 1);
  return "role=man; one male_search_context";
});

await test(4, "repeated ROLE_MAN resumes context", async () => {
  const before = (await rows("SELECT created_at,onboarding_state FROM male_search_context WHERE user_id=$1::uuid", [manUserId]))[0];
  const result = await runUpdate(callback(manTelegramId, "role:man", "Дмитрий"));
  const after = (await rows("SELECT created_at,onboarding_state FROM male_search_context WHERE user_id=$1::uuid", [manUserId]))[0];
  assert.equal(result.state.role_decision, "IDEMPOTENT");
  assert.equal(await count("male_search_context", "user_id=$1::uuid", [manUserId]), 1);
  assert.equal(String(after.created_at), String(before.created_at));
  assert.equal(after.onboarding_state, before.onboarding_state);
  return "role remains man; existing context and state reused";
});

await test(5, "opposite role callbacks are rejected", async () => {
  const rejected = await runUpdate(callback(manTelegramId, "role:woman", "Дмитрий"));
  assert.equal(rejected.state.role_decision, "REJECTED");
  assert.equal(rejected.reloaded.role, "man");
  assert.equal(await count("profiles", "user_id=$1::uuid", [manUserId]), 0);
  assert.equal(await count("profile_ai_sessions", "user_id=$1::uuid", [manUserId]), 0);
  const mirrorTelegramId = 910000098;
  await runUpdate(message(mirrorTelegramId, "/start", "Анна"));
  const womanRole = await runUpdate(callback(mirrorTelegramId, "role:woman", "Анна"));
  const mirror = await runUpdate(callback(mirrorTelegramId, "role:man", "Анна"));
  assert.equal(womanRole.reloaded.role, "woman");
  assert.equal(mirror.state.role_decision, "REJECTED");
  assert.equal(mirror.reloaded.role, "woman");
  assert.equal(await count("male_search_context", "user_id=$1::uuid", [mirror.registered.user_id]), 0);
  return "MAN→WOMAN and WOMAN→MAN rejected without opposite artifacts";
});

await test(6, "Telegram first_name proposal state", async () => {
  const context = (await rows("SELECT name,name_source,name_confirmed_at,onboarding_state FROM male_search_context WHERE user_id=$1::uuid", [manUserId]))[0];
  assert.equal(context.name, "Дмитрий");
  assert.equal(context.name_source, null);
  assert.equal(context.name_confirmed_at, null);
  assert.equal(context.onboarding_state, "AWAITING_NAME_CONFIRMATION");
  return "proposed name persisted; awaiting explicit confirmation/change";
});

await test(7, "MAN_NAME_CHANGE replaces proposed name", async () => {
  const changed = await runUpdate(callback(manTelegramId, "man_name:change", "Дмитрий"));
  assert.equal(changed.reloaded.onboarding_state, "AWAITING_MANUAL_NAME");
  const manual = await runUpdate(message(manTelegramId, "Михаил", "Дмитрий"));
  assert.equal(manual.reloaded.name, "Михаил");
  assert.equal(manual.reloaded.name_source, "MANUAL");
  assert.ok(manual.reloaded.name_confirmed_at);
  assert.equal(manual.reloaded.onboarding_state, "AWAITING_CITY");
  manState = manual.reloaded;
  return "name replaced with Михаил; source=MANUAL; next state=AWAITING_CITY";
});

await test(8, "/start during onboarding never becomes field text", async () => {
  const before = (await rows("SELECT name,city,onboarding_state FROM male_search_context WHERE user_id=$1::uuid", [manUserId]))[0];
  for (const startText of ["/start", "/start payload", "/start@bot", "/start@bot payload"]) {
    const resumed = await runUpdate(message(manTelegramId, startText, "Дмитрий"));
    assert.equal(resumed.event.action, "START");
  }
  const malformed = normalize(message(manTelegramId, "/start123", "Дмитрий"))[0].json;
  assert.equal(malformed.action, "UNKNOWN_COMMAND");
  await runUpdate(message(manTelegramId, "/start123", "Дмитрий"));
  const after = (await rows("SELECT name,city,onboarding_state FROM male_search_context WHERE user_id=$1::uuid", [manUserId]))[0];
  assert.deepEqual(after, before);
  return "all valid START forms resume; /start123 is not START; name/city unchanged";
});

await test(9, "city mutates only in AWAITING_CITY", async () => {
  const city = await runUpdate(message(manTelegramId, "  Сызрань  ", "Дмитрий"));
  assert.equal(city.reloaded.city, "Сызрань");
  assert.equal(city.reloaded.city_normalized, "сызрань");
  assert.equal(city.reloaded.onboarding_state, "COMPLETED");
  await runUpdate(message(manTelegramId, "Москва", "Дмитрий"));
  const after = (await rows("SELECT city,city_normalized,onboarding_state FROM male_search_context WHERE user_id=$1::uuid", [manUserId]))[0];
  assert.equal(after.city, "Сызрань");
  assert.equal(after.city_normalized, "сызрань");
  assert.equal(after.onboarding_state, "COMPLETED");
  manState = city.reloaded;
  return "city saved once in expected state; later arbitrary TEXT ignored";
});

await test(10, "completed MAN has no public profile", async () => {
  assert.equal(manState.onboarding_state, "COMPLETED");
  assert.equal(await count("profiles", "user_id=$1::uuid", [manUserId]), 0);
  return "MAN state=COMPLETED; profiles count=0";
});

await test(11, "first WOMAN role creates one DRAFT profile", async () => {
  await runUpdate(message(womanTelegramId, "/start", "Анна"));
  const result = await runUpdate(callback(womanTelegramId, "role:woman", "Анна"));
  womanUserId = result.registered.user_id;
  womanProfileId = result.reloaded.woman_profile_id;
  womanSessionId = result.reloaded.woman_session_id;
  assert.equal(result.reloaded.role, "woman");
  assert.equal(await count("profiles", "user_id=$1::uuid AND status='DRAFT'", [womanUserId]), 1);
  return `profile_id=${womanProfileId}; exactly one DRAFT profile`;
});

await test(12, "WOMAN has one IN_PROGRESS session", async () => {
  assert.ok(womanSessionId);
  assert.equal(await count("profile_ai_sessions", "user_id=$1::uuid AND status='IN_PROGRESS'", [womanUserId]), 1);
  const linked = (await rows("SELECT profile_id::text FROM profile_ai_sessions WHERE id=$1::uuid", [womanSessionId]))[0];
  assert.equal(linked.profile_id, womanProfileId);
  return `session_id=${womanSessionId}; linked to DRAFT profile`;
});

await test(13, "repeated WOMAN callback/start is idempotent", async () => {
  await runUpdate(callback(womanTelegramId, "role:woman", "Анна"));
  await runUpdate(message(womanTelegramId, "/start", "Анна"));
  assert.equal(await count("profiles", "user_id=$1::uuid AND status='DRAFT'", [womanUserId]), 1);
  assert.equal(await count("profile_ai_sessions", "user_id=$1::uuid AND status='IN_PROGRESS'", [womanUserId]), 1);
  return "no duplicate DRAFT profile or active session";
});

await test(14, "WF_01 text handoff reaches WF_03 session contract", async () => {
  const update = normalize(message(womanTelegramId, "Меня зовут Анна", "Анна"))[0].json;
  assert.equal(update.action, "TEXT");
  const loaded = (await db.query(loadWomanSql, [womanUserId, womanSessionId, womanProfileId])).rows;
  assert.equal(loaded.length, 1);
  assert.equal(loaded[0].session_id, womanSessionId);
  const handoff = node(wf01, "Handoff WOMAN Event to WF_03");
  assert.equal(handoff.parameters.url, "={{$env.WF_03_TRIGGER_URL}}");
  for (const key of ["telegram_id", "chat_id", "update_type", "message_text", "user_id", "profile_id", "session_id"]) {
    assert.ok(handoff.parameters.body.includes(key));
  }
  return "TEXT classified; explicit webhook payload resolves the exact WF_03 session/profile";
});

await test(15, "WF_01 photo handoff reaches WF_03 session contract", async () => {
  const update = normalize(photo(womanTelegramId, "tg-photo-handoff", "Анна"))[0].json;
  assert.equal(update.action, "PHOTO");
  assert.equal(update.photo_file_id, "tg-photo-handoff");
  const loaded = (await db.query(loadWomanSql, [womanUserId, womanSessionId, womanProfileId])).rows;
  assert.equal(loaded.length, 1);
  assert.equal(loaded[0].profile_id, womanProfileId);
  assert.ok(node(wf01, "Handoff WOMAN Event to WF_03").parameters.body.includes("photo_file_id"));
  return "PHOTO classified with largest Telegram file_id; exact resumable handler found";
});

await test(16, "prices append without silent overwrite", async () => {
  const payload = (service_name, amount) => JSON.stringify({
    fields: {},
    price_operations: [{ operation: "APPEND", service_name, amount, currency: "RUB", duration_minutes: 60, description: null }],
    meeting_place_operations: [],
  });
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, payload("Цена A", 1000)]);
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, payload("Цена B", 2000)]);
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, payload("Цена C", 3000)]);
  const temporary = (await rows("SELECT id::text FROM profile_prices WHERE profile_id=$1::uuid AND service_name='Цена C'", [womanProfileId]))[0];
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, JSON.stringify({
    fields: {},
    price_operations: [{ operation: "UPDATE", id: temporary.id, service_name: "Цена C2", amount: 3500, currency: "RUB", duration_minutes: 60, description: null }],
    meeting_place_operations: [],
  })]);
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, JSON.stringify({
    fields: {},
    price_operations: [{ operation: "DELETE", id: temporary.id }],
    meeting_place_operations: [],
  })]);
  const actual = await rows("SELECT service_name,position FROM profile_prices WHERE profile_id=$1::uuid AND is_active ORDER BY position", [womanProfileId]);
  assert.deepEqual(actual.map((x) => x.service_name), ["Цена A", "Цена B"]);
  assert.deepEqual(actual.map((x) => Number(x.position)), [0, 1]);
  return "price A and B both active at positions 0 and 1; explicit UPDATE/DELETE also executed";
});

await test(17, "meeting places append without silent overwrite", async () => {
  const payload = (label, place_type) => JSON.stringify({
    fields: {},
    price_operations: [],
    meeting_place_operations: [{ operation: "APPEND", place_type, label, district: null, description: null }],
  });
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, payload("Место A", "HOTEL")]);
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, payload("Место B", "PUBLIC_PLACE")]);
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, payload("Место C", "OTHER")]);
  const temporary = (await rows("SELECT id::text FROM profile_meeting_places WHERE profile_id=$1::uuid AND label='Место C'", [womanProfileId]))[0];
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, JSON.stringify({
    fields: {},
    price_operations: [],
    meeting_place_operations: [{ operation: "UPDATE", id: temporary.id, place_type: "OTHER", label: "Место C2", district: null, description: null }],
  })]);
  await db.query(persistWomanSql, [womanProfileId, womanSessionId, JSON.stringify({
    fields: {},
    price_operations: [],
    meeting_place_operations: [{ operation: "DELETE", id: temporary.id }],
  })]);
  const actual = await rows("SELECT label,position FROM profile_meeting_places WHERE profile_id=$1::uuid AND is_active ORDER BY position", [womanProfileId]);
  assert.deepEqual(actual.map((x) => x.label), ["Место A", "Место B"]);
  assert.deepEqual(actual.map((x) => Number(x.position)), [0, 1]);
  return "place A and B both active at positions 0 and 1; explicit UPDATE/DELETE also executed";
});

await test(18, "concurrent WOMAN photos are preserved and deduplicated", async () => {
  await Promise.all([
    db.query(savePhotoSql, [womanProfileId, "tg-concurrent-A"]),
    db.query(savePhotoSql, [womanProfileId, "tg-concurrent-B"]),
  ]);
  await db.query(savePhotoSql, [womanProfileId, "tg-concurrent-A"]);
  const actual = await rows("SELECT telegram_file_id,position FROM profile_photos WHERE profile_id=$1::uuid ORDER BY position", [womanProfileId]);
  assert.equal(actual.length, 2);
  assert.equal(new Set(actual.map((x) => x.telegram_file_id)).size, 2);
  assert.equal(new Set(actual.map((x) => Number(x.position))).size, 2);
  return "two distinct photos stored at distinct positions; repeated file_id deduplicated";
});

const catalogSameCityIds = [];
let catalogOtherCityId;
let catalogPendingId;
let catalogManOwnedId;
async function insertProfile(role, status, city, age, name) {
  const user = (await rows("INSERT INTO users(role) VALUES($1) RETURNING id::text", [role]))[0];
  return (await rows("INSERT INTO profiles(user_id,status,name,age,city,city_normalized,created_at) VALUES($1::uuid,$2,$3,$4,$5,normalize_city_name($5),now()) RETURNING id::text", [user.id, status, name, age, city]))[0].id;
}

await test(19, "catalog without preferences returns all same-city ACTIVE WOMAN profiles", async () => {
  catalogSameCityIds.push(await insertProfile("woman", "ACTIVE", "Сызрань", 22, "Каталог 22"));
  catalogSameCityIds.push(await insertProfile("woman", "ACTIVE", "Сызрань", 35, "Каталог 35"));
  catalogSameCityIds.push(await insertProfile("woman", "ACTIVE", "Сызрань", 45, "Каталог 45"));
  catalogOtherCityId = await insertProfile("woman", "ACTIVE", "Москва", 25, "Другой город");
  catalogPendingId = await insertProfile("woman", "PENDING_MODERATION", "Сызрань", 25, "Неактивная");
  catalogManOwnedId = await insertProfile("man", "ACTIVE", "Сызрань", 25, "MAN-owned");
  const actual = await db.query(catalogSql, [manUserId, 50, 0]);
  assert.deepEqual(new Set(actual.rows.map((x) => x.id)), new Set(catalogSameCityIds));
  assert.ok(actual.rows.every((x) => Number(x.considered_preferences) === 0 && Number(x.match_score) === 0));
  return `returned all ${actual.rows.length} ACTIVE WOMAN profiles in normalized city; score=0`;
});

await test(20, "preferences change only ranking, not candidate set", async () => {
  await db.query("INSERT INTO male_search_preferences(user_id,age_from,age_to) VALUES($1::uuid,20,30)", [manUserId]);
  const actual = await db.query(catalogSql, [manUserId, 50, 0]);
  assert.deepEqual(new Set(actual.rows.map((x) => x.id)), new Set(catalogSameCityIds));
  assert.equal(actual.rows[0].id, catalogSameCityIds[0]);
  assert.equal(Number(actual.rows[0].matched_preferences), 1);
  assert.equal(Number(actual.rows[0].considered_preferences), 1);
  assert.equal(Number(actual.rows[0].match_score), 1);
  assert.ok(actual.rows.slice(1).every((x) => Number(x.match_score) === 0));
  return "same candidate IDs; age preference changes score/order only";
});

await test(21, "catalog hard filters exclude wrong city/status/owner", async () => {
  const actual = await db.query(catalogSql, [manUserId, 50, 0]);
  const ids = new Set(actual.rows.map((x) => x.id));
  assert.equal(ids.has(catalogOtherCityId), false);
  assert.equal(ids.has(catalogPendingId), false);
  assert.equal(ids.has(catalogManOwnedId), false);
  assert.deepEqual(ids, new Set(catalogSameCityIds));
  return "wrong city, non-ACTIVE, and MAN-owned profiles excluded";
});

await db.close();
const failures = results.filter((result) => result.status === "FAIL");
console.log(`SUMMARY: ${results.length - failures.length}/${results.length} PASS`);
if (failures.length) process.exitCode = 1;
