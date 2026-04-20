// content.js
chrome.storage.local.get(["focusMode"], (result) => {
    if (result.focusMode) {
        document.documentElement.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height:100vh; background:#0f172a; color:#f8fafc; font-family:sans-serif; text-align:center;">
                <div>
                    <h1 style="font-size:3rem; margin-bottom:1rem; color:#ef4444;">🛑 Distraction Blocked</h1>
                    <p style="font-size:1.5rem; color:#94a3b8;">The AI Study Planner detects you are in Focus Mode.</p>
                    <p style="margin-top:2rem;">Close this tab and get back to work!</p>
                </div>
            </div>
        `;
        document.documentElement.style.overflow = "hidden";
    }
});

// Listen for real-time changes
chrome.storage.onChanged.addListener((changes) => {
    if (changes.focusMode && changes.focusMode.newValue === true) {
        // Switch immediately
        location.reload();
    }
});
