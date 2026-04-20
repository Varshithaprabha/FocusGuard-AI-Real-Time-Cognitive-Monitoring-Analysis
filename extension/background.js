// background.js

const API_URL = "http://localhost:8000/api/status/1"; // Default dev user 1
let isFocusing = false;

// Poll the status every 5 seconds
chrome.alarms.create("statusPoller", { periodInMinutes: 5 / 60 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "statusPoller") {
    fetch(API_URL)
      .then(res => res.json())
      .then(data => {
        if (data.active && data.state === "Focusing") {
          isFocusing = true;
          chrome.action.setBadgeText({ text: "ON" });
          chrome.action.setBadgeBackgroundColor({ color: "#10b981" });
        } else {
          isFocusing = false;
          chrome.action.setBadgeText({ text: "" });
        }
        
        // Broadcast state to potential open tabs
        chrome.storage.local.set({ focusMode: isFocusing });
      })
      .catch(err => console.log("Study Planner backend offline."));
  }
});
