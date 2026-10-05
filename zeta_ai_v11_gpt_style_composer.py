"""
ZETA AI V7 — ULTIMATE DESKTOP PROTOTYPE
Python + CustomTkinter only.

Core:
- Gemini + OpenAI + Local Core
- JNV Study Mode / Explain / Notes / Quiz / Revision
- Project Advisor
- Developer Mode / Ultimate Developer Mode
- Research Workspace (OpenAI web_search when available)
- File Analyzer for text/PDF/image (provider dependent)
- File Maker / Workspace export
- Local personal + chat memory
- Tone adaptation
- Voice input + TTS
- Safe device actions: open browser, open VS Code, open files/folders
- Custom themes
- Motivational mode
- Presentation / Lecture mode
- Feature Center with Free / Pro / Pro+ architecture
- Offline indicator
- Startup/self-open helper
- Google Login / Cloud / payments: architecture screen; secure backend required for production

IMPORTANT:
Public web deployment must use:
Browser -> ZETA Backend -> AI providers
Never put provider API keys in browser code.
"""

import os, json, threading, platform, subprocess, webbrowser, urllib.request, urllib.error, time, csv, sqlite3, shutil, re, base64
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Optional packages
try:
    from google import genai
except Exception:
    genai = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import pypdf
except Exception:
    pypdf = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import psutil
except Exception:
    psutil = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:
    SimpleDocTemplate = Paragraph = Spacer = getSampleStyleSheet = None

try:
    from docx import Document
except Exception:
    Document = None

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None


APP = "ZETA AI"
VER = "11.1 HUD COMMAND CENTER"
DATA = Path.home() / ".zeta_ai"
DATA.mkdir(exist_ok=True)

MEM = DATA / "memory.json"
HIST = DATA / "history.json"
SET = DATA / "settings.json"
PROFILE = DATA / "profile.json"

GEMINI_MODEL = "gemini-3.8-flash"
# Fallback order: latest -> stable/efficient alternatives.
GEMINI_FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]
OPENAI_MODEL = "gpt-5.6-luna"

BG = "#090D14"
PANEL = "#111827"
PANEL2 = "#0D1420"
BORDER = "#1E3A5F"
TEXT = "#EAF4FF"
MUTED = "#8CA3BA"
CYAN = "#00D9FF"
BLUE = "#3B82F6"
GREEN = "#39FF88"
PURPLE = "#A855F7"
RED = "#FF5577"
YELLOW = "#FFD166"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default


def save(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def internet_available():
    try:
        urllib.request.urlopen("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False


class LocalCore:
    """Small offline brain. It does not pretend to be a full offline LLM."""

    def ask(self, q):
        low = q.lower()
        now = datetime.now()

        if any(x in low for x in ["time", "समय", "टाइम"]):
            return f"Local time: {now.strftime('%I:%M:%S %p')}"

        if any(x in low for x in ["date", "तारीख", "दिनांक"]):
            return f"आज: {now.strftime('%d %B %Y')}"

        if "battery" in low or "बैटरी" in low:
            if psutil:
                try:
                    b = psutil.sensors_battery()
                    if b:
                        state = "Charging" if b.power_plugged else "Not charging"
                        return f"Battery: {b.percent:.0f}% | {state}"
                except Exception:
                    pass
            return "Battery information unavailable."

        if "offline" in low or "ऑफलाइन" in low:
            return ("Offline Core active. Local memory, chat history, file creation, "
                    "basic device tools, date/time and study templates remain available.")

        if low.strip() in ["hi", "hello", "hey", "नमस्ते", "हाय"]:
            return "नमस्ते Daksh Boss. ZETA Local Core online है।"

        if "motivat" in low or "मोटिव" in low:
            return "आज का mission: छोटा step लो, उसे पूरा करो, फिर अगला level unlock करो. 🚀"

        return None


# ZETA AI V8 — Speed Optimized
# Fast path + short retries + 18s Gemini timeout + compact generation output.

class ZetaAI:
    def __init__(self):
        self.engine = "Gemini"
        self.gkey = os.getenv("GEMINI_API_KEY", "").strip()
        self.okey = os.getenv("OPENAI_API_KEY", "").strip()
        self.gmodel = GEMINI_MODEL
        self.omodel = OPENAI_MODEL

        self.memory = load(MEM, [])
        self.history = load(HIST, [])
        self.profile = load(PROFILE, {
            "name": "Daksh Boss",
            "tone": "Friendly",
            "theme": "Cyber Blue"
        })

        self.g = None
        self.o = None
        self.local = LocalCore()
        self.configure()

    def configure(self):
        self.g = None
        self.o = None

        if self.gkey and genai:
            try:
                self.g = genai.Client(api_key=self.gkey)
            except Exception:
                pass

        if self.okey and OpenAI:
            try:
                self.o = OpenAI(api_key=self.okey, timeout=30.0)
            except Exception:
                pass

    def save_state(self):
        save(MEM, self.memory[-200:])
        save(HIST, self.history[-500:])
        save(PROFILE, self.profile)

    def remember(self, item):
        item = item.strip()
        if item:
            self.memory = (self.memory + [item])[-200:]
            self.save_state()

    def forget_last(self):
        if self.memory:
            return self.memory.pop()
        return None

    def memory_context(self):
        return "\n".join(f"- {x}" for x in self.memory[-15:])

    def system_prompt(self, extra=""):
        tone = self.profile.get("tone", "Friendly")
        name = self.profile.get("name", "Daksh Boss")
        base = (
            f"You are ZETA AI, a practical AI workspace assistant. "
            f"User name: {name}. Preferred tone: {tone}. "
            "Use simple Hindi/Hinglish when appropriate, while keeping technical terms in English. "
            "Be accurate, transparent about uncertainty, and never invent sources. "
            "For school work, teach rather than merely dump answers. "
            "For engineering, give safe educational guidance and avoid dangerous/high-voltage instructions."
        )
        return base + ("\n" + extra if extra else "")

    def _gemini_rest(self, prompt, system, model):
        """Call one Gemini model with retry/backoff and return text."""
        if not self.gkey:
            raise RuntimeError("Gemini API key is not configured.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.gkey}"
        )

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "system_instruction": {"parts": [{"text": system}]},
            "generationConfig": {
                "maxOutputTokens": 1200,
                "temperature": 0.5
            }
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        retryable = {408, 429, 500, 502, 503, 504}
        last = None

        # A few retries for transient provider/quota/capacity errors.
        for attempt in range(2):
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=18) as response:
                    obj = json.loads(response.read().decode("utf-8"))

                parts = []
                for cand in obj.get("candidates", []) or []:
                    for part in (cand.get("content", {}) or {}).get("parts", []) or []:
                        if part.get("text"):
                            parts.append(part["text"])

                answer = "\n".join(parts).strip()
                if answer:
                    return answer

                raise RuntimeError(f"{model} returned no text.")

            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                last = f"HTTP {e.code}: {detail[:700]}"

                # 400/401/403/404 usually need configuration/model/key changes,
                # so don't waste time retrying them.
                if e.code not in retryable or attempt >= 1:
                    raise RuntimeError(
                        f"Gemini model '{model}' failed — {last}"
                    ) from e

                time.sleep(0.35 if attempt == 0 else 0.8)

            except (urllib.error.URLError, TimeoutError) as e:
                last = f"Network/timeout: {e}"
                if attempt >= 1:
                    raise RuntimeError(
                        f"Gemini model '{model}' failed — {last}"
                    ) from e
                time.sleep(0.35 if attempt == 0 else 0.8)

        raise RuntimeError(
            f"Gemini model '{model}' failed after retries — {last or 'unknown error'}"
        )

    def _gemini_with_fallback(self, prompt, system):
        """Try Gemini models in order; retry each transient failure."""
        errors = []

        models = []
        for model in [self.gmodel] + GEMINI_FALLBACK_MODELS:
            if model and model not in models:
                models.append(model)

        for model in models:
            try:
                answer = self._gemini_rest(prompt, system, model)

                # Remember the working model for the current session.
                self.gmodel = model
                return answer, model, errors

            except Exception as exc:
                errors.append(f"{model}: {exc}")

        detail = "\n".join(f"• {x}" for x in errors)
        raise RuntimeError(
            "All Gemini models failed.\n"
            "Gemini fallback chain was exhausted.\n\n"
            f"{detail}"
        )

    def _gemini_stream(self, prompt, system, model, on_chunk):
        """Low-latency Gemini SSE streaming for text-only chat."""
        if not self.gkey:
            raise RuntimeError("Gemini API key is not configured.")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:streamGenerateContent?alt=sse&key={self.gkey}"
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "system_instruction": {"parts": [{"text": system}]},
            "generationConfig": {"maxOutputTokens": 1200, "temperature": 0.5}
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
            method="POST"
        )
        parts = []
        with urllib.request.urlopen(req, timeout=18) as response:
            for raw in response:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                obj = json.loads(payload)
                for cand in obj.get("candidates", []) or []:
                    for part in (cand.get("content", {}) or {}).get("parts", []) or []:
                        text_part = part.get("text") or ""
                        if text_part:
                            parts.append(text_part)
                            on_chunk(text_part)
        answer = "".join(parts).strip()
        if not answer:
            raise RuntimeError(f"Gemini model '{model}' returned no streamed text.")
        return answer

    def _openai_stream(self, prompt, system, research, on_chunk):
        if not self.okey:
            raise RuntimeError("OpenAI API key is not configured.")
        if not self.o:
            self.configure()
        if not self.o:
            raise RuntimeError("OpenAI client unavailable.")
        kwargs = {"model": self.omodel, "instructions": system, "input": prompt}
        if research:
            kwargs["tools"] = [{"type": "web_search"}]
        parts = []
        stream = self.o.responses.create(**kwargs, stream=True)
        for event in stream:
            et = getattr(event, "type", "")
            if et == "response.output_text.delta":
                delta = getattr(event, "delta", "") or ""
                if delta:
                    parts.append(delta)
                    on_chunk(delta)
        answer = "".join(parts).strip()
        if not answer:
            raise RuntimeError("OpenAI returned an empty streamed response.")
        return answer

    def ask_stream(self, prompt, system_extra="", research=False, file_path=None, on_chunk=None):
        """Stream normal text chat; fall back to the existing reliable ask() path."""
        on_chunk = on_chunk or (lambda _x: None)
        local_answer = self.local.ask(prompt)
        local_exact = prompt.strip().lower()
        local_triggers = {
            "time", "what time is it", "समय", "टाइम", "date", "today's date",
            "आज की तारीख", "तारीख", "battery", "battery status", "बैटरी",
            "offline", "ऑफलाइन", "hello", "hi", "hey", "नमस्ते", "हाय"
        }
        if self.engine == "Local" or (local_answer and local_exact in local_triggers):
            answer = local_answer or self.local.ask(prompt) or "Local Core ready."
            on_chunk(answer)
            return answer

        # Attachments use the existing non-streaming multimodal path.
        if file_path:
            answer = self.ask(prompt, system_extra, research, file_path)
            on_chunk(answer)
            return answer

        context = self.memory_context()
        full = (f"Relevant local memory:\n{context}\n\n" if context else "") + prompt
        system = self.system_prompt(system_extra)
        try:
            if self.engine == "Gemini":
                if not self.gkey:
                    raise RuntimeError("Gemini API key नहीं मिली. Settings में key डालें.")
                models = []
                for model in [self.gmodel] + GEMINI_FALLBACK_MODELS:
                    if model and model not in models:
                        models.append(model)
                errors = []
                for model in models:
                    try:
                        answer = self._gemini_stream(full, system, model, on_chunk)
                        self.gmodel = model
                        break
                    except Exception as exc:
                        errors.append(f"{model}: {exc}")
                else:
                    # Let the established Gemini -> OpenAI fallback handle recovery.
                    answer = self.ask(prompt, system_extra, research, None)
                    if answer:
                        on_chunk(answer)
            else:
                answer = self._openai_stream(full, system, research, on_chunk)

            self.history.append({
                "time": datetime.now().isoformat(timespec="seconds"),
                "engine": self.engine,
                "user": prompt,
                "assistant": answer
            })
            self.save_state()
            return answer
        except Exception:
            # Final recovery uses the proven non-streaming path.
            answer = self.ask(prompt, system_extra, research, file_path)
            on_chunk(answer)
            return answer

    def ask(self, prompt, system_extra="", research=False, file_path=None):
        if self.engine == "Local":
            return self.local.ask(prompt) or (
                "Local Core does not have a full offline LLM installed. "
                "You can add a local model later."
            )

        # Fast-path: answer only clearly local utility commands without a cloud round-trip.
        local_answer = self.local.ask(prompt)
        local_exact = prompt.strip().lower()
        local_triggers = {
            "time", "what time is it", "समय", "टाइम",
            "date", "today's date", "आज की तारीख", "तारीख",
            "battery", "battery status", "बैटरी",
            "offline", "ऑफलाइन", "hello", "hi", "hey", "नमस्ते", "हाय"
        }
        if local_answer and local_exact in local_triggers:
            return local_answer

        context = self.memory_context()
        full = (
            f"Relevant local memory:\n{context}\n\n" if context else ""
        ) + prompt
        system = self.system_prompt(system_extra)

        try:
            if self.engine == "Gemini":
                if not self.gkey:
                    return (
                        "⚠️ GEMINI CONFIG ERROR\n\n"
                        "Gemini API key नहीं मिली. Settings → Gemini API में key डालें."
                    )

                # File analysis: use the SDK, with the same model fallback chain.
                if file_path and self.g:
                    errors = []
                    models = []
                    for model in [self.gmodel] + GEMINI_FALLBACK_MODELS:
                        if model and model not in models:
                            models.append(model)

                    answer = ""
                    used_model = None

                    for model in models:
                        for attempt in range(2):
                            try:
                                contents = [full]
                                contents.append(self.g.files.upload(file=str(file_path)))

                                from google.genai import types
                                cfg = types.GenerateContentConfig(
                                    system_instruction=system
                                )
                                response = self.g.models.generate_content(
                                    model=model,
                                    contents=contents,
                                    config=cfg
                                )
                                answer = (getattr(response, "text", "") or "").strip()

                                if answer:
                                    used_model = model
                                    break

                            except Exception as exc:
                                errors.append(
                                    f"{model} attempt {attempt + 1}: {exc}"
                                )
                                if attempt < 1:
                                    time.sleep(0.4)

                        if answer:
                            break

                    if not answer:
                        raise RuntimeError(
                            "Gemini file analysis failed on all fallback models.\n"
                            + "\n".join("• " + x for x in errors[-8:])
                        )

                    self.gmodel = used_model
                else:
                    answer, used_model, gemini_errors = self._gemini_with_fallback(
                        full, system
                    )

            else:
                if not self.okey:
                    return "OpenAI API key नहीं मिली. Settings में key डालें."
                if not self.o:
                    self.configure()
                if not self.o:
                    raise RuntimeError("OpenAI client unavailable.")

                kwargs = {
                    "model": self.omodel,
                    "instructions": system,
                    "input": full
                }
                if research:
                    kwargs["tools"] = [{"type": "web_search"}]

                response = self.o.responses.create(**kwargs)
                answer = (getattr(response, "output_text", "") or "").strip()

                if not answer:
                    raise RuntimeError("OpenAI returned an empty response.")

            self.history.append({
                "time": datetime.now().isoformat(timespec="seconds"),
                "engine": self.engine,
                "user": prompt,
                "assistant": answer
            })
            self.save_state()
            return answer

        except Exception as e:
            # Automatic Gemini -> OpenAI fallback
            if self.engine == "Gemini" and self.okey:
                try:
                    if not self.o:
                        self.configure()
                    if self.o:
                        kwargs = {
                            "model": self.omodel,
                            "instructions": system,
                            "input": full
                        }
                        if research:
                            kwargs["tools"] = [{"type": "web_search"}]

                        response = self.o.responses.create(**kwargs)
                        answer = (getattr(response, "output_text", "") or "").strip()
                        if answer:
                            return "[Gemini unavailable → OpenAI fallback]\n\n" + answer
                except Exception:
                    pass

            if self.engine == "Gemini":
                return (
                    "⚠️ ZETA GEMINI RECOVERY FAILED\n\n"
                    f"{e}\n\n"
                    "What ZETA already tried:\n"
                    "1. Automatic retry with backoff\n"
                    "2. Gemini model fallback chain\n"
                    "3. OpenAI fallback (if an OpenAI key is configured)\n\n"
                    "Next checks:\n"
                    "• Verify the Gemini API key in Settings\n"
                    "• Check internet connection\n"
                    "• Check provider quota/access\n"
                    "• If this is a temporary 429/5xx error, try again shortly."
                )

            return (
                f"{self.engine} ERROR:\n{type(e).__name__}: {e}\n\n"
                "Check API key, internet, model access and provider quota."
            )


class ZetaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP} — {VER}")
        self.geometry("1500x940")
        self.minsize(1180, 760)
        self.configure(fg_color=BG)

        self.ai = ZetaAI()
        self.current_file = None
        self.busy = False
        self.page_widgets = {}

        self.nav_items = [
            ("Dashboard", "⌂"),
            ("Study Mode", "▣"),
            ("Project Advisor", "◆"),
            ("Developer Mode", "</>"),
            ("Research", "◎"),
            ("Creator Studio", "✦"),
            ("Memory", "◈"),
            ("Device Hub", "◉"),
            ("Feature Center", "★"),
            ("Smart Tools", "✧"),
            ("Agent Center", "⚡"),
            ("Knowledge Base", "⌘"),
            ("Data Lab", "▤"),
            ("Media Analyzer", "◍"),
            ("Routine Center", "◷"),
            ("System Control", "⌁"),
            ("Image Lab", "▧"),
            ("Business Workspace", "◇"),
            ("Export Center", "⇩"),
            ("Account & Cloud", "☁"),
            ("Settings", "⚙")
        ]

        self._build_shell()
        self.show_page("Dashboard")
        self.after(800, self.refresh_status)

    # ---------- UI shell ----------
    def _build_shell(self):
        # Responsive animated shell: collapsible/scrollable navigation + sliding rail.
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar_expanded = True
        self.sidebar_width_expanded = 220
        self.sidebar_width_collapsed = 76
        self.sidebar_animating = False

        self.sidebar = ctk.CTkFrame(
            self, width=self.sidebar_width_expanded, corner_radius=0, fg_color="#070B12"
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.brand_row = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=70)
        self.brand_row.pack(fill="x", padx=10, pady=(14, 4))
        self.brand_row.grid_columnconfigure(1, weight=1)

        self.sidebar_toggle = ctk.CTkButton(
            self.brand_row, text="☰", width=42, height=38,
            fg_color=PANEL, hover_color="#16314A",
            command=self.toggle_sidebar
        )
        self.sidebar_toggle.grid(row=0, column=0, padx=(0, 8), pady=4)

        self.brand_label = ctk.CTkLabel(
            self.brand_row, text="Z  ZETA AI", text_color=CYAN,
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.brand_label.grid(row=0, column=1, sticky="w")

        self.brand_subtitle = ctk.CTkLabel(
            self.sidebar, text="EK AI WORKSPACE", text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        self.brand_subtitle.pack(anchor="w", padx=24, pady=(0, 8))

        # Scrollable navigation prevents the 20+ workspaces from being cut off.
        self.nav_scroll = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#1B3550", scrollbar_button_hover_color="#28557A"
        )
        self.nav_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.nav_buttons = {}
        for name, icon in self.nav_items:
            button = ctk.CTkButton(
                self.nav_scroll,
                text=f"  {icon}   {name}",
                anchor="w", height=40,
                fg_color="transparent", hover_color="#13243A",
                command=lambda x=name: self.show_page(x)
            )
            button.pack(fill="x", padx=6, pady=2)
            self.nav_buttons[name] = button

        self.sidebar_footer = ctk.CTkLabel(
            self.sidebar,
            text="FREE • PRO • PRO+\nLOCAL ↔ CLOUD\nONLINE ↔ OFFLINE",
            text_color=MUTED, justify="left"
        )
        self.sidebar_footer.pack(anchor="w", padx=22, pady=12)

        self.topbar = ctk.CTkFrame(
            self, height=70, corner_radius=0, fg_color=PANEL2
        )
        self.topbar.grid(row=0, column=1, sticky="ew")
        self.topbar.grid_columnconfigure(2, weight=1)

        # Always-visible topbar rail control.
        self.topbar_toggle = ctk.CTkButton(
            self.topbar, text="☰", width=42, height=38,
            fg_color=PANEL, hover_color="#16314A",
            command=self.toggle_sidebar
        )
        self.topbar_toggle.grid(row=0, column=0, padx=(12, 8), pady=15)

        self.page_title = ctk.CTkLabel(
            self.topbar, text="Dashboard",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.page_title.grid(row=0, column=1, padx=5, pady=17, sticky="w")

        self.status = ctk.CTkLabel(
            self.topbar, text="● CHECK HO RAHA HAI", text_color=YELLOW
        )
        self.status.grid(row=0, column=3, sticky="e", padx=10)

        self.engine_var = ctk.StringVar(value=self.ai.engine)
        ctk.CTkOptionMenu(
            self.topbar, values=["Gemini", "OpenAI", "Local"],
            variable=self.engine_var, command=self.change_engine, width=120
        ).grid(row=0, column=4, padx=15)

        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew")

        # Smooth initial state; keep keyboard-friendly shortcut.
        self.bind("<Control-b>", lambda e: self.toggle_sidebar())

    def toggle_sidebar(self):
        """Animate the navigation rail between full and compact modes."""
        if self.sidebar_animating:
            return
        self.sidebar_animating = True
        self.sidebar_expanded = not self.sidebar_expanded
        target = self.sidebar_width_expanded if self.sidebar_expanded else self.sidebar_width_collapsed
        start = self.sidebar.winfo_width() or (self.sidebar_width_collapsed if not self.sidebar_expanded else self.sidebar_width_expanded)
        steps = 14
        delta = (target - start) / steps

        def frame(i=0):
            if i >= steps:
                self.sidebar.configure(width=target)
                self._apply_sidebar_state()
                self.sidebar_animating = False
                return
            width = int(start + delta * (i + 1))
            self.sidebar.configure(width=width)
            # Keep the animation fluid without blocking the UI thread.
            self.after(15, lambda: frame(i + 1))

        frame()

    def _apply_sidebar_state(self):
        expanded = self.sidebar_expanded
        self.sidebar_toggle.configure(text="☰" if expanded else "›")
        self.topbar_toggle.configure(text="☰" if expanded else "‹")
        self.brand_label.configure(text="Z  ZETA AI" if expanded else "Z")
        self.brand_subtitle.configure(text="EK AI WORKSPACE" if expanded else "AI")
        self.sidebar_footer.configure(
            text="FREE • PRO • PRO+\nLOCAL ↔ CLOUD\nONLINE ↔ OFFLINE" if expanded else "AI\n↕\nOFF"
        )

        for name, icon in self.nav_items:
            btn = self.nav_buttons.get(name)
            if not btn:
                continue
            btn.configure(
                text=(f"  {icon}   {name}" if expanded else icon),
                anchor="w" if expanded else "center"
            )

    def expand_sidebar(self):
        if not self.sidebar_expanded and not self.sidebar_animating:
            self.toggle_sidebar()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_page(self, name):
        self.page_title.configure(text=name)

        for n, button in self.nav_buttons.items():
            button.configure(
                fg_color="#12304A" if n == name else "transparent",
                text_color=CYAN if n == name else TEXT
            )

        self.clear_content()
        route = {"Account & Cloud": "page_account_cloud"}.get(name, "page_" + name.lower().replace(" ", "_"))
        method = getattr(self, route, self.page_dashboard)
        method()

    def header(self, title, subtitle=""):
        ctk.CTkLabel(
            self.content,
            text=title,
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", padx=30, pady=(24, 2))

        if subtitle:
            ctk.CTkLabel(
                self.content, text=subtitle, text_color=MUTED
            ).pack(anchor="w", padx=30)

    def output_box(self, height=350):
        box = ctk.CTkTextbox(
            self.content,
            height=height,
            fg_color="#080F18",
            border_width=1,
            border_color=BORDER
        )
        box.pack(fill="both", expand=True, padx=30, pady=10)
        return box

    def run_streaming(self, fn, on_chunk, callback):
        def worker():
            try:
                result = fn(lambda chunk: self.after(0, lambda c=chunk: on_chunk(c)))
            except Exception as exc:
                result = f"ERROR: {type(exc).__name__}: {exc}"
            self.after(0, lambda: callback(result))
        threading.Thread(target=worker, daemon=True).start()

    def run_async(self, fn, callback):
        def worker():
            try:
                result = fn()
            except Exception as exc:
                result = f"ERROR: {type(exc).__name__}: {exc}"

            self.after(0, lambda: callback(result))

        threading.Thread(target=worker, daemon=True).start()

    def write_output(self, box, text):
        try:
            box.delete("1.0", "end")
            box.insert("end", str(text))
            box.see("end")
        except Exception:
            pass

    # ---------- status ----------
    def change_engine(self, engine):
        self.ai.engine = engine
        self.refresh_status()

    def refresh_status(self):
        online = internet_available()

        if self.ai.engine == "Local":
            self.status.configure(
                text="● OFFLINE / LOCAL MODE",
                text_color=YELLOW
            )
        elif self.ai.engine == "Gemini":
            if self.ai.g and online:
                self.status.configure(
                    text="● GEMINI ONLINE",
                    text_color=CYAN
                )
            elif not online:
                self.status.configure(
                    text="● OFFLINE — LOCAL TOOLS",
                    text_color=YELLOW
                )
            else:
                self.status.configure(
                    text="● GEMINI KEY REQUIRED",
                    text_color=RED
                )
        else:
            if self.ai.o and online:
                self.status.configure(
                    text="● GPT ONLINE",
                    text_color=GREEN
                )
            elif not online:
                self.status.configure(
                    text="● OFFLINE — LOCAL TOOLS",
                    text_color=YELLOW
                )
            else:
                self.status.configure(
                    text="● GPT KEY REQUIRED",
                    text_color=RED
                )

    # ---------- HUD Dashboard / Chat ----------
    def _hud_card(self, parent, title, accent=CYAN, subtitle="", height=210):
        card = ctk.CTkFrame(
            parent, fg_color="#0C1824", corner_radius=14,
            border_width=1, border_color="#1D526B"
        )
        card.grid_propagate(False)
        card.configure(height=height)
        head = ctk.CTkFrame(card, fg_color="transparent", height=38)
        head.pack(fill="x", padx=12, pady=(8, 0))
        head.pack_propagate(False)
        ctk.CTkLabel(
            head, text=title.upper(), text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")
        ctk.CTkLabel(
            head, text="•••", text_color=accent,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="right")
        if subtitle:
            ctk.CTkLabel(
                card, text=subtitle, text_color=MUTED,
                font=ctk.CTkFont(size=10)
            ).pack(anchor="w", padx=13, pady=(0, 5))
        return card

    def _hud_button(self, parent, text, command, accent=CYAN, width=120):
        return ctk.CTkButton(
            parent, text=text, command=command, width=width, height=34,
            fg_color="#142636", hover_color="#1C4256",
            border_width=1, border_color="#24536A",
            text_color=TEXT
        )

    def _mini_metric(self, parent, label, value, progress=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row, text=label, text_color=MUTED).pack(side="left")
        ctk.CTkLabel(
            row, text=value, text_color=TEXT,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right")
        if progress is not None:
            bar = ctk.CTkProgressBar(row, height=7, progress_color=CYAN, fg_color="#172331")
            bar.pack(side="bottom", fill="x", pady=(3, 0))
            bar.set(max(0.0, min(1.0, progress)))

    def page_dashboard(self):
        # Visual reference: futuristic glass/HUD workspace with six functional zones.
        self.content.configure(fg_color="#071019")

        protocol = ctk.CTkFrame(
            self.content, fg_color="#0B1B28", height=42,
            corner_radius=10, border_width=1, border_color="#1B5168"
        )
        protocol.pack(fill="x", padx=18, pady=(12, 7))
        protocol.pack_propagate(False)
        ctk.CTkLabel(
            protocol, text="●  MARK 1 PROTOCOLS ACTIVE • SYSTEM READY", text_color=CYAN,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=15)
        ctk.CTkLabel(
            protocol, text="DAKSH BOSS KE LIYE ZETA AI HUB", text_color=MUTED,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=15)

        board = ctk.CTkFrame(self.content, fg_color="transparent")
        board.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        for col in range(3):
            board.grid_columnconfigure(col, weight=1, uniform="hudcol")
        for row in range(2):
            board.grid_rowconfigure(row, weight=1, uniform="hudrow")

        # Academics
        study = self._hud_card(
            board, "Academics & Study Mode", YELLOW,
            "JNV / Class 6–12 learning workspace"
        )
        study.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(
            study, text="JNV ZONE", text_color=YELLOW,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(fill="x", padx=12, pady=(4, 8))
        srow = ctk.CTkFrame(study, fg_color="transparent")
        srow.pack(fill="x", padx=10)
        self._hud_button(srow, "Study Materials", lambda: self.show_page("Study Mode"), YELLOW).pack(side="left", expand=True, fill="x", padx=2)
        self._hud_button(srow, "Quiz & Papers", lambda: self.show_page("Smart Tools"), YELLOW).pack(side="left", expand=True, fill="x", padx=2)
        srow2 = ctk.CTkFrame(study, fg_color="transparent")
        srow2.pack(fill="x", padx=10, pady=5)
        self._hud_button(srow2, "Syllabus", lambda: self.show_page("Study Mode"), YELLOW).pack(side="left", expand=True, fill="x", padx=2)
        self._hud_button(srow2, "Progress", lambda: self.show_page("Routine Center"), YELLOW).pack(side="left", expand=True, fill="x", padx=2)
        self._mini_metric(study, "Study progress", "60%", 0.60)

        # Core
        core = self._hud_card(board, "ZETA AI Core", CYAN, "Gemini + OpenAI + Local Core")
        core.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        eng = ctk.CTkFrame(core, fg_color="#07131D", corner_radius=10, border_width=1, border_color="#1B526B")
        eng.pack(fill="x", padx=12, pady=(2, 8))
        ctk.CTkLabel(eng, text=f"◈  {self.ai.engine} + Local", text_color=CYAN,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=7)
        ctk.CTkLabel(eng, text="●  ●  ●", text_color=GREEN).pack(side="right", padx=10)
        logo = ctk.CTkLabel(core, text="Z  ZETA AI", text_color=CYAN,
                            font=ctk.CTkFont(size=30, weight="bold"))
        logo.pack(pady=(8, 2))
        ctk.CTkLabel(core, text="AI WORKSPACE KA CORE", text_color=MUTED,
                     font=ctk.CTkFont(size=10, weight="bold")).pack()
        wave = ctk.CTkLabel(core, text="▁▃▆▃▇▅▂▆▃▇▂▅▃▆▁", text_color=PURPLE,
                            font=ctk.CTkFont(size=18))
        wave.pack(pady=8)
        self._hud_button(core, "Open Chat Core", self.open_chat_core, CYAN, 150).pack(pady=(0, 7))

        # R&D
        rnd = self._hud_card(board, "R&D & Science Lab", CYAN, "Projects • experiments • research")
        rnd.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        rrow = ctk.CTkFrame(rnd, fg_color="transparent")
        rrow.pack(fill="x", padx=10, pady=2)
        self._hud_button(rrow, "Project Advisor", lambda: self.show_page("Project Advisor"), CYAN).pack(side="left", expand=True, fill="x", padx=2)
        self._hud_button(rrow, "Research", lambda: self.show_page("Research"), CYAN).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkLabel(rnd, text="⚗   △   ⌬   ∿", text_color=CYAN,
                     font=ctk.CTkFont(size=25)).pack(pady=(16, 7))
        ctk.CTkLabel(
            rnd, text="Project plans • analysis • technical notes",
            text_color=MUTED, wraplength=320
        ).pack(pady=4)
        self._hud_button(rnd, "Open R&D Hub", lambda: self.show_page("Project Advisor"), CYAN, 145).pack(pady=8)

        # Design
        design = self._hud_card(board, "Design & Create", YELLOW, "Creator tools and image generation")
        design.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        drow = ctk.CTkFrame(design, fg_color="transparent")
        drow.pack(fill="x", padx=10, pady=2)
        self._hud_button(drow, "Creator Studio", lambda: self.show_page("Creator Studio"), YELLOW).pack(side="left", expand=True, fill="x", padx=2)
        self._hud_button(drow, "Image Lab", lambda: self.show_page("Image Lab"), YELLOW).pack(side="left", expand=True, fill="x", padx=2)
        tools = ctk.CTkFrame(design, fg_color="#09141F", corner_radius=8)
        tools.pack(fill="both", expand=True, padx=10, pady=8)
        for i, icon in enumerate(["✎", "T", "□", "↶", "↷", "⌁", "◈", "⌕"]):
            tools.grid_columnconfigure(i % 4, weight=1)
            ctk.CTkButton(tools, text=icon, width=40, height=35, fg_color="transparent",
                          hover_color="#173247").grid(row=i//4, column=i%4, padx=2, pady=3)

        # System / Dev
        sys = self._hud_card(board, "System & Dev Hub", GREEN, "Development and device status")
        sys.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        metrics = ctk.CTkFrame(sys, fg_color="transparent")
        metrics.pack(fill="x", padx=10, pady=3)
        cpu = mem = 0
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
            except Exception:
                pass
        self._mini_metric(metrics, "CPU Load", f"{cpu:.0f}%", cpu/100 if cpu else 0.03)
        self._mini_metric(metrics, "Memory", f"{mem:.0f}%", mem/100 if mem else 0.18)
        drow = ctk.CTkFrame(sys, fg_color="transparent")
        drow.pack(fill="x", padx=10, pady=4)
        self._hud_button(drow, "System Control", lambda: self.show_page("System Control"), GREEN).pack(side="left", expand=True, fill="x", padx=2)
        self._hud_button(drow, "Device Hub", lambda: self.show_page("Device Hub"), GREEN).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkLabel(sys, text="CONNECTED DEVICES • LOCAL AGENT READY", text_color=MUTED,
                     font=ctk.CTkFont(size=9, weight="bold")).pack(pady=6)

        # Organizer / Business
        org = self._hud_card(board, "Organizer & Business", BLUE, "Business • routines • exports")
        org.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        orow = ctk.CTkFrame(org, fg_color="transparent")
        orow.pack(fill="x", padx=10, pady=2)
        self._hud_button(orow, "Business", lambda: self.show_page("Business Workspace"), BLUE).pack(side="left", expand=True, fill="x", padx=2)
        self._hud_button(orow, "Routine", lambda: self.show_page("Routine Center"), BLUE).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkLabel(org, text="PROJECT TIMELINE", text_color=MUTED,
                     font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=13, pady=(10, 2))
        for label, pct in [("JNV Revision", 0.72), ("ZETA Build", 0.55), ("X INDOVATION", 0.28)]:
            self._mini_metric(org, label, f"{int(pct*100)}%", pct)
        self._hud_button(org, "Export Center", lambda: self.show_page("Export Center"), BLUE, 145).pack(pady=5)

        # GPT-style large composer on the main dashboard.
        self.build_gpt_composer(self.content, dashboard=True)

    def build_gpt_composer(self, parent, dashboard=False):
        """Large ChatGPT-style multiline composer with tools and Send button."""
        wrap = ctk.CTkFrame(
            parent, fg_color="#08131D", corner_radius=16,
            border_width=1, border_color="#24566E"
        )
        wrap.pack(fill="x", padx=18 if dashboard else 30, pady=(2, 10 if dashboard else 14))

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(
            top, text="✦ ZETA SE PUCHHIYE", text_color=CYAN,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        ctk.CTkLabel(
            top, text="Enter = Send  •  Shift+Enter = New Line",
            text_color=MUTED, font=ctk.CTkFont(size=10)
        ).pack(side="right")

        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(6, 10))
        row.grid_columnconfigure(0, weight=1)

        box = ctk.CTkTextbox(
            row, height=120 if dashboard else 150,
            fg_color="#050C13", border_width=1, border_color="#183E53",
            corner_radius=12, font=ctk.CTkFont(size=15),
            wrap="word"
        )
        box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        box.insert("1.0", "ZETA AI ko kya karna hai?  Type your message...")
        box.configure(text_color=MUTED)

        def focus_box(event=None):
            try:
                box.focus_set()
                current = box.get("1.0", "end-1c")
                if current == "ZETA AI ko kya karna hai?  Type your message...":
                    box.delete("1.0", "end")
                    box.configure(text_color=TEXT)
            except Exception:
                pass
            return "break" if event else None

        def submit(event=None):
            # Shift+Enter keeps newline; plain Enter sends.
            if event is not None and (event.state & 1):
                if box.cget("text_color") == str(MUTED):
                    focus_box()
                return
            text = box.get("1.0", "end").strip()
            if not text or text == "ZETA AI ko kya karna hai?  Type your message...":
                return "break"
            if dashboard:
                self.open_chat_core()
                self.chat_input.delete("1.0", "end")
                self.chat_input.insert("1.0", text)
                self.send_chat()
            else:
                self.chat_input.delete("1.0", "end")
                self.chat_input.insert("1.0", text)
                self.send_chat()
            return "break"

        box.bind("<FocusIn>", focus_box)
        box.bind("<Return>", submit)
        self.gpt_composer = box

        actions = ctk.CTkFrame(row, fg_color="transparent", width=150)
        actions.grid(row=0, column=1, sticky="ns")
        actions.grid_propagate(False)
        ctk.CTkButton(
            actions, text="➤  SEND", height=54,
            fg_color=CYAN, hover_color="#32CFE5", text_color="#001018",
            font=ctk.CTkFont(size=13, weight="bold"), command=submit
        ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            actions, text="📎  ATTACH", height=38,
            fg_color="#102536", hover_color="#173D55",
            command=self.attach_file
        ).pack(fill="x", pady=3)
        ctk.CTkButton(
            actions, text="🎙  VOICE", height=38,
            fg_color="#102536", hover_color="#173D55",
            command=self.voice_input
        ).pack(fill="x", pady=3)

        footer = ctk.CTkFrame(wrap, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(0, 9))
        ctk.CTkLabel(
            footer, text="Gemini / OpenAI / Local  •  File analysis  •  Memory  •  Voice",
            text_color=MUTED, font=ctk.CTkFont(size=10)
        ).pack(side="left")
        ctk.CTkLabel(
            footer, text="● READY", text_color=GREEN,
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(side="right")

    def open_chat_core(self):
        self.clear_content()
        self.header("ZETA AI Core", "Full Chat Core — Gemini + OpenAI + Local Core")
        self.chat = ctk.CTkTextbox(
            self.content, fg_color="#080F18", border_width=1, border_color=BORDER
        )
        self.chat.pack(fill="both", expand=True, padx=30, pady=8)
        self.chat.insert(
            "end", "ZETA: Ready, Daksh Boss. 🚀\n"
                    "ZETA: Type a question, attach a file, or choose a workspace.\n\n"
        )
        bottom = ctk.CTkFrame(self.content, fg_color="#08131D", corner_radius=16,
                              border_width=1, border_color="#24566E")
        bottom.pack(fill="x", padx=30, pady=(0, 10))
        top = ctk.CTkFrame(bottom, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(8, 0))
        ctk.CTkLabel(top, text="✦ MESSAGE ZETA AI", text_color=CYAN,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkLabel(top, text="Enter = Send • Shift+Enter = New Line", text_color=MUTED,
                     font=ctk.CTkFont(size=10)).pack(side="right")
        input_row = ctk.CTkFrame(bottom, fg_color="transparent")
        input_row.pack(fill="x", padx=12, pady=(5, 8))
        input_row.grid_columnconfigure(0, weight=1)
        self.chat_input = ctk.CTkTextbox(
            input_row, height=150, fg_color="#050C13",
            border_width=1, border_color="#183E53", corner_radius=12,
            font=ctk.CTkFont(size=15), wrap="word"
        )
        self.chat_input.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chat_input.bind("<Return>", self.chat_enter)
        ctk.CTkButton(input_row, text="➤\nSEND", width=125, height=150,
                      fg_color=CYAN, hover_color="#32CFE5", text_color="#001018",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.send_chat).grid(row=0, column=1)
        tools = ctk.CTkFrame(self.content, fg_color="transparent")
        tools.pack(fill="x", padx=30, pady=(0, 16))
        for label, cmd in [
            ("📎 Attach", self.attach_file), ("🎤 Voice", self.voice_input),
            ("🔊 Speak", self.speak_last), ("🧠 Remember", self.quick_remember),
            ("💡 Motivate", self.motivate), ("🗑 Clear", self.clear_chat)
        ]:
            ctk.CTkButton(tools, text=label, command=cmd, fg_color=PANEL).pack(side="left", padx=(0, 7))

    def chat_enter(self, event):
        # Shift+Enter = newline
        if event.state & 1:
            return
        self.send_chat()
        return "break"

    def send_chat(self):
        prompt = self.chat_input.get("1.0", "end").strip()
        if not prompt:
            return
        if self.busy:
            self.chat.insert("end", "\nZETA: पिछला response अभी चल रहा है. एक moment wait करें.\n")
            return

        self.chat_input.delete("1.0", "end")
        self.chat.insert("end", f"\nYOU: {prompt}\nZETA: ")
        self.chat.see("end")
        attached = self.current_file
        self.current_file = None
        self.busy = True
        self.status.configure(text="● RESPONSE AA RAHA HAI...", text_color=CYAN)
        streamed = {"started": False, "text": ""}

        def chunk(text):
            if not text:
                return
            streamed["started"] = True
            streamed["text"] += text
            self.chat.insert("end", text)
            self.chat.see("end")

        def done(answer):
            # Avoid duplicating a streamed response if the final callback contains it.
            if not streamed["started"]:
                self.chat.insert("end", answer)
            self.chat.insert("end", "\n")
            self.chat.see("end")
            self.busy = False
            self.refresh_status()

        self.run_streaming(
            lambda emit: self.ai.ask_stream(
                prompt,
                "You are operating in ZETA Chat Core. Answer naturally like a helpful friend.",
                file_path=attached,
                on_chunk=emit
            ),
            chunk,
            done
        )

    def clear_chat(self):
        if hasattr(self, "chat"):
            self.chat.delete("1.0", "end")
            self.chat.insert("end", "ZETA: Chat cleared. Ready.\n\n")

    def quick_remember(self):
        dialog = ctk.CTkInputDialog(
            text="ZETA ko kya yaad rakhna hai?",
            title="ZETA Memory"
        )
        value = dialog.get_input()
        if value:
            self.ai.remember(value)
            messagebox.showinfo("Memory", "Saved to local ZETA memory.")

    def motivate(self):
        self.chat.insert(
            "end",
            "\nZETA: Mission mode activated. "
            "एक छोटा task चुनो और उसे complete करो. 🚀\n"
        )

    # ---------- Study ----------
    def page_study_mode(self):
        self.header(
            "Study Mode",
            "JNV Focus • Explain • Notes • Quiz • Revision • Super Explainer"
        )

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=30, pady=10)

        self.study_topic = ctk.CTkEntry(
            row, placeholder_text="Chapter / topic / question", height=42
        )
        self.study_topic.pack(fill="x", expand=True, side="left", padx=(0, 7))

        for label, action in [
            ("Explain", "explain"),
            ("Notes", "notes"),
            ("Quiz", "quiz"),
            ("Revision", "revision"),
            ("Model Paper", "paper"),
            ("Lecture", "lecture")
        ]:
            ctk.CTkButton(
                row, text=label, width=90,
                command=lambda x=action: self.study_action(x),
                fg_color=CYAN if action == "explain" else PANEL,
                text_color="#001018" if action == "explain" else TEXT
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            self.content,
            text="📎 Study PDF/Image Analyze Karein",
            command=self.study_file,
            fg_color=PANEL
        ).pack(anchor="w", padx=30)

        self.study_out = self.output_box(430)

    def study_action(self, mode):
        topic = self.study_topic.get().strip()
        if not topic:
            return

        prompts = {
            "explain": (
                f"Explain '{topic}' for Class 9/JNV in simple Hindi + English "
                "technical terms. Use a friend-like tone, examples, common mistakes "
                "and 5 quick check questions."
            ),
            "notes": (
                f"Make concise JNV revision notes for '{topic}'. Include definitions, "
                "formulas, examples, key points and common mistakes."
            ),
            "quiz": (
                f"Create a JNV/Class 9 practice quiz for '{topic}'. Give 10 questions "
                "first and then a separate answer key with explanations."
            ),
            "revision": (
                f"Create a practical revision plan for '{topic}' using active recall, "
                "spaced repetition and practice questions."
            ),
            "paper": (
                f"Create a Class 9/JNV-style model paper on '{topic}'. Include sections, "
                "marks, time suggestion and answer key."
            ),
            "lecture": (
                f"Teach '{topic}' as a mini lecture. Structure it as: hook, concept, "
                "example, visual imagination, common mistake, recap and homework."
            )
        }

        self.write_output(self.study_out, "ZETA Study Engine: THINKING...")
        self.run_async(
            lambda: self.ai.ask(
                prompts[mode],
                "You are ZETA Study Engine. Teach clearly and encourage independent solving."
            ),
            lambda r: self.write_output(self.study_out, r)
        )

    def study_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("PDF", "*.pdf"),
                ("Images", "*.png *.jpg *.jpeg *.webp"),
                ("All", "*.*")
            ]
        )
        if not path:
            return

        self.write_output(self.study_out, "Analyzing study material...")
        self.run_async(
            lambda: self.ai.ask(
                "Analyze this study material. Explain difficult concepts, make revision notes, "
                "then create 5 practice questions.",
                "You are ZETA Super Explainer and Study Vision.",
                file_path=path
            ),
            lambda r: self.write_output(self.study_out, r)
        )

    # ---------- Project Advisor ----------
    def page_project_advisor(self):
        self.header(
            "Project Advisor",
            "Idea → Problem → Components → Budget → Build → Test → Presentation"
        )

        self.project_box = ctk.CTkTextbox(
            self.content, height=115, fg_color=PANEL,
            border_width=1, border_color=BORDER
        )
        self.project_box.pack(fill="x", padx=30, pady=10)
        self.project_box.insert(
            "1.0",
            "Example: Low-cost agriculture soil moisture monitoring project"
        )

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=30)

        self.project_budget = ctk.CTkEntry(
            row, placeholder_text="Budget ₹ (optional)"
        )
        self.project_budget.pack(fill="x", expand=True, side="left", padx=(0, 7))

        self.project_level = ctk.CTkOptionMenu(
            row, values=["School", "Beginner", "Advanced"]
        )
        self.project_level.pack(side="left", padx=5)

        ctk.CTkButton(
            row, text="BLUEPRINT BANAYEIN ◆",
            fg_color=PURPLE, command=self.build_project
        ).pack(side="left", padx=5)

        self.project_out = self.output_box(430)

    def build_project(self):
        idea = self.project_box.get("1.0", "end").strip()
        budget = self.project_budget.get().strip() or "not specified"

        prompt = f"""
Create a complete safe educational project blueprint.

Idea: {idea}
Budget: ₹{budget}
Level: {self.project_level.get()}

Return:
1. Project name
2. Problem
3. Working principle
4. Components
5. Approximate budget
6. Safe low-voltage architecture if electronics are involved
7. Software/code architecture
8. Step-by-step build plan
9. Testing checklist
10. Common failure points
11. Documentation
12. Presentation outline
13. Future upgrades

Never recommend dangerous, explosive, high-voltage, or unsafe experiments.
"""

        self.write_output(self.project_out, "ZETA Project Advisor: BUILD KAREINING...")
        self.run_async(
            lambda: self.ai.ask(
                prompt,
                "You are ZETA Project Advisor. Be practical, safe and educational."
            ),
            lambda r: self.write_output(self.project_out, r)
        )

    # ---------- Developer ----------
    def page_developer_mode(self):
        self.header(
            "Developer Mode",
            "Debug • Explain • Improve • Tests • Architecture • Ultimate Developer"
        )

        self.code_box = ctk.CTkTextbox(
            self.content, height=245,
            fg_color="#070C12", border_width=1, border_color=BORDER,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.code_box.pack(fill="x", padx=30, pady=8)

        self.error_box = ctk.CTkEntry(
            self.content, placeholder_text="Error message (optional)"
        )
        self.error_box.pack(fill="x", padx=30, pady=6)

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=30)

        actions = [
            ("Debug", "debug", RED),
            ("Explain", "explain", CYAN),
            ("Improve", "improve", GREEN),
            ("Tests", "tests", BLUE),
            ("Architecture", "architecture", PURPLE)
        ]

        for label, action, color in actions:
            ctk.CTkButton(
                row, text=label,
                command=lambda x=action: self.code_action(x),
                fg_color=color if action == "debug" else PANEL,
                text_color="#FFFFFF"
            ).pack(side="left", padx=3)

        ctk.CTkLabel(
            self.content,
            text="Ultimate Developer Mode = deeper architecture, security, testing aur refactoring guidance.",
            text_color=MUTED
        ).pack(anchor="w", padx=30, pady=7)

        self.code_out = self.output_box(280)

    def code_action(self, mode):
        code = self.code_box.get("1.0", "end").strip()
        error = self.error_box.get().strip()

        if not code:
            return

        prompts = {
            "debug": (
                f"Debug this code. Error: {error or 'not provided'}. "
                "Find root cause, provide corrected code and explain the fix."
            ),
            "explain": "Explain this code clearly, section by section, then summarize architecture.",
            "improve": "Improve readability, reliability, maintainability and error handling. Return revised code.",
            "tests": "Create useful unit tests and integration tests with expected behavior.",
            "architecture": (
                "Design a production-oriented architecture for this project. "
                "Discuss modules, security, testing, logging, configuration and deployment."
            )
        }

        prompt = prompts[mode] + f"\n\n```python\n{code}\n```"

        self.write_output(self.code_out, "Developer Engine: THINKING...")
        self.run_async(
            lambda: self.ai.ask(
                prompt,
                "You are ZETA Ultimate Developer Mode. Be precise and do not invent APIs."
            ),
            lambda r: self.write_output(self.code_out, r)
        )

    # ---------- Research ----------
    def page_research(self):
        self.header(
            "Research Workspace",
            "Live research is provider-dependent. OpenAI can use web_search when available."
        )

        self.research_box = ctk.CTkTextbox(
            self.content, height=105, fg_color=PANEL,
            border_width=1, border_color=BORDER
        )
        self.research_box.pack(fill="x", padx=30, pady=10)

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=30)

        ctk.CTkButton(
            row, text="RESEARCH KAREIN START KAREIN ◎",
            fg_color=BLUE, command=self.start_research
        ).pack(side="left")

        ctk.CTkButton(
            row, text="Google",
            fg_color=PANEL,
            command=lambda: webbrowser.open("https://www.google.com")
        ).pack(side="left", padx=7)

        self.research_out = self.output_box(430)

    def start_research(self):
        question = self.research_box.get("1.0", "end").strip()
        if not question:
            return

        prompt = (
            f"Research this question carefully:\n{question}\n\n"
            "Return: concise answer, key findings, uncertainty/caveats, "
            "and sources when available. Never invent sources."
        )

        self.write_output(self.research_out, "Researching...")
        self.run_async(
            lambda: self.ai.ask(
                prompt,
                "You are ZETA Research Engine. Clearly distinguish verified facts from uncertainty.",
                research=(self.ai.engine == "OpenAI")
            ),
            lambda r: self.write_output(self.research_out, r)
        )

    # ---------- Creator ----------
    def page_creator_studio(self):
        self.header(
            "Creator Studio",
            "Presentation • Promo • Startup Pitch • Poster • Lecture"
        )

        self.creator_prompt = ctk.CTkTextbox(
            self.content, height=120, fg_color=PANEL,
            border_width=1, border_color=BORDER
        )
        self.creator_prompt.pack(fill="x", padx=30, pady=10)
        self.creator_prompt.insert(
            "1.0", "Create a presentation for ZETA AI Study Mode"
        )

        self.creator_mode = ctk.CTkOptionMenu(
            self.content,
            values=[
                "Presentation",
                "Promo Video Script",
                "Startup Pitch",
                "Poster Copy",
                "Social Post",
                "Lecture"
            ]
        )
        self.creator_mode.pack(anchor="w", padx=30, pady=5)

        ctk.CTkButton(
            self.content, text="BANAYEIN ✦",
            fg_color=PURPLE, command=self.create_content
        ).pack(anchor="w", padx=30, pady=8)

        self.creator_out = self.output_box(420)

    def create_content(self):
        idea = self.creator_prompt.get("1.0", "end").strip()
        mode = self.creator_mode.get()

        prompt = (
            f"Create a polished {mode} for:\n{idea}\n\n"
            "Make it practical and ready to edit. Do not invent statistics, testimonials or claims."
        )

        self.run_async(
            lambda: self.ai.ask(prompt, "You are ZETA Creator Studio."),
            lambda r: self.write_output(self.creator_out, r)
        )

    # ---------- Memory ----------
    def page_memory(self):
        self.header(
            "Personal + Chat Memory",
            "Local memory is stored on this computer in .zeta_ai."
        )

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=30, pady=10)

        entry = ctk.CTkEntry(
            row, placeholder_text="Jo baat ZETA ko yaad rakhni chahiye"
        )
        entry.pack(fill="x", expand=True, side="left", padx=(0, 7))

        box = self.output_box(460)

        def refresh():
            box.delete("1.0", "end")
            if self.ai.memory:
                box.insert(
                    "end",
                    "\n".join(
                        f"{i}. {item}" for i, item in enumerate(self.ai.memory, 1)
                    )
                )
            else:
                box.insert("end", "Memory is empty.")

        def add():
            self.ai.remember(entry.get())
            entry.delete(0, "end")
            refresh()

        def remove():
            deleted = self.ai.forget_last()
            self.ai.save_state()
            refresh()
            if deleted:
                messagebox.showinfo("Memory", f"Removed:\n{deleted}")

        ctk.CTkButton(
            row, text="SAVE KAREIN", fg_color=CYAN,
            text_color="#001018", command=add
        ).pack(side="left")

        ctk.CTkButton(
            row, text="LAST REMOVE KAREIN",
            fg_color="#3A2030", command=remove
        ).pack(side="left", padx=7)

        ctk.CTkButton(
            row, text="SAB CLEAR KAREIN",
            fg_color="#35121C",
            command=lambda: self.clear_memory(refresh)
        ).pack(side="left")

        refresh()

    def clear_memory(self, refresh):
        if messagebox.askyesno(
            "Clear memory",
            "Clear local ZETA memory?"
        ):
            self.ai.memory = []
            self.ai.save_state()
            refresh()

    # ---------- Device Hub ----------
    def page_device_hub(self):
        self.header(
            "Device Hub",
            "Safe desktop actions. ZETA does not get unrestricted system control."
        )

        grid = ctk.CTkFrame(self.content, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=20)

        actions = [
            ("🌐 Open Google", lambda: webbrowser.open("https://www.google.com")),
            ("▶ Open YouTube", lambda: webbrowser.open("https://www.youtube.com")),
            ("💻 Open VS Code", self.open_vscode),
            ("📂 Open ZETA Folder", lambda: self.open_path(DATA)),
            ("📝 Create Note", self.create_note),
            ("🔁 Create Startup Shortcut", self.create_startup_helper)
        ]

        for i, (label, command) in enumerate(actions):
            grid.grid_columnconfigure(i % 2, weight=1)
            ctk.CTkButton(
                grid,
                text=label,
                height=55,
                fg_color=PANEL,
                command=command
            ).grid(
                row=i // 2,
                column=i % 2,
                sticky="ew",
                padx=5,
                pady=5
            )

        info = ctk.CTkFrame(
            self.content, fg_color=PANEL,
            border_width=1, border_color=BORDER
        )
        info.pack(fill="x", padx=30, pady=15)

        ctk.CTkLabel(
            info,
            text="Device Control Architecture",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=18, pady=(15, 5))

        ctk.CTkLabel(
            info,
            text=(
                "Current prototype: controlled, explicit actions only.\n"
                "Future web version: permission-based device bridge + signed local agent.\n"
                "No hidden background control."
            ),
            text_color=MUTED,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 15))

    def open_vscode(self):
        candidates = [
            "code",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe")
        ]

        for candidate in candidates:
            try:
                subprocess.Popen([candidate])
                return
            except Exception:
                continue

        messagebox.showinfo(
            "VS Code",
            "VS Code command नहीं मिला. इसे manually open करें."
        )

    def open_path(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(str(path))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Open", str(exc))

    def create_note(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")]
        )
        if not path:
            return

        Path(path).write_text(
            f"ZETA AI NOTE\nCreated: {datetime.now():%Y-%m-%d %H:%M}\n\n",
            encoding="utf-8"
        )
        messagebox.showinfo("File Maker", "Note created.")

    def create_startup_helper(self):
        if platform.system() != "Windows":
            messagebox.showinfo(
                "Startup",
                "This helper currently targets Windows."
            )
            return

        startup = Path(os.getenv("APPDATA", "")) / (
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )

        bat = startup / "ZETA_AI_STARTUP.bat"
        script = Path(__file__).resolve()

        content = (
            "@echo off\n"
            f'start "" "{os.sys.executable}" "{script}"\n'
        )

        try:
            bat.write_text(content, encoding="utf-8")
            messagebox.showinfo(
                "Startup",
                "ZETA startup helper created.\n"
                "Remove it from the same Startup folder whenever you want."
            )
        except Exception as exc:
            messagebox.showerror("Startup", str(exc))

    # ---------- Feature Center ----------
    def page_feature_center(self):
        self.header(
            "ZETA Feature Center",
            "Free/Core + Pro + Pro+ architecture from user feedback."
        )

        tabs = ctk.CTkTabview(self.content)
        tabs.pack(fill="both", expand=True, padx=30, pady=15)

        tabs.add("FREE / CORE")
        tabs.add("PRO")
        tabs.add("PRO+")
        tabs.add("ROADMAP")

        free = [
            "✓ Image generation integration point",
            "✓ Detail analysis / Super Explainer",
            "✓ Concept clearing",
            "✓ Friend-like natural tone",
            "✓ File maker / workspace export",
            "✓ Practice Quiz",
            "✓ Personal + Chat Memory",
            "✓ Tone adaptation",
            "✓ Permission-based Device Hub",
            "✓ Voice command",
            "✓ Project Advisor",
            "✓ Study Mode + building guides",
            "✓ Custom theme architecture",
            "✓ Developer Mode",
            "✓ Startup/self-open helper",
            "◐ Google ID sync — backend integration required",
            "✓ Motivational Mode",
            "◐ Notebook-style integrations — provider/API dependent"
        ]

        pro = [
            "PRO",
            "• Ultimate Developer Mode",
            "• Advanced Image Generation",
            "• Ultimate Guidance",
            "• Cloud Storage",
            "• Special Study Mode + Guidance",
            "• Live Research / News integration",
            "• Presentation + Lecture workflows",
            "• Location-aware features with permission",
            "• Business Workspace",
            "• Super Explainer + Analyzer",
            "• Model Paper Maker + PDF export",
            "• Higher limits / larger workspaces"
        ]

        pro_plus = [
            "PRO+",
            "• Advanced multi-step workflows",
            "• Team / shared workspaces",
            "• Multi-device sync",
            "• Advanced developer workflows",
            "• Priority model routing",
            "• Larger cloud storage",
            "• Advanced Business Workspace",
            "• Future agent/device bridge",
            "• Secure enterprise-style controls"
        ]

        roadmap = [
            "PUBLIC WEB ARCHITECTURE",
            "",
            "Browser",
            "   ↓",
            "ZETA Secure Backend",
            "   ├── Gemini",
            "   ├── OpenAI",
            "   ├── Authentication",
            "   ├── Cloud Storage",
            "   ├── Subscription / Billing",
            "   └── Usage limits",
            "",
            "Desktop prototype ≠ production backend.",
            "Never expose provider API keys in the browser."
        ]

        self._feature_text(tabs.tab("FREE / CORE"), free, CYAN)
        self._feature_text(tabs.tab("PRO"), pro, PURPLE)
        self._feature_text(tabs.tab("PRO+"), pro_plus, GREEN)
        self._feature_text(tabs.tab("ROADMAP"), roadmap, BLUE)

    def _feature_text(self, parent, lines, color):
        box = ctk.CTkTextbox(parent, fg_color="#080F18")
        box.pack(fill="both", expand=True, padx=15, pady=15)
        box.insert("end", "\n".join(lines))
        box.tag_config("title", foreground=color)

    # ---------- Smart Tools from classmate feedback ----------
    def page_smart_tools(self):
        self.header(
            "Smart Tools",
            "Concepts • Quiz • Model Paper • Lecture • Analyzer • File Maker"
        )
        grid = ctk.CTkFrame(self.content, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=15)
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

        tools = [
            ("💡 Concept Clearer", "Explain a concept like a friend, then give a tiny example.", "concept"),
            ("🧠 Practice Quiz", "Create 10 JNV-style questions with answers and short explanations.", "quiz"),
            ("📝 Model Paper", "Create a chapter-wise practice paper with answer key.", "paper"),
            ("🎓 Lecture Mode", "Turn a topic into a short teacher-style lesson with checkpoints.", "lecture"),
            ("🔎 Super Analyzer", "Analyze pasted text and return key points, gaps and next steps.", "analyze"),
            ("📄 File Maker", "Turn the generated result into a TXT/MD file you can save.", "file")
        ]
        self.smart_topic = ctk.CTkTextbox(self.content, height=90, fg_color=PANEL, border_width=1, border_color=BORDER)
        self.smart_topic.pack(fill="x", padx=30, pady=(0, 12))
        self.smart_topic.insert("1.0", "Example: Algebraic Expressions & Identities — Class 9 JNV")
        self.smart_out = self.output_box(390)
        self.smart_last = ""

        def run_tool(mode):
            topic = self.smart_topic.get("1.0", "end").strip()
            if not topic:
                return
            prompts = {
                "concept": f"Explain this concept like a friendly teacher: {topic}. Use simple Hindi/Hinglish, examples, common mistakes and a 3-question check.",
                "quiz": f"Create a 10-question JNV Class 9 practice quiz on: {topic}. Include answer key and one-line explanations. Do not treat it as a live test.",
                "paper": f"Create a printable JNV Class 9 practice model paper on: {topic}. Include sections, marks, answer key and concise solutions.",
                "lecture": f"Teach this topic as a 10-minute mini lecture: {topic}. Use sections, examples, checkpoints and a recap.",
                "analyze": f"Analyze the following topic/text: {topic}. Return key ideas, unclear points, likely misconceptions and practical next steps.",
                "file": f"Create polished study notes for: {topic}. Use headings, formulas where relevant, examples and a quick revision box."
            }
            self.write_output(self.smart_out, "ZETA: Streaming...")
            def done(r):
                self.smart_last = r
                self.write_output(self.smart_out, r)
            self.run_async(lambda: self.ai.ask(prompts[mode], "You are ZETA Smart Tools. Be accurate, age-appropriate and practical."), done)

        for i, (label, desc, mode) in enumerate(tools):
            card = ctk.CTkFrame(grid, fg_color=PANEL, border_width=1, border_color=BORDER)
            card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=16, weight="bold"), text_color=CYAN).pack(anchor="w", padx=12, pady=(10, 3))
            ctk.CTkLabel(card, text=desc, text_color=MUTED, wraplength=280, justify="left").pack(anchor="w", padx=12, pady=3)
            ctk.CTkButton(card, text="RUN KAREIN", command=lambda m=mode: run_tool(m), fg_color=BLUE).pack(anchor="w", padx=12, pady=(6, 12))

    # ---------- Agent Center ----------
    def page_agent_center(self):
        self.header("Agent Center", "Plan → review → safe actions execute → report")
        ctk.CTkLabel(self.content, text="ZETA ko multi-step goal dein. Execution sirf explicit safe local actions tak limited hai.", text_color=MUTED).pack(anchor="w", padx=30, pady=(8, 5))
        self.agent_goal = ctk.CTkTextbox(self.content, height=110, fg_color=PANEL, border_width=1, border_color=BORDER)
        self.agent_goal.pack(fill="x", padx=30, pady=8)
        self.agent_goal.insert("1.0", "Plan a study session for Algebraic Expressions & Identities and create a note with the plan")
        row=ctk.CTkFrame(self.content, fg_color="transparent"); row.pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(row,text="PLAN BANAYEIN",fg_color=BLUE,command=self.agent_plan).pack(side="left",padx=(0,6))
        ctk.CTkButton(row,text="SAFE PLAN EXECUTE KAREIN BANAYEIN",fg_color=GREEN,text_color="#001018",command=self.agent_execute).pack(side="left",padx=6)
        ctk.CTkButton(row,text="STOP",fg_color=RED,command=lambda:self.write_output(self.agent_out,"Agent stopped. No background task is running.")).pack(side="left",padx=6)
        self.agent_out=self.output_box(430)
        self.agent_plan_text=""

    def agent_plan(self):
        goal=self.agent_goal.get("1.0","end").strip()
        if not goal:return
        prompt=(f"Create a safe executable plan for this desktop task: {goal}.\n"
                "Return numbered steps. Only use these action types if needed: OPEN_URL, OPEN_PATH, OPEN_VSCODE, CREATE_NOTE, EXPORT_TEXT. "
                "Never include shell commands, credential actions, deletion, registry changes, downloads, or unrestricted computer control. "
                "Mark any step requiring user confirmation as CONFIRM.")
        self.write_output(self.agent_out,"ZETA Agent: planning...")
        self.run_async(lambda:self.ai.ask(prompt,"You are ZETA Safe Agent Planner. Produce only safe, explicit, reversible desktop actions."),self._save_agent_plan)

    def _save_agent_plan(self,r):
        self.agent_plan_text=r
        self.write_output(self.agent_out,r)

    def agent_execute(self):
        plan=getattr(self,"agent_plan_text","").strip()
        if not plan:
            self.write_output(self.agent_out,"Create a plan first."); return
        low=plan.lower()
        forbidden=["delete","format","registry","password","api key","credential","powershell","cmd.exe","shutdown","restart","install"]
        if any(x in low for x in forbidden):
            self.write_output(self.agent_out,"Execution blocked: plan contains a restricted system action. Review the plan and keep actions safe.")
            return
        results=["Agent execution started."]
        if "open_vscode" in low or "open vscode" in low:
            self.open_vscode(); results.append("✓ VS Code opened")
        if "open_url" in low or "open google" in low or "open youtube" in low:
            webbrowser.open("https://www.google.com"); results.append("✓ Browser opened")
        if "create_note" in low or "create note" in low:
            path=DATA/"agent_note.txt"; path.write_text("ZETA Agent Note\nCreated: "+datetime.now().isoformat()+"\n\n"+self.agent_goal.get("1.0","end").strip(),encoding="utf-8"); results.append(f"✓ Note created: {path}")
        results.append("Agent finished. Actions were limited to safe local operations.")
        self.write_output(self.agent_out,"\n".join(results))

    # ---------- Knowledge Base ----------
    def page_knowledge_base(self):
        self.header("Knowledge Base", "Local project library • search • document Q&A • project context")
        row=ctk.CTkFrame(self.content,fg_color="transparent"); row.pack(fill="x",padx=30,pady=8)
        ctk.CTkButton(row,text="FILES ADD KAREIN",fg_color=BLUE,command=self.kb_add_files).pack(side="left")
        ctk.CTkButton(row,text="LIBRARY KHOLEN",fg_color=PANEL,command=lambda:self.open_path(DATA/"knowledge")).pack(side="left",padx=6)
        self.kb_query=ctk.CTkEntry(row,placeholder_text="Apni local knowledge base mein search/ask karein...")
        self.kb_query.pack(side="left",fill="x",expand=True,padx=6)
        ctk.CTkButton(row,text="SEARCH KAREIN",command=self.kb_search).pack(side="left")
        self.kb_out=self.output_box(470)
        self.kb_files=[]
        (DATA/"knowledge").mkdir(exist_ok=True)

    def kb_add_files(self):
        paths=filedialog.askopenfilenames(filetypes=[("Documents","*.txt *.md *.pdf *.csv *.docx"),("All files","*.*")])
        if not paths:return
        dest=DATA/"knowledge"; copied=[]
        for src in paths:
            try:
                target=dest/Path(src).name; shutil.copy2(src,target); copied.append(str(target))
            except Exception as e: copied.append(f"ERROR {src}: {e}")
        self.write_output(self.kb_out,"Added to local Knowledge Base:\n"+"\n".join(copied))

    def _kb_text(self,path):
        try:
            ext=path.suffix.lower()
            if ext in {".txt",".md",".csv"}: return path.read_text(encoding="utf-8",errors="ignore")[:30000]
            if ext==".pdf" and pypdf:
                reader=pypdf.PdfReader(str(path)); return "\n".join((pg.extract_text() or "") for pg in reader.pages)[:30000]
            if ext==".docx" and Document:
                d=Document(str(path)); return "\n".join(x.text for x in d.paragraphs)[:30000]
        except Exception: pass
        return ""

    def kb_search(self):
        q=self.kb_query.get().strip().lower()
        if not q:return
        folder=DATA/"knowledge"; hits=[]
        for path in folder.iterdir() if folder.exists() else []:
            if path.is_file():
                text=self._kb_text(path); score=sum(1 for term in re.findall(r"\\w+",q) if term and term in text.lower())
                if score: hits.append((score,path,text))
        hits.sort(key=lambda x:x[0],reverse=True)
        if not hits:
            self.write_output(self.kb_out,"No matching local documents found."); return
        summary=[]
        for score,path,text in hits[:8]:
            idx=text.lower().find(q)
            excerpt=text[max(0,idx-180):idx+700] if idx>=0 else text[:700]
            summary.append(f"[{score}] {path.name}\n{excerpt.strip()}\n")
        self.write_output(self.kb_out,"\n".join(summary))

    # ---------- Data Lab ----------
    def page_data_lab(self):
        self.header("Data Lab", "CSV/XLSX analysis • summaries • statistics • charts-ready insights")
        row=ctk.CTkFrame(self.content,fg_color="transparent"); row.pack(fill="x",padx=30,pady=8)
        ctk.CTkButton(row,text="CSV/XLSX KHOLEN",fg_color=BLUE,command=self.data_open).pack(side="left")
        self.data_query=ctk.CTkEntry(row,placeholder_text="Example: columns summarize karein aur missing values dhoondhein")
        self.data_query.pack(side="left",fill="x",expand=True,padx=8)
        ctk.CTkButton(row,text="ANALYZE KAREIN",command=self.data_analyze).pack(side="left")
        self.data_out=self.output_box(470); self.data_path=None

    def data_open(self):
        path=filedialog.askopenfilename(filetypes=[("Data","*.csv *.xlsx")])
        if path:self.data_path=path; self.write_output(self.data_out,f"Loaded: {path}\nClick ANALYZE KAREIN.")

    def data_analyze(self):
        if not self.data_path:return self.write_output(self.data_out,"Load a CSV or XLSX first.")
        if not pd:
            return self.write_output(self.data_out,"Install pandas for Data Lab: py -m pip install pandas")
        try:
            df=pd.read_csv(self.data_path) if self.data_path.lower().endswith(".csv") else pd.read_excel(self.data_path)
            q=self.data_query.get().strip() or "summarize this dataset"
            info={"rows":int(len(df)),"columns":list(map(str,df.columns)),"missing":df.isna().sum().to_dict(),"dtypes":{str(k):str(v) for k,v in df.dtypes.items()},"numeric_summary":df.describe(include="number").round(3).to_dict()}
            prompt=f"User request: {q}\nDataset metadata: {json.dumps(info,default=str)[:12000]}\nGive a concise factual analysis. Do not invent values beyond metadata."
            self.run_async(lambda:self.ai.ask(prompt,"You are ZETA Data Analyst. Use only supplied dataset metadata and clearly label limitations."),lambda r:self.write_output(self.data_out,"Dataset loaded successfully.\n\n"+r))
        except Exception as e:self.write_output(self.data_out,f"Data error: {e}")

    # ---------- Media Analyzer ----------
    def page_media_analyzer(self):
        self.header("Media Analyzer", "Image • audio • video • PDF analyze karein (model support ke according)")
        row=ctk.CTkFrame(self.content,fg_color="transparent"); row.pack(fill="x",padx=30,pady=8)
        ctk.CTkButton(row,text="MEDIA SELECT KAREIN",fg_color=BLUE,command=self.media_select).pack(side="left")
        self.media_prompt=ctk.CTkEntry(row,placeholder_text="ZETA ko kya analyze karna hai?")
        self.media_prompt.pack(side="left",fill="x",expand=True,padx=8)
        ctk.CTkButton(row,text="ANALYZE KAREIN",command=self.media_analyze).pack(side="left")
        self.media_out=self.output_box(470); self.media_path=None

    def media_select(self):
        path=filedialog.askopenfilename(filetypes=[("Media/Documents","*.png *.jpg *.jpeg *.webp *.mp3 *.wav *.mp4 *.mov *.pdf"),("All files","*.*")])
        if path:self.media_path=path; self.write_output(self.media_out,f"Selected: {path}")

    def media_analyze(self):
        if not self.media_path:return self.write_output(self.media_out,"Select a media file first.")
        if not self.ai.g:return self.write_output(self.media_out,"Gemini client is required for multimodal analysis. Add a Gemini API key in Settings.")
        prompt=self.media_prompt.get().strip() or "Analyze this file and explain the important information clearly."
        path=self.media_path
        def work():
            uploaded=self.ai.g.files.upload(file=path)
            # Video/audio files may require processing; poll briefly when state is exposed.
            for _ in range(60):
                state=getattr(getattr(uploaded,"state",None),"name",None)
                if not state or state=="ACTIVE": break
                time.sleep(1); uploaded=self.ai.g.files.get(name=uploaded.name)
            resp=self.ai.g.models.generate_content(model=self.ai.gmodel,contents=[uploaded,prompt])
            return getattr(resp,"text",str(resp))
        self.run_async(work,lambda r:self.write_output(self.media_out,r))

    # ---------- Routine Center ----------
    def page_routine_center(self):
        self.header("Routine Center", "Study reminders • project tasks • desktop notifications")
        self.routine_text=ctk.CTkTextbox(self.content,height=250,fg_color=PANEL,border_width=1,border_color=BORDER); self.routine_text.pack(fill="x",padx=30,pady=10)
        self.routine_text.insert("1.0","07:20 | School\n12:00 | Home\n15:00 | Revision\n15:50 | Coaching\n18:00 | Study\n20:00 | Dinner\n22:00 | Sleep")
        row=ctk.CTkFrame(self.content,fg_color="transparent"); row.pack(fill="x",padx=30)
        ctk.CTkButton(row,text="SAVE KAREIN ROUTINE",fg_color=BLUE,command=self.save_routine).pack(side="left")
        ctk.CTkButton(row,text="ALERT TEST KAREIN",fg_color=PANEL,command=lambda:messagebox.showinfo("ZETA Routine","Routine alert ka test." )).pack(side="left",padx=7)
        self.routine_out=self.output_box(250)
        self.write_output(self.routine_out,"Routine is local to this desktop prototype. Future cloud sync can share it across devices.")

    def save_routine(self):
        text=self.routine_text.get("1.0","end").strip(); path=DATA/"routine.txt"; path.write_text(text,encoding="utf-8")
        self.write_output(self.routine_out,f"Routine saved locally:\n{path}\n\n{ text }")

    # ---------- System Control ----------
    def page_system_control(self):
        self.header("System Control", "Permission-based local controls — koi unrestricted background control nahi")
        grid=ctk.CTkFrame(self.content,fg_color="transparent"); grid.pack(fill="x",padx=30,pady=15)
        actions=[
            ("OPEN BROWSER",lambda:webbrowser.open("https://www.google.com")),
            ("OPEN VS CODE",self.open_vscode),
            ("OPEN ZETA DATA",lambda:self.open_path(DATA)),
            ("CREATE NOTE",self.create_note),
            ("CHECK BATTERY",self.show_battery),
            ("SYSTEM INFO",self.show_system_info)
        ]
        for i,(label,cmd) in enumerate(actions):
            grid.grid_columnconfigure(i%2,weight=1); ctk.CTkButton(grid,text=label,height=55,fg_color=PANEL,command=cmd).grid(row=i//2,column=i%2,sticky="ew",padx=5,pady=5)
        ctk.CTkLabel(self.content,text="Safety rule: ZETA sirf is UI se allowed actions perform karta hai. Bina explicit action ke silently commands type, security settings change, ya machine control nahi karta.",text_color=MUTED,wraplength=900,justify="left").pack(anchor="w",padx=30,pady=15)

    def show_battery(self):
        if psutil:
            b=psutil.sensors_battery(); self.write_output(self.system_info_out if hasattr(self,'system_info_out') else self._system_info_box(), str(b) if b else "Battery information unavailable.")
        else: messagebox.showinfo("Battery","Install psutil for battery information.")

    def _system_info_box(self):
        self.system_info_out=self.output_box(220); return self.system_info_out

    def show_system_info(self):
        info=f"OS: {platform.platform()}\nPython: {platform.python_version()}\nMachine: {platform.machine()}\nTime: {datetime.now():%Y-%m-%d %H:%M:%S}"
        self.write_output(self.system_info_out if hasattr(self,'system_info_out') else self._system_info_box(),info)

    # ---------- Image Lab ----------
    def page_image_lab(self):
        self.header("Image Lab", "Prompt → image generation → local save. OpenAI API key aur image access required.")
        self.image_prompt = ctk.CTkTextbox(self.content, height=120, fg_color=PANEL, border_width=1, border_color=BORDER)
        self.image_prompt.pack(fill="x", padx=30, pady=10)
        self.image_prompt.insert("1.0", "Create a futuristic ZETA AI HUD concept, dark cyberpunk workspace, blue neon core")
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=30, pady=5)
        self.image_size = ctk.CTkOptionMenu(row, values=["1024x1024", "1536x1024", "1024x1536"])
        self.image_size.pack(side="left")
        ctk.CTkButton(row, text="IMAGE GENERATE KAREIN", fg_color=GREEN, text_color="#001018", command=self.generate_image).pack(side="left", padx=8)
        self.image_out = self.output_box(300)

    def generate_image(self):
        prompt = self.image_prompt.get("1.0", "end").strip()
        if not prompt:
            return
        self.write_output(self.image_out, "Image Lab: generating...")
        def work():
            if not self.ai.okey or not self.ai.o:
                raise RuntimeError("OpenAI API key/client is required for image generation.")
            result = self.ai.o.images.generate(model="gpt-image-2", prompt=prompt, size=self.image_size.get())
            item = result.data[0]
            b64 = getattr(item, "b64_json", None)
            if not b64:
                raise RuntimeError("Image provider returned no base64 image data.")
            out = DATA / f"zeta_image_{datetime.now():%Y%m%d_%H%M%S}.png"
            out.write_bytes(base64.b64decode(b64))
            return f"Image generated successfully.\nSaved: {out}"
        self.run_async(work, lambda r: self.write_output(self.image_out, r))

    # ---------- Business Workspace ----------
    def page_business_workspace(self):
        self.header("Business Workspace", "Idea → market → customer → product → budget → launch plan")
        self.business_box = ctk.CTkTextbox(self.content, height=120, fg_color=PANEL, border_width=1, border_color=BORDER)
        self.business_box.pack(fill="x", padx=30, pady=10)
        self.business_box.insert("1.0", "Example: ZETA AI web launch")
        row=ctk.CTkFrame(self.content, fg_color="transparent"); row.pack(fill="x", padx=30)
        self.business_budget=ctk.CTkEntry(row, placeholder_text="Budget ₹ (optional)"); self.business_budget.pack(side="left", fill="x", expand=True, padx=(0,7))
        self.business_mode=ctk.CTkOptionMenu(row, values=["Idea Validation","Business Plan","Pricing","Marketing Plan","Launch Plan","Pitch Deck"]); self.business_mode.pack(side="left")
        ctk.CTkButton(row,text="BUILD KAREIN",fg_color=PURPLE,command=self.build_business).pack(side="left",padx=7)
        self.business_out=self.output_box(420)
    def build_business(self):
        idea=self.business_box.get("1.0","end").strip(); budget=self.business_budget.get().strip() or "not specified"; mode=self.business_mode.get()
        prompt=f"Create a factual, practical {mode} for this idea: {idea}. Budget: ₹{budget}. Include assumptions, customer problem, product, pricing options, risks, validation experiments, marketing, launch steps and measurable next actions. Do not invent market statistics; mark assumptions clearly."
        self.run_async(lambda:self.ai.ask(prompt,"You are ZETA Business Workspace. Separate facts, assumptions and suggestions."),lambda r:self.write_output(self.business_out,r))

    # ---------- Export Center ----------
    def page_export_center(self):
        self.header("Export Center", "ZETA output ko TXT, Markdown, PDF, DOCX, PPTX ya XLSX mein export karein")
        self.export_box=ctk.CTkTextbox(self.content,height=360,fg_color=PANEL,border_width=1,border_color=BORDER); self.export_box.pack(fill="both",expand=True,padx=30,pady=10)
        ctk.CTkLabel(self.content,text="Paste or generate content above, then choose an export format.",text_color=MUTED).pack(anchor="w",padx=30)
        row=ctk.CTkFrame(self.content,fg_color="transparent"); row.pack(fill="x",padx=30,pady=10)
        for label,ext,fn in [("TXT",".txt",self.export_txt),("MD",".md",self.export_txt),("PDF",".pdf",self.export_pdf),("DOCX",".docx",self.export_docx),("PPTX",".pptx",self.export_pptx),("XLSX",".xlsx",self.export_xlsx)]:
            ctk.CTkButton(row,text=label,command=lambda e=ext,f=fn:f(e),fg_color=PANEL).pack(side="left",padx=3)
    def export_txt(self,ext):
        content=self.export_box.get("1.0","end").strip();
        if not content:return
        path=filedialog.asksaveasfilename(defaultextension=ext,filetypes=[("File",f"*{ext}")])
        if path: Path(path).write_text(content,encoding="utf-8"); messagebox.showinfo("Export",f"Created:\n{path}")
    def export_pdf(self,ext):
        if not SimpleDocTemplate: return messagebox.showinfo("PDF","Install reportlab first.")
        content=self.export_box.get("1.0","end").strip();
        if not content:return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
        if not path:return
        styles=getSampleStyleSheet(); doc=SimpleDocTemplate(path); story=[]
        for para in content.split("\n"):
            story += [Paragraph(para.replace("&","&amp;").replace("<","&lt;"),styles["BodyText"]),Spacer(1,6)]
        doc.build(story); messagebox.showinfo("Export",f"PDF created:\n{path}")
    def export_docx(self,ext):
        if not Document:return messagebox.showinfo("DOCX","Install python-docx first.")
        content=self.export_box.get("1.0","end").strip();
        if not content:return
        path=filedialog.asksaveasfilename(defaultextension=".docx",filetypes=[("DOCX","*.docx")])
        if not path:return
        d=Document(); [d.add_paragraph(x) for x in content.split("\n")]; d.save(path); messagebox.showinfo("Export",f"DOCX created:\n{path}")
    def export_pptx(self,ext):
        if not Presentation:return messagebox.showinfo("PPTX","Install python-pptx first.")
        content=self.export_box.get("1.0","end").strip();
        if not content:return
        path=filedialog.asksaveasfilename(defaultextension=".pptx",filetypes=[("PPTX","*.pptx")])
        if not path:return
        prs=Presentation()
        for i,part in enumerate([x.strip() for x in content.split("\n\n") if x.strip()] or [content]):
            slide=prs.slides.add_slide(prs.slide_layouts[1]); slide.shapes.title.text=f"ZETA Slide {i+1}"; slide.placeholders[1].text=part[:3000]
        prs.save(path); messagebox.showinfo("Export",f"PPTX created:\n{path}")
    def export_xlsx(self,ext):
        if not Workbook:return messagebox.showinfo("XLSX","Install openpyxl first.")
        content=self.export_box.get("1.0","end").strip();
        if not content:return
        path=filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("XLSX","*.xlsx")])
        if not path:return
        wb=Workbook(); ws=wb.active; ws.title="ZETA Export"
        for i,line in enumerate(content.split("\n"),1): ws.cell(i,1,line)
        wb.save(path); messagebox.showinfo("Export",f"XLSX created:\n{path}")

    # ---------- Account & Cloud ----------
    def page_account_cloud(self):
        self.header("Account & Cloud", "Secure web architecture: authentication, sync, storage and billing")
        box=ctk.CTkTextbox(self.content,height=430,fg_color=PANEL,border_width=1,border_color=BORDER); box.pack(fill="both",expand=True,padx=30,pady=15)
        box.insert("end", "ZETA Web Architecture\n\nBrowser → ZETA Secure Backend → Gemini/OpenAI\n\nPlanned production services:\n✓ Google OAuth / account login\n✓ Encrypted server-side sessions\n✓ Cloud chat + memory sync\n✓ File storage\n✓ Multi-device sync\n✓ Subscription/billing\n✓ Usage limits and abuse protection\n✓ Provider API keys kept on server only\n\nDesktop prototype status:\n• Local memory/storage: WORKING\n• Export/import: WORKING\n• Google OAuth: backend credentials required\n• Cloud sync: backend/database required\n• Billing: payment provider + adult/guardian-managed account setup required\n\nThis screen deliberately does not fake cloud authentication or payments.")
        ctk.CTkButton(self.content,text="Open Web Architecture Notes",command=lambda:webbrowser.open("https://www.google.com"),fg_color=PANEL).pack(anchor="w",padx=30,pady=5)

    # ---------- Settings ----------
    def page_settings(self):
        self.header(
            "Settings",
            "Session API keys • Models • Profile • Theme • Privacy"
        )

        frame = ctk.CTkFrame(
            self.content, fg_color=PANEL,
            border_width=1, border_color=BORDER
        )
        frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            frame, text="Gemini API",
            text_color=CYAN,
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=18, pady=(15, 5))

        gkey = ctk.CTkEntry(
            frame, placeholder_text="Gemini API key",
            show="•"
        )
        gkey.pack(fill="x", padx=18, pady=5)

        gmodel = ctk.CTkEntry(frame)
        gmodel.insert(0, self.ai.gmodel)
        gmodel.pack(fill="x", padx=18, pady=5)

        ctk.CTkLabel(
            frame, text="OpenAI API",
            text_color=GREEN,
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=18, pady=(15, 5))

        okey = ctk.CTkEntry(
            frame, placeholder_text="OpenAI API key",
            show="•"
        )
        okey.pack(fill="x", padx=18, pady=5)

        omodel = ctk.CTkEntry(frame)
        omodel.insert(0, self.ai.omodel)
        omodel.pack(fill="x", padx=18, pady=5)

        def apply_api():
            if gkey.get().strip():
                self.ai.gkey = gkey.get().strip()
            if okey.get().strip():
                self.ai.okey = okey.get().strip()

            self.ai.gmodel = gmodel.get().strip() or GEMINI_MODEL
            self.ai.omodel = omodel.get().strip() or OPENAI_MODEL
            self.ai.configure()
            self.refresh_status()
            messagebox.showinfo("ZETA", "API settings updated.")

        ctk.CTkButton(
            frame, text="APPLY API SETTINGS",
            fg_color=CYAN, text_color="#001018",
            command=apply_api
        ).pack(anchor="w", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            frame,
            text=(
                "Gemini fallback chain: "
                + " → ".join(GEMINI_FALLBACK_MODELS)
                + "\nEach model gets automatic retries for temporary 429/5xx/network errors."
            ),
            text_color=MUTED,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 8))

        ctk.CTkButton(
            frame, text="TEST CURRENT ENGINE",
            fg_color=PANEL2,
            command=self.test_current_engine
        ).pack(anchor="w", padx=18, pady=(0, 15))

        profile = ctk.CTkFrame(
            self.content, fg_color=PANEL,
            border_width=1, border_color=BORDER
        )
        profile.pack(fill="x", padx=30, pady=8)

        ctk.CTkLabel(
            profile, text="Personalization",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=18, pady=(15, 5))

        name = ctk.CTkEntry(
            profile, placeholder_text="Name"
        )
        name.insert(0, self.ai.profile.get("name", "Daksh Boss"))
        name.pack(fill="x", padx=18, pady=5)

        tone = ctk.CTkOptionMenu(
            profile,
            values=["Friendly", "Teacher", "JARVIS", "Professional", "Simple Hindi"]
        )
        tone.set(self.ai.profile.get("tone", "Friendly"))
        tone.pack(anchor="w", padx=18, pady=5)

        theme = ctk.CTkOptionMenu(
            profile,
            values=["Cyber Blue", "Matrix Green", "Purple Core", "Minimal Dark"]
        )
        theme.set(self.ai.profile.get("theme", "Cyber Blue"))
        theme.pack(anchor="w", padx=18, pady=5)

        def save_profile():
            self.ai.profile["name"] = name.get().strip() or "Daksh Boss"
            self.ai.profile["tone"] = tone.get()
            self.ai.profile["theme"] = theme.get()
            self.ai.save_state()
            self.apply_theme(theme.get())
            messagebox.showinfo("ZETA", "Profile and theme saved.")

        ctk.CTkButton(
            profile, text="SAVE KAREIN PROFILE + THEME",
            fg_color=PURPLE, command=save_profile
        ).pack(anchor="w", padx=18, pady=(8, 15))

        ctk.CTkLabel(
            self.content,
            text=(
                f"Local data folder: {DATA}\n"
                "Provider keys are not written into this source code. "
                "For public deployment use a secure backend."
            ),
            text_color=MUTED, justify="left"
        ).pack(anchor="w", padx=30, pady=10)

        ctk.CTkButton(
            self.content,
            text="Open ZETA Data Folder",
            fg_color=PANEL,
            command=lambda: self.open_path(DATA)
        ).pack(anchor="w", padx=30)

    def test_current_engine(self):
        engine = self.ai.engine

        def finish(result):
            messagebox.showinfo(
                "ZETA Connection Test",
                f"Engine: {engine}\n\n{result}"
            )
            self.refresh_status()

        self.run_async(
            lambda: self.ai.ask(
                "Reply exactly: ZETA ONLINE TEST OK",
                "This is a connection test."
            ),
            finish
        )

    def apply_theme(self, theme):
        # CustomTkinter supports a small set of appearance colors.
        # Keep the futuristic layout while changing accent colors.
        if theme == "Matrix Green":
            global CYAN
            CYAN = GREEN
        elif theme == "Purple Core":
            CYAN = PURPLE
        elif theme == "Minimal Dark":
            CYAN = "#D9E2EC"
        else:
            CYAN = "#00D9FF"

    # ---------- files ----------
    def attach_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp"),
                ("PDF", "*.pdf"),
                ("Text", "*.txt *.md *.py *.json"),
                ("All", "*.*")
            ]
        )
        if path:
            self.current_file = path
            messagebox.showinfo(
                "ZETA Attachment",
                f"Attached:\n{Path(path).name}\n\nNow send your question."
            )

    # ---------- voice ----------
    def voice_input(self):
        if not sr:
            messagebox.showinfo(
                "Voice",
                "Install SpeechRecognition and a microphone backend first."
            )
            return

        def capture():
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(
                    source, timeout=6, phrase_time_limit=15
                )
            return recognizer.recognize_google(audio)

        def done(text):
            if hasattr(self, "chat_input"):
                self.chat_input.insert("end", text)

        self.run_async(capture, done)

    def speak_last(self):
        if not pyttsx3:
            messagebox.showinfo(
                "TTS",
                "Install pyttsx3 first."
            )
            return

        if not hasattr(self, "chat"):
            return

        text = self.chat.get("1.0", "end").strip()[-3500:]
        if not text:
            return

        def speak():
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return "done"

        self.run_async(speak, lambda _: None)

    # ---------- startup + file maker ----------
    def create_file_from_ai(self, content, extension=".txt"):
        path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[
                ("Text", "*.txt"),
                ("Markdown", "*.md"),
                ("Python", "*.py"),
                ("JSON", "*.json"),
                ("All", "*.*")
            ]
        )
        if not path:
            return

        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo("ZETA File Maker", f"File created:\n{path}")


if __name__ == "__main__":
    app = ZetaApp()
    app.mainloop()
