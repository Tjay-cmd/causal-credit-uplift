import { promises as fs } from "fs";
import path from "path";
import type { Phase1Data, Phase2Data } from "./types";

async function readJson<T>(filename: string): Promise<T | null> {
  try {
    const filePath = path.join(process.cwd(), "public", "data", filename);
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export async function loadPhase1(): Promise<Phase1Data | null> {
  return readJson<Phase1Data>("phase1.json");
}

export async function loadPhase2(): Promise<Phase2Data | null> {
  return readJson<Phase2Data>("phase2.json");
}
