import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { compile } from "json-schema-to-typescript";

const WEB_ROOT = resolve(import.meta.dirname, "..");
const REPO_ROOT = resolve(WEB_ROOT, "../..");
const SCHEMA_PATH = resolve(
  REPO_ROOT,
  "contracts/json-schema/cultureshift.contracts.schema.json",
);
const OUTPUT_PATH = resolve(WEB_ROOT, "src/generated/contracts.ts");

function normalize(text) {
  return `${text.replace(/\r\n/g, "\n").trimEnd()}\n`;
}

export function syncGeneratedFile(content, outputPath, check) {
  if (check) {
    if (!existsSync(outputPath) || readFileSync(outputPath, "utf8") !== content) {
      throw new Error("stale: src/generated/contracts.ts");
    }
    return;
  }
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, content, "utf8");
}

export async function renderContracts(schemaPath = SCHEMA_PATH) {
  const schema = JSON.parse(readFileSync(schemaPath, "utf8"));
  return normalize(
    await compile(schema, "ContractRegistry", {
      bannerComment: "/* AUTO-GENERATED FROM PYDANTIC JSON SCHEMA. DO NOT EDIT. */",
      unreachableDefinitions: true,
    }),
  );
}

export async function run({ check = false, outputPath = OUTPUT_PATH } = {}) {
  syncGeneratedFile(await renderContracts(), outputPath, check);
  console.log(`${check ? "current" : "wrote"}: src/generated/contracts.ts`);
}

const invokedDirectly =
  process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (invokedDirectly) {
  run({ check: process.argv.includes("--check") }).catch((error) => {
    const message =
      error instanceof Error && error.message.startsWith("stale:")
        ? error.message
        : "contract generation failed";
    console.error(message);
    process.exitCode = 1;
  });
}
