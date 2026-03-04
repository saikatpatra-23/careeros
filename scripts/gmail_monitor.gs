/**
 * CareerOS — Gmail Monitor
 * Monitors Gmail for Naukri HR activity (invites, profile views, messages).
 * Runs every 5 minutes on Google's servers. Always-on. Free.
 *
 * SETUP (one time):
 * 1. Open script.google.com → New project → paste this entire file
 * 2. Set MAKE_WEBHOOK_URL below (from your careeros_config.json → make_webhook_url)
 * 3. Click Run → setupTrigger()
 * 4. Authorize when prompted (Google needs permission to read Gmail)
 * Done. CareerOS now monitors your inbox 24/7 from Google's cloud.
 */

// ── Config (set this) ──────────────────────────────────────────────────────
var MAKE_WEBHOOK_URL = "YOUR_MAKE_WEBHOOK_URL"; // from careeros_config.json
var PROCESSED_LABEL  = "CareerOS/Processed";     // Gmail label to mark done emails


// ── Main function (runs every 5 minutes) ──────────────────────────────────
function checkNaukriEmails() {
  ensureLabelExists(PROCESSED_LABEL);

  // Search last 8 minutes (slight overlap so no email is ever missed)
  var cutoff = new Date();
  cutoff.setMinutes(cutoff.getMinutes() - 8);
  var afterTimestamp = Math.floor(cutoff.getTime() / 1000);

  var query = 'from:(naukri.com) after:' + afterTimestamp + ' -label:' + PROCESSED_LABEL;
  var threads = GmailApp.search(query, 0, 20);

  var processed = 0;
  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    for (var j = 0; j < messages.length; j++) {
      var msg = messages[j];
      if (msg.getDate() < cutoff) continue;

      var subject = msg.getSubject();
      var body    = msg.getPlainBody();
      var inviteType = detectEventType(subject, body);

      if (inviteType) {
        var data = parseEmailData(subject, body, inviteType, msg.getFrom());
        var sent = notifyCareerOS(data);
        if (sent) {
          Logger.log("Notified CareerOS: " + inviteType + " — " + data.company);
          processed++;
        }
      }

      // Label as processed regardless (so we don't re-scan it)
      threads[i].addLabel(GmailApp.getUserLabelByName(PROCESSED_LABEL));
    }
  }

  if (processed > 0) {
    Logger.log("Run complete. Notified CareerOS about " + processed + " event(s).");
  }
}


// ── Event type detection ──────────────────────────────────────────────────
function detectEventType(subject, body) {
  var text = (subject + " " + body.substring(0, 800)).toLowerCase();

  // P1: HR directly invited you to apply — highest signal
  if (text.match(/invited you to apply|job invite|apply now|recruiter.*invited/)) {
    return "HR_INVITE";
  }
  // P1: HR sent you a direct message
  if (text.match(/sent you a message|new message from|has messaged you/)) {
    return "HR_MESSAGE";
  }
  // P2: HR viewed your profile (not yet invite, but warm signal)
  if (text.match(/viewed your profile|has viewed your|profile was viewed/)) {
    return "PROFILE_VIEW";
  }
  // P3: Job alert from Naukri (scheduled digest, lower priority)
  if (text.match(/job alert|jobs matching|new jobs for you/)) {
    return "JOB_ALERT";
  }
  return null;
}


// ── Parse email into structured data ─────────────────────────────────────
function parseEmailData(subject, body, eventType, from) {
  var company = extractCompany(subject, body);
  var role    = extractRole(subject, body);
  var url     = extractNaukriUrl(body);
  var hrName  = extractHRName(body);

  return {
    event_type:    eventType,
    company:       company,
    role:          role,
    hr_name:       hrName,
    apply_url:     url,
    subject:       subject,
    from_email:    from,
    detected_at:   new Date().toISOString(),
    raw_snippet:   body.substring(0, 400),
    priority:      (eventType === "HR_INVITE" || eventType === "HR_MESSAGE") ? "P1" : "P2"
  };
}

function extractCompany(subject, body) {
  // "TCS has invited you..." or "Message from Infosys recruiter"
  var patterns = [
    /^(.+?)\s+(?:has invited|has viewed|sent you|is looking)/i,
    /recruiter from\s+(.+?)\s+(?:has|is)/i,
    /from\s+(.+?)[,\.]/i,
  ];
  for (var i = 0; i < patterns.length; i++) {
    var m = subject.match(patterns[i]);
    if (m) return m[1].trim();
  }
  // Try body
  var bm = body.match(/(?:company|employer|organisation)[\s:]+([^\n]+)/i);
  return bm ? bm[1].trim() : "Unknown Company";
}

function extractRole(subject, body) {
  var patterns = [
    /(?:for the role of|position of|job title|opening for)\s+['""]?([^'""\n\.]+)/i,
    /(?:apply for|applied for)\s+['""]?([^'""\n\.]+)/i,
  ];
  var text = subject + " " + body;
  for (var i = 0; i < patterns.length; i++) {
    var m = text.match(patterns[i]);
    if (m) return m[1].trim();
  }
  return "";
}

function extractNaukriUrl(body) {
  var m = body.match(/https?:\/\/(?:www\.)?naukri\.com\/[^\s\n"'<>\)]+/i);
  return m ? m[0] : "";
}

function extractHRName(body) {
  var patterns = [
    /(?:from|by|regards,?|thanks,?)\s+([A-Z][a-z]+ [A-Z][a-z]+)/,
    /([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:from|at|–|-)/,
  ];
  for (var i = 0; i < patterns.length; i++) {
    var m = body.match(patterns[i]);
    if (m) return m[1].trim();
  }
  return "";
}


// ── Notify CareerOS via Make.com webhook ─────────────────────────────────
function notifyCareerOS(data) {
  if (!MAKE_WEBHOOK_URL || MAKE_WEBHOOK_URL === "YOUR_MAKE_WEBHOOK_URL") {
    Logger.log("ERROR: MAKE_WEBHOOK_URL not set. Open this script and set it.");
    return false;
  }

  try {
    var response = UrlFetchApp.fetch(MAKE_WEBHOOK_URL, {
      method:             "post",
      contentType:        "application/json",
      payload:            JSON.stringify({
        source:           "careeros_gmail_monitor",
        type:             "hr_activity",
        notif_pref:       "whatsapp",   // Make.com uses this to route notification
        data:             data,
        message: buildNotificationMessage(data),
      }),
      muteHttpExceptions: true,
    });
    return response.getResponseCode() === 200;
  } catch (e) {
    Logger.log("Webhook error: " + e.toString());
    return false;
  }
}

function buildNotificationMessage(data) {
  if (data.event_type === "HR_INVITE") {
    return "🔥 *P1 — HR Invite!*\n\n"
      + "*Company:* " + data.company + "\n"
      + (data.role    ? "*Role:* "    + data.role    + "\n" : "")
      + (data.hr_name ? "*HR:* "      + data.hr_name + "\n" : "")
      + (data.apply_url ? "\n👉 " + data.apply_url : "")
      + "\n\nCareerOS will auto-apply on next run. Check Run History.";
  }
  if (data.event_type === "HR_MESSAGE") {
    return "💬 *HR Message Received*\n\n"
      + "*From:* " + data.company + "\n"
      + (data.hr_name ? "*HR:* " + data.hr_name + "\n" : "")
      + "\n📩 Check your Naukri inbox.";
  }
  if (data.event_type === "PROFILE_VIEW") {
    return "👀 *Profile Viewed*\n\n"
      + "*By:* " + data.company + "\n"
      + "Your Naukri profile was viewed. Stay alert — invite may follow.";
  }
  return "📬 Naukri activity detected: " + data.event_type + " from " + data.company;
}


// ── Gmail label helper ────────────────────────────────────────────────────
function ensureLabelExists(labelName) {
  var parts = labelName.split("/");
  var current = "";
  for (var i = 0; i < parts.length; i++) {
    current = i === 0 ? parts[i] : current + "/" + parts[i];
    if (!GmailApp.getUserLabelByName(current)) {
      GmailApp.createLabel(current);
    }
  }
}


// ── One-time setup ────────────────────────────────────────────────────────
/**
 * Run this ONCE to create the 5-minute trigger.
 * After that, checkNaukriEmails() runs automatically on Google's servers forever.
 */
function setupTrigger() {
  // Delete existing triggers first
  var existing = ScriptApp.getProjectTriggers();
  for (var i = 0; i < existing.length; i++) {
    ScriptApp.deleteTrigger(existing[i]);
  }

  // Create new 5-minute trigger
  ScriptApp.newTrigger("checkNaukriEmails")
    .timeBased()
    .everyMinutes(5)
    .create();

  ensureLabelExists(PROCESSED_LABEL);

  Logger.log("✅ CareerOS Gmail Monitor is live!");
  Logger.log("   Checks your Gmail every 5 minutes.");
  Logger.log("   Processed emails get label: " + PROCESSED_LABEL);
  Logger.log("   Notifications go to Make.com → WhatsApp/email.");
}


// ── Manual test ───────────────────────────────────────────────────────────
/**
 * Run this to test without waiting for a real Naukri email.
 */
function testWebhook() {
  var testData = {
    event_type:  "HR_INVITE",
    company:     "Test Company Pvt Ltd",
    role:        "Senior Business Analyst",
    hr_name:     "Priya Sharma",
    apply_url:   "https://www.naukri.com/job-listings-test",
    detected_at: new Date().toISOString(),
    priority:    "P1",
    raw_snippet: "Test email — CareerOS webhook test.",
  };
  var result = notifyCareerOS(testData);
  Logger.log(result ? "✅ Webhook test succeeded." : "❌ Webhook test failed. Check MAKE_WEBHOOK_URL.");
}
