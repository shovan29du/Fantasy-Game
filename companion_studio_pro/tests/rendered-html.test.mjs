import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/", {headers:{accept:"text/html"}}), {ASSETS:{fetch:async()=>new Response("Not found",{status:404})}}, {waitUntil(){},passThroughOnException(){}});
}

test("server-renders Companion Studio intelligence tools", async()=>{
  const response=await render();assert.equal(response.status,200);const html=await response.text();
  assert.match(html,/<title>Companion Reel/);assert.match(html,/Subtitle, notes and file reader/);assert.match(html,/Models and services/);assert.match(html,/Custom avatar file reader/);assert.match(html,/Adjustable text-to-video/);assert.match(html,/create separately timed English subtitles/);assert.match(html,/CC-BY-NC-4\.0/);assert.doesNotMatch(html,/Your site is taking shape/);
});

test("ships editor, model manager, subtitle editing and narration export",async()=>{
  const [page,api,services,installer]=await Promise.all([
    readFile(new URL("../app/page.tsx",import.meta.url),"utf8"),readFile(new URL("../local_api/intelligence.py",import.meta.url),"utf8"),readFile(new URL("../local_api/services.py",import.meta.url),"utf8"),readFile(new URL("../full_install.py",import.meta.url),"utf8")]);
  assert.match(page,/Editable timestamped subtitles/);assert.match(page,/Export MP3/);assert.match(page,/modelAction/);assert.match(api,/word_timestamps=True/);assert.match(api,/scene,0\.28/);assert.match(api,/video-extracted-assets\.zip/);assert.match(services,/models\/pull/);assert.match(installer,/--diagnose/);assert.match(installer,/--uninstall/);
});
