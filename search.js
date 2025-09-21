function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

async function performSearch(name) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (!name) {
    resultsDiv.textContent = 'Please enter a character name.';
    return;
  }

  try {
    const fileName = name.toLowerCase();
    const res = await fetch(`snapshots/${fileName}.json`);

    if (!res.ok) {
      resultsDiv.textContent = `No history found for "${name}".`;
      return;
    }

    const history = await res.json();

    if (!Array.isArray(history) || history.length === 0) {
      resultsDiv.textContent = `No history found for "${name}".`;
      return;
    }

/*
    let html = `Snapshots via build planner for <a href="https://beta.pathofdiablo.com/armory?name=${encodeURIComponent(name)}" target="_blank">${name}</a><br><br><table><tr><th>Date/Time</th><th>Build Planner URL</th></tr>`;
    for (const entry of history) {
      html += `<tr><td>${entry.timestamp || ""}</td><td><a href="${entry.url}" target="_blank">${entry.url}</a></td></tr>`;
    }
    html += '</table>';
*/
  let html = `Historical snapshots via build planner for character <a href="https://beta.pathofdiablo.com/armory?name=${encodeURIComponent(name)}" target="_blank">${name}</a><br><br><table><tr><th>Build Planner link</th><th>Copy URL</th></tr>`;

  for (const entry of history) {
//    const timestamp = entry.timestamp || "Unknown date";
  let timestamp = "Unknown date";
  if (entry.timestamp) {
    const date = new Date(entry.timestamp);
    if (!isNaN(date)) {
      timestamp = date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        hour12: true
      });
    } else {
      // fallback for partial timestamp like "2025-09-21T14"
      const [datePart, hourPart] = entry.timestamp.split('T');
      const [year, month, day] = datePart.split('-');
      const hour = parseInt(hourPart, 10);
      const formattedDate = new Date(year, month - 1, day, hour);
      timestamp = formattedDate.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        hour12: true
      });
    }
  }


    const url = entry.url;
    const safeId = `copy-${Math.random().toString(36).substr(2, 9)}`; // unique ID

    html += `<tr>
      <td><a href="${url}" target="_blank">Snapshot of build on ${timestamp}</a></td>
      <td>
        <button onclick="copyToClipboard('${url}', '${safeId}')" title="Copy to clipboard">📋</button>
        <span id="${safeId}" class="tooltip">Copied!</span>
      </td>
    </tr>`;
  }

  html += '</table>';

    resultsDiv.innerHTML = html;
  } catch (err) {
    console.error(err);
    resultsDiv.textContent = 'Error fetching character history.';
  }
} 

document.getElementById('searchBtn').addEventListener('click', () => {
  const name = document.getElementById('charName').value.trim();
  performSearch(name);
});

// 🔍 Auto-trigger search if URL contains ?search=...
window.addEventListener('DOMContentLoaded', () => {
  const autoSearch = getQueryParam('search');
  if (autoSearch) {
    document.getElementById('charName').value = autoSearch;
    performSearch(autoSearch);
  }
});


function copyToClipboard(text, tooltipId) {
  navigator.clipboard.writeText(text).then(() => {
    const tooltip = document.getElementById(tooltipId);
    if (tooltip) {
      tooltip.style.visibility = 'visible';
      setTimeout(() => {
        tooltip.style.visibility = 'hidden';
      }, 1500);
    }
  });
}

// Example search url:
// https://qordwasalreadytaken.github.io/PoD-History-Builder/search.html?search=viggie
