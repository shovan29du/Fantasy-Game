import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const pages = ["Chat", "Characters", "Explore", "World", "Media", "Knowledge", "Settings"];

function App() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <h1>AiChat Pro</h1>
        {pages.map((page) => <button key={page}>{page}</button>)}
      </aside>
      <section className="workspace">
        <p className="eyebrow">React/Vite migration shell</p>
        <h2>Backend-safe frontend replacement path</h2>
        <p>
          This app shell is ready to consume endpoints backed by
          <code> backend.app.services</code> while the Streamlit UI remains available.
        </p>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
