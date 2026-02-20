import React from 'react';
import { Bot, User, Send, Building2 } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="logo-section">
          <Building2 size={24} />
          <h1>EnterpriseHub AI</h1>
        </div>
        <nav>
          <span>War Room</span>
          <span>Market Intelligence</span>
          <span>Settings</span>
        </nav>
      </header>

      <main className="main-content">
        <section className="agent-stream">
          <div className="message bot">
            <Bot size={20} />
            <div className="content">
              <p>Welcome, Jorge. I've analyzed the latest market trends in Rancho Cucamonga. Ready to generate a personalized pitch for Lead #402?</p>
            </div>
          </div>
          
          <div className="message user">
            <User size={20} />
            <div className="content">
              <p>Yes, prioritize high-equity sellers with recent permit activity.</p>
            </div>
          </div>
        </section>

        <footer className="input-area">
          <input type="text" placeholder="Instruct the agent swarm..." />
          <button className="send-btn">
            <Send size={18} />
          </button>
        </footer>
      </main>

      <style jsx>{`
        .dashboard-container {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: #f8f9fa;
          font-family: system-ui, -apple-system, sans-serif;
        }
        .header {
          display: flex;
          justify-content: space-between;
          padding: 1rem 2rem;
          background: #fff;
          border-bottom: 1px solid #eee;
        }
        .logo-section {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #2563eb;
        }
        .main-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          max-width: 800px;
          margin: 0 auto;
          width: 100%;
          padding: 2rem;
        }
        .agent-stream {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          overflow-y: auto;
        }
        .message {
          display: flex;
          gap: 1rem;
          padding: 1rem;
          border-radius: 8px;
        }
        .bot { background: #eff6ff; }
        .user { background: #fff; border: 1px solid #eee; flex-direction: row-reverse; }
        .input-area {
          display: flex;
          gap: 1rem;
          padding: 1rem 0;
        }
        input {
          flex: 1;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 6px;
        }
        .send-btn {
          padding: 0.75rem;
          background: #2563eb;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}
