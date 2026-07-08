"use client";

import { useState, useEffect, useRef } from "react";
import { MessageSquare, Send, Plus, Menu, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { getApprovedSchemes } from "@/lib/schemes";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8001";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Scheme {
  id: string;
  name: string;
  url: string;
}

const SUGGESTED_PROMPTS = [
  "What is the expense ratio of HDFC Large Cap Fund?",
  "Tell me about HDFC Defence Fund",
  "Compare HDFC Mid Cap and Large Cap funds",
  "What are the top holdings of HDFC Equity Fund?",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [isCheckingBackend, setIsCheckingBackend] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sessionId, setSessionId] = useState(() => 
    `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  );
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setSchemes(getApprovedSchemes());
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    setIsCheckingBackend(true);
    try {
      const response = await fetch(`${backendUrl}/health`);
      const data = await response.json();
      if (data.ready) {
        setIsBackendReady(true);
      } else {
        // Retry after 2 seconds if backend is loading
        setTimeout(checkBackendHealth, 2000);
      }
    } catch (error) {
      console.error("Backend health check failed:", error);
      // Retry after 2 seconds
      setTimeout(checkBackendHealth, 2000);
    } finally {
      setIsCheckingBackend(false);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(`session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
    setIsSidebarOpen(false);
    inputRef.current?.focus();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      if (!response.ok) throw new Error("Failed to connect to backend");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = "";

      if (reader) {
        let currentEvent = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7);
            } else if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (currentEvent === "token" && data.content) {
                  assistantMessage += data.content;
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage?.role === "assistant") {
                      lastMessage.content = assistantMessage;
                    } else {
                      newMessages.push({ role: "assistant", content: assistantMessage });
                    }
                    return newMessages;
                  });
                } else if (currentEvent === "blocked") {
                  assistantMessage = "This request was blocked by the compliance layer.";
                  setMessages((prev) => [...prev, { role: "assistant", content: assistantMessage }]);
                } else if (currentEvent === "error") {
                  assistantMessage = `Error: ${data.message || "Something went wrong"}`;
                  setMessages((prev) => [...prev, { role: "assistant", content: assistantMessage }]);
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't connect to the server. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedPrompt = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-screen bg-[#f7f7f8]">
      {/* Mobile sidebar overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-72 bg-white border-r border-zinc-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Sidebar header */}
          <div className="flex items-center justify-between p-4 border-b border-zinc-200">
            <h1 className="text-lg font-semibold text-zinc-900">HDFC MF Assistant</h1>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="lg:hidden p-2 hover:bg-zinc-100 rounded-md"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* New chat button */}
          <div className="p-4">
            <button
              onClick={handleNewChat}
              className="w-full flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span className="font-medium">New Chat</span>
            </button>
          </div>

          {/* Schemes list */}
          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-sm font-medium text-zinc-500 mb-3">Supported Schemes</h2>
            <ul className="space-y-1">
              {schemes.map((scheme) => (
                <li key={scheme.id}>
                  <a
                    href={scheme.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-md transition-colors"
                  >
                    {scheme.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-zinc-200">
            <p className="text-xs text-zinc-500">
              Data sourced from Groww. Refreshed daily at 9:00 AM IST.
            </p>
          </div>
        </div>
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-zinc-200">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="lg:hidden p-2 hover:bg-zinc-100 rounded-md"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-emerald-600" />
            <h1 className="text-lg font-semibold text-zinc-900">Chat</h1>
          </div>
          <button
            onClick={handleNewChat}
            className="hidden lg:flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-100 rounded-md transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4">
          {isCheckingBackend || !isBackendReady ? (
            <div className="max-w-2xl mx-auto py-8 text-center">
              <div className="flex items-center justify-center gap-2 mb-4">
                <div className="w-3 h-3 bg-emerald-600 rounded-full animate-bounce" />
                <div className="w-3 h-3 bg-emerald-600 rounded-full animate-bounce delay-100" />
                <div className="w-3 h-3 bg-emerald-600 rounded-full animate-bounce delay-200" />
              </div>
              <h2 className="text-xl font-semibold text-zinc-900 mb-2">
                {isCheckingBackend ? "Connecting to backend..." : "Backend is waking up"}
              </h2>
              <p className="text-zinc-600">
                {isCheckingBackend 
                  ? "Please wait while we connect to the server."
                  : "The backend is starting up. This may take a few seconds on the free tier."}
              </p>
            </div>
          ) : messages.length === 0 ? (
            <div className="max-w-2xl mx-auto py-8">
              <h2 className="text-2xl font-semibold text-zinc-900 mb-2">
                Welcome to HDFC Mutual Fund Assistant
              </h2>
              <p className="text-zinc-600 mb-6">
                Ask me anything about the 21 approved HDFC Mutual Fund schemes.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className="text-left px-4 py-3 bg-white border border-zinc-200 rounded-lg hover:border-emerald-300 hover:bg-emerald-50 transition-colors text-sm text-zinc-700"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === "user"
                        ? "bg-emerald-600 text-white"
                        : "bg-white border border-zinc-200 shadow-sm"
                    }`}
                  >
                    {message.role === "assistant" ? (
                      <div className="text-zinc-900 text-sm">
                        <ReactMarkdown>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-zinc-200 rounded-lg px-4 py-3 shadow-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="p-4 bg-white border-t border-zinc-200">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="flex items-center gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about HDFC Mutual Funds..."
                className="flex-1 px-4 py-3 bg-zinc-100 border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm text-zinc-900 placeholder-zinc-500 disabled:text-zinc-400 disabled:placeholder-zinc-400"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
