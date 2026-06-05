/**
 * Product Hunt Tracker — Google Apps Script Web App
 *
 * DEPLOY ONCE:
 *   1. Open https://docs.google.com/spreadsheets/d/15RMY2hV7cPU9QzFtmY_n_uW_wfAHK3nqiw7W2Lvi3GY
 *   2. Extensions → Apps Script
 *   3. Replace any existing code with this file's contents
 *   4. Click Deploy → New deployment
 *      • Type: Web app
 *      • Execute as: Me
 *      • Who has access: Anyone
 *   5. Click Deploy → copy the /exec URL
 *   6. Set that URL as SHEETS_WEBAPP_URL in your environment or .env file
 */

var SPREADSHEET_ID = "15RMY2hV7cPU9QzFtmY_n_uW_wfAHK3nqiw7W2Lvi3GY";
var SHEET_GID      = 1725789762;

function getSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getSheetId() === SHEET_GID) return sheets[i];
  }
  return ss.getSheets()[0];
}

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var rows    = payload.rows;   // array of arrays [[col1,col2,...], ...]
    var sheet   = getSheet_();

    for (var i = 0; i < rows.length; i++) {
      sheet.appendRow(rows[i]);
    }

    return ContentService
      .createTextOutput(JSON.stringify({ status: "ok", appended: rows.length }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/** Smoke-test: GET the URL to confirm the web app is live. */
function doGet(e) {
  var sheet     = getSheet_();
  var lastRow   = sheet.getLastRow();
  return ContentService
    .createTextOutput(JSON.stringify({ status: "ready", rows_in_sheet: lastRow }))
    .setMimeType(ContentService.MimeType.JSON);
}
