/**
 * CareerOS — Gmail Monitor
 * Monitors Gmail for Naukri HR activity (invites, profile views, messages).
 * Sends instant push notifications via ntfy.sh — free, no account needed.
 * Runs every 5 minutes on Google's servers. Always-on. Zero cost.
 *
 * SETUP (one time, ~2 minutes):
 * 1. Open script.google.com → New project → paste this entire file
 * 2. Set NTFY_TOPIC below (copy from CareerOS → Setup page → your channel)
 * 3. Click Run → setupTrigger() → authorize when prompted
 * Done. CareerOS now monitors your Gmail 24/7 from Google's cloud.
 */

// ── Set this (copy from CareerOS Setup page) ──────────────────────────────
var NTFY_TOPIC = "YOUR_CAREEROS_TOPIC";  // e.g. "careeros-a3f9b2c1d4"
var NTFY_BASE  = "https://ntfy.sh";
var PROCESSED_LABEL = "CareerOS/Processed";


// ── Main (runs every 5 minutes) ───────────────────────────────────────────
function checkNaukriEmails() {
  if (NTFY_TOPIC === "YOUR_CAREEROS_TOPIC") {
    Logger.log("ERROR: Set your NTFY_TOPIC first. Find it on CareerOS Setup page.");
    return;
  }

  ensureLabelExists(PROCESSED_LABEL);

  var cutoff = new Date();
  cutoff.setMinutes(cutoff.getMinutes() - 8); // 8-min window (runs every 5)

  var query = 'from:(naukri.com) after:' + Math.floor(cutoff.getTime() / 1000)
              + ' -label:' + PROCESSED_LABEL;
  var threads = GmailApp.search(query, 0, 20);

  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    for (var j = 0; j < messages.length; j++) {
      var msg = messages[j];
      if (msg.getDate() < cutoff) continue;

      var subject = msg.getSubject();
      var body    = msg.getPlainBody();
      var type    = detectEventType(subject, body);

      if (type) {
        var data = parseEmailData(subject, body, type);
        sendNtfy(data);
        Logger.log("Notified: " + type + " from " + data.company);
      }
    }
    threads[i].addLabel(GmailApp.getUserLabelByName(PROCESSED_LABEL));
  }
}


// ── Detect event type ─────────────────────────────────────────────────────
function detectEventType(subject, body) {
  var text = (subject + " " + body.substring(0, 800)).toLowerCase();

  if (text.match(/invited you to apply|job invite|apply now|recruiter.*invited/))
    return "HR_INVITE";
  if (text.match(/sent you a message|new message from|has messaged you/))
    return "HR_MESSAGE";
  if (text.match(/viewed your profile|has viewed your|profile was viewed/))
    return "PROFILE_VIEW";

  return null;
}


// ── Parse email into structured data ──────────────────────────────────────
function parseEmailData(subject, body, type) {
  return {
    type:    type,
    company: extractCompany(subject, body),
    role:    extractRole(subject, body),
    hrName:  extractHRName(body),
    url:     extractNaukriUrl(body),
    snippet: body.substring(0, 200),
  };
}

function extractCompany(subject, body) {
  var m = subject.match(/^(.+?)\s+(?:has invited|has viewed|sent you|is looking)/i);
  if (m) return m[1].trim();
  m = body.match(/(?:company|employer)[\s:]+([^\n]+)/i);
  return m ? m[1].trim() : "Unknown Company";
}

function extractRole(subject, body) {
  var text = subject + " " + body;
  var m = text.match(/(?:for the role of|position of|opening for|apply for)\s+['""]?([^'""\n.]{3,60})/i);
  return m ? m[1].trim() : "";
}

function extractHRName(body) {
  var m = body.match(/([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:from|at|–|-)/);
  if (m) return m[1].trim();
  m = body.match(/(?:regards,?|thanks,?)\s*\n\s*([A-Z][a-z]+ [A-Z][a-z]+)/);
  return m ? m[1].trim() : "";
}

function extractNaukriUrl(body) {
  var m = body.match(/https?:\/\/(?:www\.)?naukri\.com\/[^\s\n"'<)\]]+/i);
  return m ? m[0] : "";
}


// ── Send ntfy push notification ───────────────────────────────────────────
function sendNtfy(data) {
  var config = buildNotification(data);

  var headers = {
    "Title":    config.title,
    "Priority": config.priority,
    "Tags":     config.tags,
  };
  if (data.url) headers["Click"] = data.url;

  UrlFetchApp.fetch(NTFY_BASE + "/" + NTFY_TOPIC, {
    method:             "post",
    headers:            headers,
    payload:            config.body,
    muteHttpExceptions: true,
  });
}

function buildNotification(data) {
  if (data.type === "HR_INVITE") {
    return {
      title:    "HR Invite — " + data.company,
      body:     "Role: " + (data.role || "Not specified") + "\n"
                + "HR: " + (data.hrName || "Unknown") + "\n"
                + "CareerOS will auto-apply on next run.",
      priority: "urgent",
      tags:     "fire,briefcase",
    };
  }
  if (data.type === "HR_MESSAGE") {
    return {
      title:    "HR Message — " + data.company,
      body:     (data.hrName ? "From: " + data.hrName + "\n" : "")
                + "Check your Naukri inbox.",
      priority: "high",
      tags:     "speech_balloon",
    };
  }
  // PROFILE_VIEW
  return {
    title:    "Profile Viewed — " + data.company,
    body:     "An HR viewed your Naukri profile. Stay alert — invite may follow.",
    priority: "default",
    tags:     "eyes",
  };
}


// ── Gmail label helper ────────────────────────────────────────────────────
function ensureLabelExists(name) {
  var parts = name.split("/");
  var current = "";
  for (var i = 0; i < parts.length; i++) {
    current = i === 0 ? parts[i] : current + "/" + parts[i];
    if (!GmailApp.getUserLabelByName(current))
      GmailApp.createLabel(current);
  }
}


// ── One-time setup ────────────────────────────────────────────────────────
function setupTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++)
    ScriptApp.deleteTrigger(triggers[i]);

  ScriptApp.newTrigger("checkNaukriEmails")
    .timeBased()
    .everyMinutes(5)
    .create();

  ensureLabelExists(PROCESSED_LABEL);

  Logger.log("CareerOS Gmail Monitor is LIVE!");
  Logger.log("Checks Gmail every 5 min. Notifies: " + NTFY_BASE + "/" + NTFY_TOPIC);

  // Send test notification to confirm setup
  UrlFetchApp.fetch(NTFY_BASE + "/" + NTFY_TOPIC, {
    method:   "post",
    headers:  { "Title": "CareerOS Gmail Monitor Active", "Priority": "default", "Tags": "tada" },
    payload:  "Gmail monitor is running. You'll be notified instantly for HR invites and profile views.",
    muteHttpExceptions: true,
  });
}


// ── Test without real email ───────────────────────────────────────────────
function testNotification() {
  var testData = {
    type:    "HR_INVITE",
    company: "Test Company Pvt Ltd",
    role:    "Senior Business Analyst",
    hrName:  "Priya Sharma",
    url:     "https://www.naukri.com",
    snippet: "Test notification from CareerOS Gmail Monitor.",
  };
  sendNtfy(testData);
  Logger.log("Test notification sent to " + NTFY_BASE + "/" + NTFY_TOPIC);
}
